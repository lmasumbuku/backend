# routes/voice.py
import os
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel
from schemas import RestaurantInfo, VoiceOrderIn, OrderOut, OrderLineOut

router = APIRouter(prefix="/voice", tags=["voice"])

# ------------------------------------------------------------
# DB session helper
# ------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------
# Sécurité via X-API-Key
# ------------------------------------------------------------
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")

def require_api_key(x_api_key: str = Header(None)):
    # FastAPI matchera indifféremment 'X-API-Key' / 'x-api-key' côté client
    if x_api_key != VOICE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ------------------------------------------------------------
# Utils
# ------------------------------------------------------------
def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

# ------------------------------------------------------------
# DEBUG endpoints (publics, sans clé)
# ------------------------------------------------------------
@router.get("/ping")
def voice_ping():
    print("PING /voice/ping")
    return {"ok": True}

@router.get("/debug/headers")
def voice_headers(request: Request):
    print("==== /voice/debug/headers ====")
    for k, v in request.headers.items():
        print(f"{k}: {v}")
    print("================================")
    return {"headers": dict(request.headers)}

# ------------------------------------------------------------
# GET menu par numéro appelé (protégé)
# ------------------------------------------------------------
@router.get(
    "/restaurant/by-number/{called_number}",
    response_model=RestaurantInfo,
    dependencies=[Depends(require_api_key)],
)
def get_restaurant_by_number(
    called_number: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # Logs debug pour voir la requête qui arrive réellement
    print("==== HEADERS RECUS ====")
    for k, v in request.headers.items():
        print(f"{k}: {v}")
    print("=======================")

    num = normalize_number(called_number)

    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    match = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            match = r
            break

    if not match:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == match.id).all()

    return {
        "id": match.id,
        "nom_restaurant": getattr(match, "nom_restaurant", None),
        "numero_appel": getattr(match, "numero_appel", None),
        "menu": [
            {"id": i.id, "name": i.name, "price": i.price, "aliases": []}
            for i in items
        ],
    }

# ------------------------------------------------------------
# POST order (protégé)
# ------------------------------------------------------------
@router.post(
    "/order",
    response_model=OrderOut,
    dependencies=[Depends(require_api_key)],
)
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    num = normalize_number(payload.restaurant_number)

    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    resto = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    by_name = {i.name.strip().lower(): i for i in menu_items}

    lines: List[OrderLineOut] = []
    total = 0.0

    for it in payload.items:
        key = (it.name or "").strip().lower()
        mi = by_name.get(key)
        if not mi:
            raise HTTPException(status_code=400, detail=f"Item not in menu: {it.name}")
        qty = max(1, int(it.quantity or 1))
        line_total = (mi.price or 0) * qty
        total += line_total

        lines.append(
            OrderLineOut(
                name=mi.name,
                unit_price=mi.price,
                quantity=qty,
                note=it.note or "",
            )
        )

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
