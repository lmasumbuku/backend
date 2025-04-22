import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bdd_restaurant_user:VCy0VOy9xOanCwwPg1Nk3XoaTc6cBvhP@dpg-cvdelubv2p9s73cehhvg-a.oregon-postgres.render.com/bdd_restaurant?sslmode=require"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ✅ Ajout de la fonction get_db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
      
