from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Restaurant, MenuItem
from utils.hash import hash_password  # Assure-toi d’avoir un utilitaire pour hasher

router = APIRouter()

@router.post("/debug/init")
def init_demo_data(db: Session = Depends(get_db)):
    # Vérifie si l'utilisateur existe déjà
    existing = db.query(Restaurant).filter(Restaurant.username == "admin").first()
    if existing:
        return {"message": "Le compte admin existe déjà."}

    # Crée un restaurant "admin"
    admin = Restaurant(
        username="admin",
        password=hash_password("admin123"),
        nom_restaurant="Maison Pasta",
        nom_representant="Love",
        prenom_representant="Masumbuku",
        adresse_postale="123 Rue Demo, Paris",
        email="admin@maisonpasta.com",
        numero_appel="0102030405"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # Crée 2 plats
    items = [
        MenuItem(name="Pâtes carbonara", price=12.5, restaurant_id=admin.id),
        MenuItem(name="Lasagnes maison", price=14.0, restaurant_id=admin.id),
    ]
    db.add_all(items)
    db.commit()

    return {"message": "✅ Compte admin et menu de test créés avec succès."}
