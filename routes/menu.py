from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MenuItem, MenuItemCreate, MenuItemUpdate, Restaurant
from typing import List
from routes.auth import decode_token  # On utilise l'authentification via token

router = APIRouter()

# ✅ Ajouter un plat au menu
@router.post("/add", response_model=MenuItem)
def add_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
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

# ✅ Voir tous les plats du menu du restaurateur connecté
@router.get("/mes-plats", response_model=List[MenuItem])
def get_my_items(
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
    return db.query(MenuItem).filter(MenuItem.restaurant_id == current_user.id).all()

# ✅ Supprimer un plat de son menu
@router.delete("/delete/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé ou accès non autorisé")
    db.delete(item)
    db.commit()
    return {"message": "Plat supprimé avec succès"}

# ✅ Modifier un plat existant
@router.put("/edit/{item_id}", response_model=MenuItem)
def update_item(
    item_id: int,
    item_update: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: Restaurant = Depends(decode_token)
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plat non trouvé ou accès non autorisé")

    item.name = item_update.name
    item.description = item_update.description
    item.price = item_update.price
    db.commit()
    db.refresh(item)
    return item
