from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel, OrderCreate, OrderResponse, Restaurant
from typing import List
from routes.auth import decode_token

router = APIRouter()

# DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Route protégée par token (à placer en premier)
@router.get("/mes-commandes")
def mes_commandes_utilisateur(user: Restaurant = Depends(decode_token)):
    return {"message": f"Bienvenue {user.username}, voici vos commandes."}

# Route : Créer commande
@router.post("/create", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = OrderModel(
        restaurant_id=order.restaurant_id,
        items=",".join(order.items),
        status="pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# Route : Accepter commande
@router.post("/accept/{order_id}")
def accept_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "accepted"
    db.commit()
    return {"message": "Commande acceptée"}

# Route : Refuser commande
@router.post("/reject/{order_id}")
def reject_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "rejected"
    db.commit()
    return {"message": "Commande refusée"}

# Route : Voir les commandes par restaurant_id (à placer en dernier)
@router.get("/{restaurant_id}", response_model=List[OrderResponse])
def get_orders(restaurant_id: int, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).filter(OrderModel.restaurant_id == restaurant_id).all()
    return orders
