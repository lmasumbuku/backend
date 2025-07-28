from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Restaurant
from schemas import (
    RestaurantBase,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    RestaurantOut,
    LoginRequest,
    TokenResponse,
    OrderCreate,
)
from security_utils import hash_password, verify_password, create_access_token

router = APIRouter()

# 🔸 Créer un restaurant
@router.post("/restaurants", response_model=RestaurantBase)
def create_restaurant(restaurant: RestaurantCreate, db: Session = Depends(get_db)):
    db_restaurant = db.query(Restaurant).filter(Restaurant.username == restaurant.username).first()
    if db_restaurant:
        raise HTTPException(status_code=400, detail="Un restaurant avec ce nom d'utilisateur existe déjà.")

    hashed_pw = hash_password(restaurant.password)
    restaurant_data = restaurant.dict()
    restaurant_data["password"] = hashed_pw

    new_restaurant = Restaurant(**restaurant_data)
    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)
    return new_restaurant

# 🔸 Connexion et génération de token
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.username == login_data.username).first()

    if not restaurant or not verify_password(login_data.password, restaurant.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect"
        )

    token_data = {
        "sub": str(restaurant.id),
        "username": restaurant.username,
    }

    access_token = create_access_token(data=token_data)
    return TokenResponse(access_token=access_token)

# 🔸 Obtenir tous les restaurants
@router.get("/restaurants", response_model=List[RestaurantOut])
def get_all_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).all()

# 🔸 Mise à jour d’un restaurateur
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

# 🔸 Obtenir un restaurateur via son numéro de téléphone (Voiceflow)
@router.get("/restaurants/from-number/{number_called}")
def get_restaurateur_by_numero(number_called: str, db: Session = Depends(get_db)):
    # Recherche du restaurant par le numéro appelé
    restaurant = db.query(Restaurant).filter(Restaurant.numero_appel == number_called).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Aucun restaurant trouvé avec ce numéro")

    return {
        "restaurant_id": restaurant.id,
        "nom_restaurant": restaurant.nom_restaurant,
        "menu": [item.name for item in restaurant.menu_items]
    }

# 🔸 Obtenir un restaurateur via son ID
@router.get("/restaurant/{restaurant_id}")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant non trouvé")
    return restaurant

# 🔸 Endpoint pour recevoir une commande de l'IA
@router.post("/orders/ia")
def create_order_from_ia(order: OrderCreate, db: Session = Depends(get_db)):
    # Vérifier si le restaurant existe
    restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant non trouvé")

    # Créer la commande
    new_order = Order(restaurant_id=order.restaurant_id, items=",".join(order.items), status="pending")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return {"message": "Commande prise en charge par l'IA et enregistrée avec succès"}

@router.put("/restaurants/update-number")
def update_phone_number(
    data: schemas.UpdatePhoneNumber,
    db: Session = Depends(get_db),
    current_restaurant: models.Restaurant = Depends(get_current_restaurant)
):
    current_restaurant.phone_number = data.phone_number
    db.commit()
    db.refresh(current_restaurant)
    return {"message": "Numéro mis à jour avec succès", "phone_number": current_restaurant.phone_number}
