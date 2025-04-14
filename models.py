from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from typing import List, Optional

Base = declarative_base()

# 🔸 Modèle SQLAlchemy : Restaurant
class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    # ✅ Infos supplémentaires du restaurateur
    nom_restaurant = Column(String, nullable=True)
    nom_representant = Column(String, nullable=True)
    prenom_representant = Column(String, nullable=True)
    adresse_postale = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    numero_appel = Column(String, unique=True, nullable=True)

    orders = relationship("Order", back_populates="restaurant")
    menu_items = relationship("MenuItem", back_populates="restaurant")

# 🔸 Modèle SQLAlchemy : Order
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    items = Column(String)  # items séparés par des virgules
    status = Column(String, default="pending")

    restaurant = relationship("Restaurant", back_populates="orders")

# 🔸 Modèle SQLAlchemy : MenuItem
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))

    restaurant = relationship("Restaurant", back_populates="menu_items")

# ──────────────── Pydantic Schemas ────────────────

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

class RestaurantUpdate(RestaurantBase):
    pass

class RestaurantResponse(BaseModel):
    id: int
    username: str
    nom_restaurant: Optional[str]
    nom_representant: Optional[str]
    prenom_representant: Optional[str]
    adresse_postale: Optional[str]
    email: Optional[EmailStr]
    numero_appel: Optional[str]

    class Config:
        orm_mode = True
