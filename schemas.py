from pydantic import BaseModel, EmailStr
from typing import List, Optional

class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    restaurant_id: int

    class Config:
        from_attributes = True

# 🔹 Restaurant
class RestaurantBase(BaseModel):
    username: str
    password: str
    nom_restaurant: Optional[str]
    nom_representant: Optional[str]
    prenom_representant: Optional[str]
    adresse_postale: Optional[str]
    email: Optional[EmailStr]
    numero_appel: Optional[str]

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]
    nom_restaurant: Optional[str]
    nom_representant: Optional[str]
    prenom_representant: Optional[str]
    adresse_postale: Optional[str]
    email: Optional[EmailStr]
    numero_appel: Optional[str]

class RestaurantResponse(BaseModel):
    id: int
    username: str
    nom_restaurant: Optional[str]
    nom_representant: Optional[str]
    prenom_representant: Optional[str]
    adresse_postale: Optional[str]
    email: Optional[EmailStr]
    numero_appel: Optional[str]

class RestaurantOut(BaseModel):
    id: int
    username: str
    nom_restaurant: Optional[str]
    nom_representant: Optional[str]
    prenom_representant: Optional[str]
    adresse_postale: Optional[str]
    email: Optional[EmailStr]
    numero_appel: Optional[str]
    menu_items: List[MenuItemResponse] = []
    
    class Config:
        from_attributes = True


# 🔹 Order
class OrderCreate(BaseModel):
    restaurant_id: int
    items: List[str]

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    items: List[str]
    status: str

    class Config:
        from_attributes = True

# 🔹 MenuItem
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str]
    price: float

class MenuItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]

    class Config:
        from_attributes = True
