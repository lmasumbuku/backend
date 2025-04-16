from pydantic import BaseModel, EmailStr
from typing import Optional

# ✅ Ce modèle représente ce que le frontend envoie pour s’inscrire
class RestaurantCreate(BaseModel):
    name: str
    legal_representative: str
    address: str
    email: EmailStr
    call_number: str
    username: str
    password: str

# ✅ Ce modèle représente les champs modifiables
class RestaurantUpdate(BaseModel):
    name: Optional[str]
    legal_representative: Optional[str]
    address: Optional[str]
    email: Optional[EmailStr]
    call_number: Optional[str]

# ✅ Ce modèle représente la réponse envoyée vers le frontend
class RestaurantOut(BaseModel):
    id: int
    name: str
    legal_representative: str
    address: str
    email: EmailStr
    call_number: str

    class Config:
        orm_mode = True
