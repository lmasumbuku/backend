import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bdd_restaurant_dev_user:LlinJ60pxk7rZaqRTh3YczZQtoO6eEX6@dpg-d03stp9r0fns739g8820-a.oregon-postgres.render.com/bdd_restaurant_dev?sslmode=require"
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
