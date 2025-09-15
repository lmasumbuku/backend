from pydantic import BaseModel, EmailStr
from typing import List, Optional

# 🔹 MenuItem
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
    password: str  # Le mot de passe est inclus ici pour la création et l'authentification
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
    items: List[str]  # Liste des éléments dans la commande
    source: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    items: List[str]  # Liste des éléments dans la commande
    status: str
    source: str

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

# 🔹 Authentification
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UpdatePhoneNumber(BaseModel):
    numero_appel: str

# --- AJOUTS POUR L'API /voice ---

from typing import Any, Dict  # <- ajouter en haut si pas présent

# ✅ Réponse menu avec alias pour la reco vocale
class MenuItemOut(BaseModel):
    id: int
    name: str
    price: float
    aliases: Optional[List[str]] = []

    class Config:
        from_attributes = True

# ✅ Infos restaurant pour le lookup par numéro appelé
class RestaurantInfo(BaseModel):
    id: int
    # on garde la cohérence avec tes noms actuels
    nom_restaurant: Optional[str]
    numero_appel: Optional[str]
    # le backend remplira aussi call_number si tu l'ajoutes plus tard
    menu: List[MenuItemOut]

# ✅ Élément structuré du panier envoyé par le bot
class BasketItem(BaseModel):
    name: str
    quantity: int
    note: Optional[str] = None

# ✅ Payload standardisé pour créer une commande depuis le bot vocal
class VoiceOrderIn(BaseModel):
    restaurant_number: str              # numéro appelé (format libre, on normalise côté backend)
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    items: List[BasketItem]             # liste structurée (nom, quantité, note)
    channel: str = "voice"
    meta: Optional[Dict[str, Any]] = {} # ex: {"callSid": "CA..."} pour l'idempotence

# ✅ Sortie "jolie" d'une commande (même si ta DB n'a pas encore OrderLine)
class OrderLineOut(BaseModel):
    name: str
    unit_price: float
    quantity: int
    note: str = ""

class OrderOut(BaseModel):
    id: int
    restaurant_id: int
    total: float
    status: str
    lines: List[OrderLineOut]

    class Config:
        from_attributes = True
