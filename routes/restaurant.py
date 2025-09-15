from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

# ✅ Imports Pydantic (on importe explicitement les classes utilisées)
from schemas import (
    UpdatePhoneNumber,
    RestaurantBase,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    RestaurantOut,
    LoginRequest,
    TokenResponse,
    OrderCreate,
)

# ✅ DB / Models
from database import get_db
from models import Restaurant, Order as OrderModel  # <- OrderModel importé ici

# ✅ Auth utils
from security_utils import hash_password, verify_password, create_access_token
from routes.secure_routes import get_current_restaurant

router = APIRouter()

# Petit helper pour normaliser les numéros (retire espaces, +, etc.)
def normalize_number(num: str) -> str:
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    # option : 00xx -> xx
    if digits.startswith("00"):
        digits = digits[2:]
    return digits

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
    # Normalisation pour comparer proprement
    target = normalize_number(number_called)

    # On récupère tous les restos qui ont un numero_appel défini
    restaurants = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()

    match = None
    for r in restaurants:
        if normalize_number(getattr(r, "numero_appel", "")) == target:
            match = r
            break

    if not match:
        raise HTTPException(status_code=404, detail="Aucun restaurant trouvé avec ce numéro")

    return {
        "restaurant_id": match.id,
        "nom_restaurant": match.nom_restaurant,
        "menu": [item.name for item in match.menu_items]
    }

# 🔸 Obtenir un restaurateur via son ID
@router.get("/restaurant/{restaurant_id}")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant non trouvé")
    return restaurant

# 🔸 Endpoint pour recevoir une commande de l'IA (legacy interne)
@router.post("/orders/ia")
def create_order_from_ia(order: OrderCreate, db: Session = Depends(get_db)):
    # Vérifier si le restaurant existe
    restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant non trouvé")

    # ⚠️ Selon ton modèle DB, items peut être JSON/ARRAY ou TEXT.
    # Si c'est une colonne texte, on join pour stocker "1 x Pizza, 2 x Coca".
    items_value = order.items
    if not isinstance(items_value, list):
        # sécurité minimale
        items_value = [str(items_value)]

    # Si ta colonne Order.items est TEXT, décommente la ligne suivante :
    # items_value = ", ".join(items_value)

    new_order = OrderModel(
        restaurant_id=order.restaurant_id,
        items=items_value,       # <-- adapte selon le type de colonne en DB
        status="pending",
        source="ia"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return {"message": "Commande prise en charge par l'IA et enregistrée avec succès", "order_id": new_order.id}

# ✅ Modifier le numéro d’appel vocal du restaurateur connecté
@router.put("/restaurants/update-number")
def update_phone_number(
    data: UpdatePhoneNumber,                             # <- on utilise la classe importée
    db: Session = Depends(get_db),
    current_restaurant: Restaurant = Depends(get_current_restaurant)  # <- type correct
):
    current_restaurant.numero_appel = data.numero_appel
    db.commit()
    db.refresh(current_restaurant)
    return {"message": "Numéro mis à jour avec succès", "numero_appel": current_restaurant.numero_appel}
