from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.orders import router as orders_router
from routes.menu import router as menu_router
from routes.debug import router as debug_router
from routes.vocal_routes import router as vocal_router
from database import Base, engine
import models
from fastapi import APIRouter

app = FastAPI()

# Autoriser les requêtes depuis le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-46us.onrender.com"],  # En production : remplace "*" par l'URL de ton frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)  # Création des tables

app.include_router(auth_router, prefix="/auth")
app.include_router(orders_router, prefix="/orders")
app.include_router(menu_router, prefix="/menu")
app.include_router(debug_router)
app.include_router(vocal_routes.router)

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API des restaurateurs !"}
create_router = APIRouter()

@create_router.get("/create-tables")
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Tables créées avec succès ✅"}
    except Exception as e:
        return {"error": str(e)}

app.include_router(create_router)
