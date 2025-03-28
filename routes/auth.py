from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Restaurant
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta

router = APIRouter()

# 🔐 Clés et config token
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 🔐 OAuth2PasswordBearer modifié pour Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# 🔐 Modèles
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# 🔐 Créer un token
def create_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# 🔐 Décrypter le token et retourner le restaurateur
def decode_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Restaurant:
    if token is None:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        user = db.query(Restaurant).filter(Restaurant.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

# 🔐 Route d’inscription
@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")

    new_user = Restaurant(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Inscription réussie"}

# 🔐 Route de connexion
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    restaurateur = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if not restaurateur or restaurateur.password != user.password:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_token(restaurateur.username)
    return {"access_token": token, "token_type": "bearer"}
