# routes/voice.py
import os
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from typing import Dict, List
from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel
from schemas import RestaurantInfo, VoiceOrderIn, OrderOut, OrderLineOut, MenuItemOut

router = APIRouter(prefix="/voice", tags=["voice"])

# --- DB session helper (local pour éviter dépendances externes) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Sécurité simple MVP ---
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")
def require_api_key(x_api_key: str = Header(None)):
    if x_api_key != VOICE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

@router.get("/restaurant/by-number/{called_number}",
            response_model=RestaurantInfo,
            dependencies=[Depends(require_api_key)])
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    """
    Retourne les infos du restaurant (nom, numero_appel) + son menu actif.
    On matche sur Restaurant.numero_appel (normalisé).
    """
    num = normalize_number(called_number)
    resto = (
        db.query(Restaurant)
        .filter(Restaurant.numero_appel.isnot(None))
        .all()
    )
    # match souple (normalisation)
    match = None
    for r in resto:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            match = r
            break
    if not match:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == match.id)
        .all()
    )

    return {
        "id": match.id,
        "nom_restaurant": getattr(match, "nom_restaurant", None),
        "numero_appel": getattr(match, "numero_appel", None),
        "menu": [
            {
                "id": i.id,
                "name": i.name,
                "price": i.price,
                "aliases": [],  # pas d'aliases en base pour l'instant
            }
            for i in items
        ],
    }

@router.post("/order",
             response_model=OrderOut,
             dependencies=[Depends(require_api_key)])
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    """
    Crée une commande structurée à partir d'items (name, quantity, note).
    - Valide les items sur le menu du restaurant (name exact, insensible à la casse).
    - Calcule 'total' et renvoie des 'lines' complètes dans la réponse.
    - Stocke en base Order.items comme une liste de chaînes "QTY x NAME" (compatible avec ton modèle actuel).
    """
    num = normalize_number(payload.restaurant_number)
    # Lookup restaurant
    restos = (
        db.query(Restaurant)
        .filter(Restaurant.numero_appel.isnot(None))
        .all()
    )
    resto = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Charger le menu
    menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == resto.id)
        .all()
    )
    # Map nom (lower) -> MenuItem
    by_name = {i.name.strip().lower(): i for i in menu_items}

    # Construire les lignes et total
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
        lines.append(OrderLineOut(name=mi.name, unit_price=mi.price, quantity=qty, note=it.note or ""))

    # Stockage compatible avec ton modèle actuel (Order.items: List[str])
    items_str = [f"{l.quantity} x {l.name}" for l in lines]
    new_order = OrderModel(
        restaurant_id=resto.id,
        items=items_str,
        status="accepted",   # cohérent avec ton précédent code
        source="ia"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Réponse enrichie (OrderOut) calculée à la volée
    return OrderOut(
        id=new_order.id,
        restaurant_id=resto.id,
        total=round(total, 2),
        status=new_order.status,
        lines=lines
    )

from fastapi import Request

@router.get("/voice/restaurant/by-number/{restaurant_number}")
async def get_restaurant_by_number(restaurant_number: str, request: Request, db: Session = Depends(get_db)):
    # Log tous les headers reçus
    headers = dict(request.headers)
    print("==== HEADERS RECUS ====")
    for k, v in headers.items():
        print(f"{k}: {v}")
    print("=======================")

    # Ici, tu continues ton traitement normal
    restaurant = db.query(Restaurant).filter(Restaurant.number == restaurant_number).first()
    if not restaurant:
        return {"error": "Restaurant not found"}

    return {
        "restaurant_name": restaurant.name,
        "menu": [item.name for item in restaurant.menu_items]
    }
