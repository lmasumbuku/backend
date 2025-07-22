from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from startup import create_tables_if_not_exist
from routes.auth import router as auth_router
from routes.orders import router as orders_router
from routes.menu import router as menu_router
from routes.debug import router as debug_router
from routes.vocal_routes import router as vocal_router
from routes.voiceflow_commande import router as voiceflow_commande_router
from routes.restaurant import router as restaurant_router
from routes.status import router as status_router
from routes import secure_routes
from routes.init_debug import router as init_debug_router
from database import Base, engine

create_tables_if_not_exist()

app = FastAPI()

# 🔐 Autoriser les requêtes depuis le frontend React (mettre l’URL exacte en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-46us.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 Inclusion des routes
app.include_router(auth_router, prefix="/auth")
app.include_router(orders_router, prefix="/orders")
app.include_router(menu_router, prefix="/menu")
app.include_router(debug_router)
app.include_router(vocal_router)
app.include_router(voiceflow_commande_router, prefix="/voiceflow-commande")
app.include_router(restaurant_router)
app.include_router(secure_routes.router, prefix="/secure", tags=["Secure Routes"])
app.include_router(init_debug_router)
app.include_router(status_router)

# 🌐 Route de base
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API des restaurateurs !"}

# 📦 Route pour créer manuellement les tables (utile en dev/debug)
create_router = APIRouter()

@create_router.get("/create-tables")
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Tables créées avec succès ✅"}
    except Exception as e:
        return {"error": str(e)}

app.include_router(create_router)
