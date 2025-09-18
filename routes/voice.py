# routes/voice.py
from __future__ import annotations

import os
import re
import json
import math
import secrets
from typing import List, Optional, Dict, Any
from urllib.parse import unquote_plus

import difflib
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel  # OrderModel facultatif
# Si "Order" n'existe pas chez toi, tu peux simplement commenter toute la partie "création DB d'une commande"

# -------------------------------------------------------------------
# Router
# -------------------------------------------------------------------
router = APIRouter(prefix="/voice", tags=["voice"])

# -------------------------------------------------------------------
# DB helper
# -------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------
# Sécurité : API Key (header x-api-key ou query ?key=)
# -------------------------------------------------------------------
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")

def require_api_key(
    x_api_key: Optional[str] = Header(default=None, convert_underscores=False),
    key: Optional[str] = Query(default=None)
):
    """
    Autorise soit:
      - header 'x-api-key: <clé>'
      - query '?key=<clé>'
    """
    provided_raw = x_api_key or key
    if provided_raw is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Voiceflow encode parfois les '!' et '$' => on normalise
    provided = unquote_plus(str(provided_raw)).strip()
    expected = str(VOICE_API_KEY).strip()

    if not provided or not expected or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")

# -------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------
def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit() or c == "+")
    # On tolère +33 / 0033 / 33 / 0…
    digits = digits.replace(" ", "")
    digits = digits.replace("-", "")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("0") and len(digits) >= 10:
        # FR: 0X XX XX XX XX  -> +33X…
        digits = "+33" + digits[1:]
    return digits

