import os
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Dict, List
from models import Restaurant, MenuItem, Order
from schemas import RestaurantInfo, VoiceOrderIn, OrderOut
from routes.deps import get_db  # adapte le chemin si besoin

router = APIRouter(prefix="/voice", tags=["voice"])

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
    num = normalize_number(called_number)
    resto = db.query(Restaurant).filter(Restaurant.call_number_normalized == num).first()
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == resto.id, MenuItem.is_active == True)
        .all()
    )
    return {
        "id": resto.id,
        "name": getattr(resto, "name", None) or getattr(resto, "nom_restaurant", ""),
        "call_number": getattr(resto, "call_number", None),
        "menu": [
            {
                "id": i.id,
                "name": i.name,
                "price": i.price,
                "aliases": i.aliases or [],
            }
            for i in items
        ],
    }

@router.post("/order",
             response_model=OrderOut,
             dependencies=[Depends(require_api_key)])
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    num = normalize_number(payload.restaurant_number)
    resto = db.query(Restaurant).filter(Restaurant.call_number_normalized == num).first()
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Menu map (names + aliases)
    menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == resto.id, MenuItem.is_active == True)
        .all()
    )
    by_name = {i.name.lower(): i for i in menu_items}
    for i in menu_items:
        for a in (i.aliases or []):
            by_name[a.lower()] = i

    # Build order lines
    order_lines: List[Dict] = []
    total = 0.0
    for it in payload.items:
        key = (it.name or "").strip().lower()
        mi = by_name.get(key)
        if not mi:
            raise HTTPException(status_code=400, detail=f"Item not in menu: {it.name}")
        qty = max(1, it.quantity or 1)
        line_total = mi.price * qty
        total += line_total
        order_lines.append(
            {
                "menu_item_id": mi.id,
                "name": mi.name,
                "unit_price": mi.price,
                "quantity": qty,
                "note": it.note or "",
            }
        )

    # Idempotence on callSid (if provided)
    if payload.meta and payload.meta.get("callSid"):
        existing = (
            db.query(Order)
            .filter(
                Order.restaurant_id == resto.id,
                Order.meta["callSid"].astext == payload.meta["callSid"],
            )
            .first()
        )
        if existing:
            return existing

    order = Order.create_voice_order(
        db=db,
        restaurant_id=resto.id,
        items=order_lines,
        customer_phone=payload.customer_phone,
        customer_name=payload.customer_name,
        channel=payload.channel,
        meta=payload.meta,
        total=round(total, 2),
    )
    return order
