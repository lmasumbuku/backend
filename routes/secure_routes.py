from fastapi import APIRouter, Depends
from dependencies import get_current_restaurant

router = APIRouter()

@router.get("/me")
def get_my_profile(current_restaurant=Depends(get_current_restaurant)):
    return {
        "id": current_restaurant.id,
        "username": current_restaurant.username,
        "nom_restaurant": current_restaurant.nom_restaurant
    }

@router.get("/secure-hello")
def hello_protected(current_restaurant=Depends(get_current_restaurant)):
    return {"message": f"Bonjour {current_restaurant.nom_restaurant} !"}
