from fastapi import APIRouter
from sqlalchemy import text
from database import engine, Base
from models import MenuItem

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/reset-menu-items")
def reset_menu_items():
    # 1. Suppression de la table menu_items si elle existe
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS menu_items CASCADE;"))
        connection.commit()

    # 2. Recréation de la table menu_items
    Base.metadata.create_all(bind=engine, tables=[MenuItem.__table__])

    return {"message": "La table menu_items a été réinitialisée avec succès ✅"}
