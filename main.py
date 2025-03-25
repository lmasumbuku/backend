from fastapi import FastAPI
from routes.auth import router as auth_router
from routes.orders import router as orders_router
from routes.menu import router as menu_router
from database import Base, engine
import models

app = FastAPI()

Base.metadata.create_all(bind=engine)  # Création des tables

app.include_router(auth_router, prefix="/auth")
app.include_router(orders_router, prefix="/orders")
app.include_router(menu_router, prefix="/menu")

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API des restaurateurs !"}
