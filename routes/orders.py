from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel, OrderCreate, OrderResponse
from typing import List
from utils.auth import decode_token

router = APIRouter()

# Fonction pour obtenir la session de la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/orders/{restaurant_id}", response_model=List[OrderResponse])
def get_orders(restaurant_id: int, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).filter(OrderModel.restaurant_id == restaurant_id).all()
    return orders

@router.post("/orders/create", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = OrderModel(restaurant_id=order.restaurant_id, items=",".join(order.items), status="pending")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.post("/orders/accept/{order_id}")
def accept_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "accepted"
    db.commit()
    return {"message": "Commande acceptée"}

@router.post("/orders/reject/{order_id}")
def reject_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    order.status = "rejected"
    db.commit()
    return {"message": "Commande refusée"}

from fastapi import APIRouter, Depends
from utils.auth import decode_token
from models import Restaurant

router = APIRouter()

@router.get("/mes-commandes")
def get_orders(current_user: Restaurant = Depends(decode_token)):
    return {"message": f"Bienvenue {current_user.username}, voici vos commandes."}

from fastapi import APIRouter, Depends
from auth import decode_token  # Assure-toi que ce chemin est correct selon ton projet

router = APIRouter()

@router.get("/mes-commandes")
def mes_commandes_utilisateur(user=Depends(decode_token)):
    return {"message": f"Bienvenue {user.username}, voici vos commandes."}

