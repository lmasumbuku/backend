from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import MenuItem as MenuItemModel, MenuItemCreate, MenuItemResponse
from typing import List

router = APIRouter()

# ✅ Fonction pour obtenir la session de la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/menu/{restaurant_id}", response_model=List[MenuItemResponse])
def get_menu(restaurant_id: int, db: Session = Depends(get_db)):
    menu = db.query(MenuItemModel).filter(MenuItemModel.restaurant_id == restaurant_id).all()
    return menu

@router.post("/menu/{restaurant_id}/add", response_model=MenuItemResponse)
def add_menu_item(restaurant_id: int, item: MenuItemCreate, db: Session = Depends(get_db)):
    new_item = MenuItemModel(name=item.name, price=item.price, restaurant_id=restaurant_id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.delete("/menu/{restaurant_id}/remove")
def remove_menu_item(restaurant_id: int, item_name: str, db: Session = Depends(get_db)):
    item = db.query(MenuItemModel).filter(MenuItemModel.restaurant_id == restaurant_id, MenuItemModel.name == item_name).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")
    db.delete(item)
    db.commit()
    return {"message": "Plat supprimé"}
