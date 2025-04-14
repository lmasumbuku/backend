from fastapi import APIRouter
from sqlalchemy import text
from database import engine, Base
from models import MenuItem, Restaurant

router = APIRouter(prefix="/debug", tags=["debug"])

# 🔁 Réinitialisation de la table menu_items
@router.get("/reset-menu-items")
def reset_menu_items():
    print(">>> [DEBUG] Route /reset-menu-items appelée")

    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS menu_items CASCADE;"))
        connection.commit()

    Base.metadata.create_all(bind=engine, tables=[MenuItem.__table__])
    return {"message": "La table menu_items a été réinitialisée avec succès ✅"}

# 🔁 Réinitialisation de la table restaurants
@router.get("/reset-restaurants")
def reset_restaurants():
    print(">>> [DEBUG] Route /reset-restaurants appelée")

    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS restaurants CASCADE;"))
        connection.commit()

    Base.metadata.create_all(bind=engine, tables=[Restaurant.__table__])
    return {"message": "La table restaurants a été réinitialisée avec succès ✅"}
