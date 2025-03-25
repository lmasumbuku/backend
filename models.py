from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MenuItem, MenuItemCreate, MenuItemUpdate
from routes.auth import decode_token
from typing import List

router = APIRouter()

# 🔸 Lister tous les plats du menu pour le restaurateur connecté
@router.get("/", response_model=List[MenuItemCreate])
def list_menu_items(current_user=Depends(decode_token), db: Session = Depends(get_db)):
    return db.query(MenuItem).filter(MenuItem.restaurant_id == current_user.id).all()

# 🔸 Obtenir le détail d’un plat spécifique
@router.get("/{item_id}", response_model=MenuItemCreate)
def get_menu_item(item_id: int, current_user=Depends(decode_token), db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")
    return item

# 🔸 Ajouter un nouveau plat
@router.post("/add", response_model=MenuItemCreate)
def add_menu_item(item: MenuItemCreate, current_user=Depends(decode_token), db: Session = Depends(get_db)):
    new_item = MenuItem(
        name=item.name,
        description=item.description,
        price=item.price,
        restaurant_id=current_user.id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# 🔸 Modifier un plat existant
@router.put("/update/{item_id}", response_model=MenuItemCreate)
def update_menu_item(item_id: int, updated_data: MenuItemUpdate, current_user=Depends(decode_token), db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")
    item.name = updated_data.name
    item.description = updated_data.description
    item.price = updated_data.price
    db.commit()
    db.refresh(item)
    return item

# 🔸 Supprimer un plat
@router.delete("/delete/{item_id}")
def delete_menu_item(item_id: int, current_user=Depends(decode_token), db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé")
    db.delete(item)
    db.commit()
    return {"message": "Plat supprimé avec succès"}
