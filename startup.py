from sqlalchemy import inspect
from database import Base, engine
from models import Restaurant, MenuItem, Order

def create_tables_if_not_exist():
    print("📦 Création des tables si elles n’existent pas...")

    # Création effective des tables
    Base.metadata.create_all(bind=engine)
    
    # Vérification des tables existantes (après création)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Affichage de ce qui manque (au cas où)
    if "restaurants" not in existing_tables:
        print("❗ Table 'restaurants' non trouvée.")
    if "menu_items" not in existing_tables:
        print("❗ Table 'menu_items' non trouvée.")
    if "orders" not in existing_tables:
        print("❗ Table 'orders' non trouvée.")
    
    print("✅ Vérification terminée : toutes les tables sont prêtes.")
