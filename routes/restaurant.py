from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Restaurant
from schemas import RestaurantUpdate, RestaurantResponse, RestaurantCreate, RestaurantOut

router = APIRouter()

@router.get("/restaurants", response_model=List[RestaurantOut])
def get_all_restaurants(db: Session = Depends(get_db)):
    return db.query(models.Restaurant).all()

# 🔄 Mettre à jour les informations d’un restaurateur
@router.put("/restaurant/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(restaurant_id: int, updates: RestaurantUpdate, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant non trouvé")

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(restaurant, key, value)

    db.commit()
    db.refresh(restaurant)
    return restaurant


# 🔎 Obtenir un restaurateur via son numéro de téléphone (appelé par Voiceflow)
@router.get("/restaurant-par-numero")
def get_restaurateur_by_numero(numero: str = Query(...), db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.numero_appel == numero).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Aucun restaurant trouvé avec ce numéro")

    return {
        "restaurant_id": restaurant.id,
        "nom_restaurant": restaurant.nom_restaurant,
        "menu": [item.name for item in restaurant.menu_items]  # On peut détailler plus tard
    }
