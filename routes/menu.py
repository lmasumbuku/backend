from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import MenuItem, MenuItemCreate, MenuItemResponse, Restaurant
from database import get_db
from auth import decode_token
from typing import List

router = APIRouter()

@router.post("/{restaurant_id}/add", response_model=MenuItemResponse)
def add_menu_item(restaurant_id: int, item: MenuItemCreate, db: Session = Depends(get_db), user: Restaurant = Depends(decode_token)):
    if user.id != restaurant_id:
        raise HTTPException(status_code=403, detail="Non autorisé à ajouter un plat pour ce restaurant")

    new_item = MenuItem(restaurant_id=restaurant_id, name=item.name, price=item.price)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/{restaurant_id}", response_model=List[MenuItemResponse])
def get_menu(restaurant_id: int, db: Session = Depends(get_db)):
    menu = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    return menu
