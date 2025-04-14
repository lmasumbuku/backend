from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Restaurant, RestaurantUpdate, RestaurantResponse

router = APIRouter()

# 🔄 Route de mise à jour du profil
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

# 🆕 Route pour identifier un restaurant à partir de son numéro de ligne vocale
@router.get("/restaurant/by-numero")
def get_restaurateur_by_numero(numero: str = Query(...), db: Session = Depends(get_
