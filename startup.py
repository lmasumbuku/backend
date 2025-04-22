from sqlalchemy import inspect
from database import Base, engine
from models import Restaurant, MenuItem

def create_tables_if_not_exist():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "restaurants" not in tables or "menu_items" not in tables:
        print("✅ Création automatique des tables manquantes...")
        Base.metadata.create_all(bind=engine)
    else:
        print("✅ Les tables existent déjà.")
