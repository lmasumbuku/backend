from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import Restaurant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "SECRET"  # Change-le plus tard
ALGORITHM = "HS256"

def decode_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Restaurant:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        user = db.query(Restaurant).filter(Restaurant.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Échec de la validation du token")
