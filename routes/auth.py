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
    print(user.dict())  # Affiche les données reçues
    return {"message": "Debug : inscription en cours"}
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")

    # Création du nouvel utilisateur
    new_user = Restaurant(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Inscription réussie"}
    
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    print(user.dict())  # Affiche les données reçues pour debug
    return {"message": "Debug : connexion en cours"}
    existing_user = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if not existing_user or existing_user.password != user.password:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    # Génération du token
    access_token = jwt.encode({"sub": user.username}, "secret", algorithm="HS256")
    return {"access_token": access_token, "token_type": "bearer"}
