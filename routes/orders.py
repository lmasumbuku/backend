from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel, Restaurant
from schemas import OrderCreate, OrderResponse
from typing import List
from routes.auth import decode_token

router = APIRouter()

# Obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔐 Voir MES commandes (à partir du token)
@router.get("/mes-commandes", response_model=List[OrderResponse])
def get_my_orders(current_user: Restaurant = Depends(decode_token), db: Session = Depends(get_db)):
    orders = db.query(OrderModel).filter(OrderModel.restaurant_id == current_user.id).all()
    return [
        {
            "id": order.id,
            "restaurant_id": order.restaurant_id,
            "items": order.items.split(",") if order.items else [],
            "status": order.status,
            "source": order.source
        }
        for order in orders
    ]

# ✅ Créer une commande (acceptée automatiquement)
@router.post("/create", response_model=OrderResponse)
def create_order(order: OrderCreate, 
                 db: Session = Depends(get_db), 
                 current_user: Restaurant = Depends(decode_token)):
    new_order = OrderModel(
        restaurant_id=current_user.id,
        items=",".join(order.items),
        status="accepted",  # ✅ Commande acceptée automatiquement
        source=order.source or "web"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return {
        "id": new_order.id,
        "restaurant_id": new_order.restaurant_id,
        "items": new_order.items.split(","),
        "status": new_order.status
    }

# ✅ Accepter une commande (optionnel)
@router.post("/accept/{order_id}")
def accept_order(order_id: int, current_user: Restaurant = Depends(decode_token), db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id, OrderModel.restaurant_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "accepted"
    db.commit()
    return {"message": "Commande acceptée"}

# ✅ Refuser une commande (optionnel)
@router.post("/reject/{order_id}")
def reject_order(order_id: int, current_user: Restaurant = Depends(decode_token), db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id, OrderModel.restaurant_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "rejected"
    db.commit()
    return {"message": "Commande refusée"}
