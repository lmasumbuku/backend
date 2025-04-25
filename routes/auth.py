from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Restaurant
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from security_utils import hash_password, verify_password, create_access_token  # Import des utils de sécurité

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
    nom_restaurant: str
    nom_representant: str
    prenom_representant: str
    adresse_postale: str
    email: str
    numero_appel: str

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

    # Hachage du mot de passe avant de le stocker
    hashed_pw = hash_password(user.password)

    new_user = Restaurant(
        username=user.username,
        password=hashed_pw,
        nom_restaurant=user.nom_restaurant,
        nom_representant=user.nom_representant,
        prenom_representant=user.prenom_representant,
        adresse_postale=user.adresse_postale,
        email=user.email,
        numero_appel=user.numero_appel,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Inscription réussie"}

# 🔐 Route de connexion
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    restaurateur = db.query(Restaurant).filter(Restaurant.username == user.username).first()
    if not restaurateur or not verify_password(user.password, restaurateur.password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # Création du token d'accès
    token = create_token(restaurateur.username)

    # Retourner l'ID du restaurateur avec le token
    return {"access_token": token, "restaurateur_id": restaurateur.id, "token_type": "bearer"}
