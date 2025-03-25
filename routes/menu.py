from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import MenuItem, MenuItemCreate, MenuItemResponse, Restaurant
from routes.auth import decode_token
from typing import List

router = APIRouter()

# Fonction pour obtenir la session de la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Route pour ajouter un plat au menu
@router.post("/add", response_model=MenuItemResponse)
def add_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
    new_item = MenuItem(
        name=item.name,
        price=item.price,
        restaurant_id=current_user.id  # Automatiquement extrait du token
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# ✅ Route pour récupérer le menu du restaurateur connecté
@router.get("/", response_model=List[MenuItemResponse])
def get_my_menu(
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == current_user.id).all()
    return menu_items
