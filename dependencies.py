from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from models import Restaurant
from app.core.database import get_db
from app.utils.utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_restaurant(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Restaurant:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou manquant",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        restaurant_id: int = payload.get("sub")
        if restaurant_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if restaurant is None:
        raise credentials_exception
    return restaurant