def safe_aliases(value: Any) -> List[str]:
    """
    Retourne une liste d'aliases propre à partir de ce que la DB contient :
    - None -> []
    - "coca,coca cola" -> ["coca", "coca cola"]
    - '["coca","coca cola"]' -> ["coca", "coca cola"]
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    if not s:
        return []
    # JSON ?
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(v).strip() for v in parsed if str(v).strip()]
    except Exception:
        pass
    # CSV ?
    return [seg.strip() for seg in s.split(",") if seg.strip()]

def canon(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s\-]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE)
    # simplifications très simples de pluriel
    s = re.sub(r"s\b", "", s)
    return s

def best_match(text: str, candidates: List[str]) -> Optional[str]:
    """
    Retourne le meilleur match fuzzy ou None.
    """
    if not candidates:
        return None
    text_c = canon(text)
    cands_c = [canon(c) for c in candidates]
    # cut-off 0.6: assez tolérant (0..1)
    idxs = difflib.get_close_matches(text_c, cands_c, n=1, cutoff=0.6)
    if not idxs:
        return None
    # difflib travaille sur les versions "canonisées", on retrouve l'original par index
    best_canon = idxs[0]
    try:
        pos = cands_c.index(best_canon)
        return candidates[pos]
    except Exception:
        return None

# -------------------------------------------------------------------
# Schemas
# -------------------------------------------------------------------
class VoiceOrderItemIn(BaseModel):
    name: str
    quantity: int = 1
    note: Optional[str] = ""

class VoiceOrderParseIn(BaseModel):
    restaurant_number: str = Field(..., description="Numéro appelé, ex: +33755123456")
    utterance: str = Field(..., description="Texte libre utilisateur, ex: '2 margherita et 1 coca'")

class OrderLineOut(BaseModel):
    name: str
    unit_price: float
    quantity: int
    note: str = ""

class OrderParseOut(BaseModel):
    ok: bool
    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None
    lines: List[OrderLineOut] = []
    total: float = 0.0
    message: Optional[str] = None

class RestaurantInfo(BaseModel):
    id: int
    nom_restaurant: Optional[str]
    numero_appel: Optional[str]
    menu: List[Dict[str, Any]]

# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@router.get("/ping")
def ping(_: Any = Depends(require_api_key)):
    return {"ok": True}

@router.get(
    "/restaurant/by-number/{called_number}",
    response_model=RestaurantInfo,
    dependencies=[Depends(require_api_key)],
)
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    num = normalize_number(called_number)
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()

    target: Optional[Restaurant] = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            target = r
            break

    if not target:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == target.id).all()

    def item_payload(mi: MenuItem) -> Dict[str, Any]:
        als = safe_aliases(getattr(mi, "aliases", None))
        return {
            "id": mi.id,
            "name": mi.name,
            "price": float(mi.price),
            "aliases": als,
        }

    return {
        "id": target.id,
        "nom_restaurant": getattr(target, "nom_restaurant", None),
        "numero_appel": getattr(target, "numero_appel", None),
        "menu": [item_payload(i) for i in items],
    }

# -------------------------------------------------------------------
# Parsing "intelligent" d'une phrase libre en lignes de commande
# -------------------------------------------------------------------
@router.post(
    "/order",
    response_model=OrderParseOut,
    dependencies=[Depends(require_api_key)],
)
def parse_order(payload: VoiceOrderParseIn, db: Session = Depends(get_db)):
    # 1) Trouver le resto par numéro appelé
    num = normalize_number(payload.restaurant_number)
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()

    resto: Optional[Restaurant] = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 2) Charger le menu + dictionnaire de recherche
    menu_items: List[MenuItem] = (
        db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    )

    # Préparer les candidats de matching
    # mapping: "nom canonisé" -> MenuItem
    name_to_item: Dict[str, MenuItem] = {}
    display_names: List[str] = []  # pour fuzzy (garder noms originaux)
    for mi in menu_items:
        display_names.append(mi.name)
        name_to_item[canon(mi.name)] = mi
        for al in safe_aliases(getattr(mi, "aliases", None)):
            display_names.append(al)
            name_to_item[canon(al)] = mi

    if not menu_items:
        return OrderParseOut(
            ok=False,
            restaurant_id=resto.id,
            restaurant_name=getattr(resto, "nom_restaurant", None),
            lines=[],
            total=0.0,
            message="Menu vide",
        )

    # 3) Extraire "quantité + libellé" depuis l'utterance
    text = " " + payload.utterance.lower().strip() + " "
    # Remplacements basiques pour chiffres écrits
    replaces = {
        r"\bune\b": " 1 ",
        r"\bun\b": " 1 ",
        r"\bdeux\b": " 2 ",
        r"\btrois\b": " 3 ",
        r"\bquatre\b": " 4 ",
        r"\bcinq\b": " 5 ",
        r"\bsix\b": " 6 ",
        r"\bsept\b": " 7 ",
        r"\bhuit\b": " 8 ",
        r"\bneuf\b": " 9 ",
        r"\bdix\b": " 10 ",
    }
    for k, v in replaces.items():
        text = re.sub(k, v, text, flags=re.IGNORECASE)

    # Séparer sur " et " / "," / "+" / " ; "
    chunks = re.split(r"[,+;]|\bet\b", text)
    # Pattern: "2 margherita", "3x burger", "1 coca cola"
    qty_name_re = re.compile(r"(?P<qte>\d+)\s*x?\s*(?P<name>[a-zA-ZÀ-ÿ0-9\-\s']{2,})")

    parsed_items: List[VoiceOrderItemIn] = []
    for raw in chunks:
        raw = raw.strip()
        if not raw:
            continue

        m = qty_name_re.search(raw)
        if m:
            qte = int(m.group("qte"))
            name = m.group("name").strip()
        else:
            # pas de quantite trouvée -> on tentera 1 si un match item existe
            qte = 1
            name = raw

        # Fuzzy matching contre tous les "display_names"
        matched_display = best_match(name, display_names)
        if not matched_display:
            # Aucun match satisfaisant pour ce morceau -> on skip
            continue

        # Retrouver le MenuItem via le canon
        mi = name_to_item.get(canon(matched_display))
        if not mi:
            continue

        parsed_items.append(VoiceOrderItemIn(name=mi.name, quantity=max(1, qte)))

    # Si rien reconnu
    if not parsed_items:
        return OrderParseOut(
            ok=False,
            restaurant_id=resto.id,
            restaurant_name=getattr(resto, "nom_restaurant", None),
            lines=[],
            total=0.0,
            message="Aucun plat reconnu",
        )

    # 4) Consolider (si même item répété)
    consolidated: Dict[str, int] = {}
    for it in parsed_items:
        consolidated[it.name] = consolidated.get(it.name, 0) + int(it.quantity or 1)

    # 5) Construire lignes + total
    # Pour retrouver les prix, indexons les MenuItem par "name lower"
    price_of: Dict[str, float] = {mi.name.lower(): float(mi.price) for mi in menu_items}
    lines: List[OrderLineOut] = []
    total = 0.0
    for name, qty in consolidated.items():
        unit = price_of.get(name.lower(), 0.0)
        total += unit * qty
        lines.append(OrderLineOut(name=name, unit_price=unit, quantity=qty, note=""))

    # (Optionnel) Création d'une commande en DB si tu le souhaites
    # items_str = [f"{l.quantity} x {l.name}" for l in lines]
    # new_order = OrderModel(
    #     restaurant_id=resto.id,
    #     items=items_str,
    #     status="accepted",
    #     source="ia",
    # )
    # db.add(new_order)
    # db.commit()
    # db.refresh(new_order)

    return OrderParseOut(
        ok=True,
        restaurant_id=resto.id,
        restaurant_name=getattr(resto, "nom_restaurant", None),
        lines=lines,
        total=round(total, 2),
        message=None,
    )
