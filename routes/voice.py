# routes/voice.py
import os
import re
import secrets
from urllib.parse import unquote_plus
from typing import Generator, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel

router = APIRouter(prefix="/voice", tags=["voice"])

# ---------------------------
# DB session helper
# ---------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Security (API Key)
# ---------------------------
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me").strip()

def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    key: Optional[str] = Query(default=None),
):
    """
    Accepte soit le header `x-api-key`, soit le query param `?key=`.
    Les valeurs peuvent être url-encodées (on les decode).
    """
    provided_raw = x_api_key or key
    if not provided_raw:
        raise HTTPException(status_code=401, detail="Invalid API key")

    provided = unquote_plus(str(provided_raw)).strip()
    expected = VOICE_API_KEY

    if not provided or not expected or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---------------------------
# Utils
# ---------------------------
def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    # Retirer 00 ou + au début (on normalise)
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

# ---------------------------
# Schemas (pour /order/parse)
# ---------------------------
class ParseOrderIn(BaseModel):
    restaurant_number: str = Field(..., description="Numéro du restaurant (ex: +33755123456)")
    utterance: str = Field(..., description="Texte saisi/parlé par l'utilisateur")
    create: bool = Field(False, description="Créer la commande en DB si True")

class ParsedLineOut(BaseModel):
    name: str
    unit_price: float
    quantity: int
    note: str = ""

class ParsedOrderOut(BaseModel):
    lines: List[ParsedLineOut]
    total: float
    order_id: Optional[int] = None  # présent si create=True

# ---------------------------
# Endpoints
# ---------------------------

@router.get("/ping")
def ping():
    return {"ok": True}

@router.get(
    "/restaurant/by-number/{called_number}",
    dependencies=[Depends(require_api_key)]
)
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    """
    Renvoie les infos d'un restaurant + menu à partir d'un numéro appelé.
    """
    num = normalize_number(called_number)

    # On récupère tous les restos ayant un numero_appel non nul, puis on compare normalisé
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    resto = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break

    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()

    return {
        "id": resto.id,
        "nom_restaurant": getattr(resto, "nom_restaurant", None),
        "numero_appel": getattr(resto, "numero_appel", None),
        "menu": [
            {
                "id": i.id,
                "name": i.name,
                "price": float(i.price),
                "aliases": [],  # à remplir plus tard si tu ajoutes les alias en DB
            }
            for i in items
        ],
    }

@router.post(
    "/order/parse",
    response_model=ParsedOrderOut,
    dependencies=[Depends(require_api_key)]
)
def parse_order(payload: ParseOrderIn, db: Session = Depends(get_db)):
    """
    Analyse une 'utterance' (ex: '2 margherita et 1 coca') avec le menu du resto,
    renvoie des lignes structurées + total. Si create=True, crée l'Order en DB.
    """

    # 1) Récupérer le resto par numéro
    num = normalize_number(payload.restaurant_number)
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    resto = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 2) Charger le menu
    menu_items: List[MenuItem] = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    if not menu_items:
        raise HTTPException(status_code=400, detail="Empty menu")

    # Map pour matching simple
    # (améliorable avec alias/levenshtein plus tard)
    by_name = {i.name.strip().lower(): i for i in menu_items}

    utter = (payload.utterance or "").lower().strip()
    if not utter:
        raise HTTPException(status_code=400, detail="Empty utterance")

    # 3) Parsing naïf:
    #    - RegExp pour attraper "2 pizza", "1 coca", "3x margherita", etc.
    #    - Fallback: si un item du menu est contenu dans la phrase, on met qty=1
    lines: List[ParsedLineOut] = []

    # a) Tentative avec regex "nombre + nom"
    pattern = re.compile(r"(\d+)\s*x?\s*([a-zA-ZÀ-ÿ' -]+)")
    matches = pattern.findall(utter)

    used_span_texts = set()
    if matches:
        for qty_str, item_text in matches:
            qty = max(1, int(qty_str))
            candidate = item_text.strip().lower()

            # Chercher le meilleur item dont le nom est contenu dans 'candidate'
            matched_item: Optional[MenuItem] = None
            for key, mi in by_name.items():
                if key in candidate or candidate in key:
                    matched_item = mi
                    break

            if matched_item:
                lines.append(
                    ParsedLineOut(
                        name=matched_item.name,
                        unit_price=float(matched_item.price),
                        quantity=qty,
                    )
                )
                used_span_texts.add(candidate)

    # b) Fallback : items détectés sans nombre -> qty=1
    if not lines:
        for key, mi in by_name.items():
            if key in utter:
                lines.append(
                    ParsedLineOut(
                        name=mi.name,
                        unit_price=float(mi.price),
                        quantity=1,
                    )
                )

    if not lines:
        raise HTTPException(status_code=400, detail="No items recognized")

    # 4) Calcul du total
    total = sum(l.unit_price * l.quantity for l in lines)

    order_id: Optional[int] = None
    if payload.create:
        # 5) Création de la commande en DB (format actuel: items -> ["2 x Pizza", "1 x Coca"])
        items_str = [f"{l.quantity} x {l.name}" for l in lines]
        new_order = OrderModel(
            restaurant_id=resto.id,
            items=items_str,
            status="accepted",
            source="ia",
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        order_id = new_order.id

    return ParsedOrderOut(lines=lines, total=round(total, 2), order_id=order_id)
