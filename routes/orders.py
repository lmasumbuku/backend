from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel, OrderCreate, OrderResponse, Restaurant
from typing import List
from routes.auth import decode_token  # Assure-toi que ce chemin est correct selon ton projet

router = APIRouter()

# Fonction pour obtenir la session de la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Liste des commandes pour un restaurant spécifique (accessible sans token)
@router.get("/{restaurant_id}", response_model=List[OrderResponse])
def get_orders(restaurant_id: int, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).filter(OrderModel.restaurant_id == restaurant_id).all()
    return orders

# ✅ Créer une commande
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

# ✅ Accepter une commande
@router.post("/accept/{order_id}")
def accept_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "accepted"
    db.commit()
    return {"message": "Commande acceptée"}

# ✅ Refuser une commande
@router.post("/reject/{order_id}")
def reject_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "rejected"
    db.commit()
    return {"message": "Commande refusée"}

# ✅ Voir ses propres commandes (avec authentification via token)
@router.get("/mes-commandes")
def mes_commandes_utilisateur(current_user: Restaurant = Depends(decode_token), db: Session = Depends(get_db)):
    commandes = db.query(OrderModel).filter(OrderModel.restaurant_id == current_user.id).all()
    return commandes
