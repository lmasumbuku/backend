from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # Le mot de passe est stocké en texte haché
    nom_restaurant = Column(String, nullable=True)
    nom_representant = Column(String, nullable=True)
    prenom_representant = Column(String, nullable=True)
    adresse_postale = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    numero_appel = Column(String, unique=True, nullable=True)

    orders = relationship("Order", back_populates="restaurant")
    menu_items = relationship("MenuItem", back_populates="restaurant")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    items = Column(String)  # Assurer que cette colonne existe et contient les éléments de la commande
    status = Column(String, default="pending")

    restaurant = relationship("Restaurant", back_populates="orders")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))

    restaurant = relationship("Restaurant", back_populates="menu_items")
