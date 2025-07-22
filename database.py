import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bdd_restaurant_prod_user:XsG1H00cwTEdawEBdzXT5hHlWpiXObGO@dpg-d1vjq2mmcj7s73feort0-a.oregon-postgres.render.com/bdd_restaurant_prod"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ✅ Ajout de la fonction get_db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
