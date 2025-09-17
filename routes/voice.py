# routes/voice.py
import os
import json
import secrets
import unicodedata
from urllib.parse import unquote_plus
from typing import Dict, List, Iterable, Optional

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel
from schemas import RestaurantInfo, VoiceOrderIn, OrderOut, OrderLineOut

router = APIRouter(prefix="/voice", tags=["voice"])

# ---------- DB session helper ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Security ----------
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")

def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    key: Optional[str] = Query(default=None),  # fallback si header impossible côté client
):
    provided_raw = x_api_key or key
    expected = VOICE_API_KEY
    if expected:
        provided = (unquote_plus(provided_raw or "")).strip()
        if not provided or not secrets.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail="Invalid API key")

# ---------- Utils ----------
def normalize_text(s: str) -> str:
    """minuscule, sans accents, espaces compactés"""
    if not s:
        return ""
    s = s.strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = " ".join(s.split())
    return s

def parse_aliases_field(aliases_field: Optional[str]) -> List[str]:
    """
    Supporte:
      - CSV: "pizza, margherita , margarita"
      - JSON list: '["pizza","margherita","margarita"]'
      - NULL/empty
    """
    if not aliases_field:
        return []
    aliases_field = aliases_field.strip()
    try:
        if aliases_field.startswith("["):
            data = json.loads(aliases_field)
            if isinstance(data, list):
                return [str(x) for x in data if x]
    except Exception:
        pass
    # CSV
    return [p.strip() for p in aliases_field.split(",") if p.strip()]

def build_menu_index(menu_items: Iterable[MenuItem]) -> Dict[str, MenuItem]:
    """
    Crée un index "terme normalisé" -> MenuItem
    avec le nom officiel ET tous les alias.
    """
    idx: Dict[str, MenuItem] = {}
    for mi in menu_items:
        # nom officiel
        idx[normalize_text(mi.name)] = mi
        # alias
        for alias in parse_aliases_field(getattr(mi, "aliases", None)):
            idx[normalize_text(alias)] = mi
    return idx

def token_set(s: str) -> set:
    return set(normalize_text(s).split())

def best_lookup(user_phrase: str, index: Dict[str, MenuItem]) -> Optional[MenuItem]:
    """
    Essayons dans l'ordre:
      1) exact match (normalisé)
      2) contains (ex: 'pizza' contenu dans 'pizza margherita')
      3) token-set overlap > 0 (ex: 'pizza fromage' ~ 'pizza margherita')
    """
    q = normalize_text(user_phrase)
    if not q:
        return None

    # 1) exact
    if q in index:
        return index[q]

    # 2) contains
    for key, mi in index.items():
        if q in key or key in q:
            return mi

    # 3) token overlap
    q_tokens = token_set(q)
    best_item = None
    best_score = 0
    for key, mi in index.items():
        overlap = len(q_tokens & token_set(key))
        if overlap > best_score:
            best_score = overlap
            best_item = mi
    return best_item if best_score > 0 else None

def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

def find_restaurant_by_called_number(called_number: str, db: Session) -> Optional[Restaurant]:
    num = normalize_number(called_number)
    candidates = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    for r in candidates:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            return r
    return None

# ---------- Health/debug ----------
@router.get("/ping")
def ping(key: Optional[str] = Query(default=None)):
    # Permet de tester facilement la clé via ?key=...
    if VOICE_API_KEY and key and not secrets.compare_digest(key, VOICE_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"ok": True}

# ---------- API ----------
@router.get(
    "/restaurant/by-number/{called_number}",
    response_model=RestaurantInfo,
    dependencies=[Depends(require_api_key)],
)
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    resto = find_restaurant_by_called_number(called_number, db)
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()

    # On renvoie aussi les alias (si tu veux les consommer côté Voiceflow)
    def item_out(i: MenuItem) -> Dict:
        return {
            "id": i.id,
            "name": i.name,
            "price": i.price,
            "aliases": parse_aliases_field(getattr(i, "aliases", None)),
        }

    return {
        "id": resto.id,
        "nom_restaurant": getattr(resto, "nom_restaurant", None),
        "numero_appel": getattr(resto, "numero_appel", None),
        "menu": [item_out(i) for i in items],
    }

@router.post(
    "/order",
    response_model=OrderOut,
    dependencies=[Depends(require_api_key)],
)
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    """
    Expects VoiceOrderIn:
      - restaurant_number: str (numéro appelé)
      - items: List[{ name: str, quantity: int | None, note: str | None }]
    """
    resto = find_restaurant_by_called_number(payload.restaurant_number, db)
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    index = build_menu_index(menu_items)

    lines: List[OrderLineOut] = []
    total = 0.0

    for it in payload.items:
        # On match par name OU par phrase entière (ex: "1 pizza")
        # Ici, on ne parse pas la quantité depuis le texte (déjà fournie par Voiceflow)
        candidate = (
            best_lookup(it.name, index)
            if it and it.name
            else None
        )
        if not candidate:
            raise HTTPException(status_code=400, detail=f"Item not in menu: {it.name}")

        qty = max(1, int(it.quantity or 1))
        line_total = candidate.price * qty
        total += line_total

        lines.append(
            OrderLineOut(
                name=candidate.name,
                unit_price=candidate.price,
                quantity=qty,
                note=it.note or "",
            )
        )

    # Stockage compatible (liste de strings "QTY x NAME")
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

    return OrderOut(
        id=new_order.id,
        restaurant_id=resto.id,
        total=round(total, 2),
        status=new_order.status,
        lines=lines,
    )
