from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict

router = APIRouter()

class Plat(BaseModel):
    nom: str
    quantité: int

class CommandeDetail(BaseModel):
    type: str
    plats: List[Plat]
    instructions: str = ""

class Client(BaseModel):
    nom: str
    canal: str

class CommandeVocale(BaseModel):
    source: str
    client: Client
    commande: CommandeDetail
    horodatage: datetime

@router.post("/api/commande-vocale")
async def recevoir_commande_vocale(data: CommandeVocale):
    print("📞 Commande vocale reçue :", data)
    # TODO : ici tu peux enregistrer en BDD ou déclencher une notification
    return {"status": "success", "message": "Commande vocale enregistrée"}
