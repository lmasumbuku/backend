# routes/voice.py
import os
import secrets
from urllib.parse import unquote_plus

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel
from schemas import (
    RestaurantInfo,
    VoiceOrderIn,
    OrderOut,
    OrderLineOut,
)

# ============================================================
#  Config & helpers
# ============================================================

VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_api_key(x_api_key: str = Header(None)):
    """
    Authentifie via le HEADER HTTP 'x-api-key' uniquement.
    (Pas de query string, pas de fallback.)
    """
    expected = VOICE_API_KEY
    if not expected or expected == "change-me":
        # Sécurité minimale : on refuse si la clé serveur est mal configurée
        raise HTTPException(status_code=500, detail="Server API key not configured")

    # Décode proprement le header si Cloudflare/Proxy encode des caractères spéciaux
    provided = (unquote_plus(x_api_key).strip() if x_api_key else None)

    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")

def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

# ============================================================
#  Router (protège TOUTES les routes /voice/*)
# ============================================================

router = APIRouter(
    prefix="/voice",
    tags=["voice"],
    dependencies=[Depends(require_api_key)],
)

# --- Santé / debug (protégés) --------------------------------

@router.get("/ping")
def ping():
    return {"ok": True}

@router.get("/debug/headers")
async def debug_headers(request: Request):
    # Utile si tu veux vérifier ce que Voiceflow envoie en prod
    return {"headers": dict(request.headers)}

# ============================================================
#  Endpoints métier
# ============================================================

@router.get(
    "/restaurant/by-number/{called_number}",
    response_model=RestaurantInfo,
)
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    """
    Retourne le restaurant associé à 'called_number' + son menu.
    """
    num = normalize_number(called_number)

    # Recherche souple par numéro normalisé
    resto_match = None
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto_match = r
            break

    if not resto_match:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto_match.id).all()

    return {
        "id": resto_match.id,
        "nom_restaurant": getattr(resto_match, "nom_restaurant", None),
        "numero_appel": getattr(resto_match, "numero_appel", None),
        "menu": [
            {
                "id": it.id,
                "name": it.name,
                "price": it.price,
                "aliases": [],  # pas d'aliases pour l’instant
            }
            for it in items
        ],
    }

@router.post(
    "/order",
    response_model=OrderOut,
)
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    """
    Crée une commande à partir d'items (name, quantity, note),
    valide les produits avec le menu du restaurant et calcule le total.
    """
    num = normalize_number(payload.restaurant_number)

    # 1) Trouver le restaurant
    resto = None
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # 2) Charger le menu
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    by_name = {i.name.strip().lower(): i for i in menu_items}

    # 3) Construire les lignes + total
    lines: List[OrderLineOut] = []
    total = 0.0

    for it in payload.items:
        key = (it.name or "").strip().lower()
        mi = by_name.get(key)
        if not mi:
            raise HTTPException(status_code=400, detail=f"Item not in menu: {it.name}")

        qty = max(1, int(it.quantity or 1))
        line_total = mi.price * qty
        total += line_total

        lines.append(
            OrderLineOut(
                name=mi.name,
                unit_price=mi.price,
                quantity=qty,
                note=it.note or "",
            )
        )

    # 4) Persister une commande simple (items sous forme "QTY x NAME")
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

    # 5) Réponse
    return OrderOut(
        id=new_order.id,
        restaurant_id=resto.id,
        total=round(total, 2),
        status=new_order.status,
        lines=lines,
    )
