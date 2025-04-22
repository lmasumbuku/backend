from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_current_restaurant
from database import get_db
from schemas import RestaurantOut

router = APIRouter()

# 🔐 Route sécurisée pour afficher le profil du restaurateur connecté
@router.get("/me", response_model=RestaurantOut)
def get_my_profile(current_restaurant=Depends(get_current_restaurant), db: Session = Depends(get_db)):
    return current_restaurant

# 🔐 Exemple de route protégée personnalisée
@router.get("/hello-secure")
def say_hello(current_restaurant=Depends(get_current_restaurant)):
    return {"message": f"Bonjour {current_restaurant.nom_restaurant} ! Bienvenue dans votre espace sécurisé."}
