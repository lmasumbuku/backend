from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MenuItem, MenuItemCreate, MenuItemUpdate, MenuItemResponse, Restaurant
from routes.auth import decode_token
from typing import List

router = APIRouter()

# ✅ Ajouter un plat au menu du restaurateur connecté
@router.post("/add", response_model=MenuItemResponse)
def add_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    user: Restaurant = Depends(decode_token)
):
    new_item = MenuItem(
        name=item.name,
        description=item.description,
        price=item.price,
        restaurant_id=user.id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# ✅ Récupérer tous les plats du menu du restaurateur connecté
@router.get("/mes-plats", response_model=List[MenuItemResponse])
def get_menu_items(
    db: Session = Depends(get_db),
    user: Restaurant = Depends(decode_token)
):
    return db.query(MenuItem).filter(MenuItem.restaurant_id == user.id).all()

# ✅ Modifier un plat du menu
@router.put("/modifier/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: int,
    item: MenuItemUpdate,
    db: Session = Depends(get_db),
    user: Restaurant = Depends(decode_token)
):
    menu_item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == user.id).first()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")

    if item.name is not None:
        menu_item.name = item.name
    if item.description is not None:
        menu_item.description = item.description
    if item.price is not None:
        menu_item.price = item.price

    db.commit()
    db.refresh(menu_item)
    return menu_item

# ✅ Supprimer un plat du menu
@router.delete("/supprimer/{item_id}")
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: Restaurant = Depends(decode_token)
):
    menu_item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == user.id).first()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")

    db.delete(menu_item)
    db.commit()
    return {"message": "Plat supprimé avec succès"}
