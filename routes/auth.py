from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Restaurant
from pydantic import BaseModel
import jwt
import datetime
import secrets

router = APIRouter()

SECRET_KEY = secrets.token_hex(32)

# Modèle de requête attendu pour l'inscription
class UserRegister(BaseModel):
    username: str
    password: str

# ✅ Définition de UserLogin aussi, pour la suite
class UserLogin(BaseModel):
    username: str
    password: str

# Fonction pour obtenir la session de la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fonction pour créer un token JWT
def create_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# ✅ Ajoute cette fonction pour la gestion des tokens
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ✅ Route d'inscription qui attend un JSON dans le Body
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")

    # Création du nouvel utilisateur
    new_user = Restaurant(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Inscription réussie"}
    
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey"  # 🔐 À stocker dans une variable d'environnement en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Durée de validité du token

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    restaurateur = db.query(Restaurant).filter(Restaurant.username == user.username).first()

    if not restaurateur or restaurateur.password != user.password:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": restaurateur.username,
        "exp": expire
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}
