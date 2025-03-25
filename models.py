from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

# 🔸 Modèle SQLAlchemy : Restaurant
class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

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

# Restaurant
class RestaurantCreate(BaseModel):
    username: str
    password: str

class RestaurantResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

# Order
class OrderCreate(BaseModel):
    restaurant_id: int
    items: List[str]

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    items: List[str]
    status: str

    class Config:
        orm_mode = True

# MenuItem
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str]
    price: float

class MenuItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]

class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    restaurant_id: int

    class Config:
        orm_mode = True
