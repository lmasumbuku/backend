from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import List

# ✅ Modèle SQLAlchemy pour la base de données
class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    menu_items = relationship("MenuItem", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    items = Column(String)  # Liste des plats sous forme de texte
    status = Column(String, default="pending")  # pending, accepted, rejected
    restaurant = relationship("Restaurant", back_populates="orders")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Integer)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    restaurant = relationship("Restaurant", back_populates="menu_items")

# ✅ Modèles Pydantic pour FastAPI
class OrderCreate(BaseModel):
    items: List[str]

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    items: List[str]
    status: str

    class Config:
        from_attributes = True

class MenuItemCreate(BaseModel):
    name: str
    price: float

class MenuItemResponse(BaseModel):
    id: int
    name: str
    price: float
    restaurant_id: int

    class Config:
        from_attributes = True  # ✅ Pydantic V2
