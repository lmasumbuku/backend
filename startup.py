from sqlalchemy import inspect
from database import Base, engine
from models import Restaurant, MenuItem, Order

def create_tables_if_not_exist():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "restaurants" not in existing_tables:
        print("📦 Table 'restaurants' manquante : création en cours…")
    if "menu_items" not in existing_tables:
        print("📦 Table 'menu_items' manquante : création en cours…")
    if "orders" not in existing_tables:
        print("📦 Table 'orders' manquante : création en cours…")

    Base.metadata.create_all(bind=engine)

    print("✅ Vérification terminée : toutes les tables sont prêtes.")
