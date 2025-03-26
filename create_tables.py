from database import Base, engine
from models import *

print("🔄 Création des tables…")
Base.metadata.create_all(bind=engine)
print("✅ Terminé.")
