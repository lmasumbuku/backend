from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order

router = APIRouter(prefix="/voiceflow-commande")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
async def creer_commande_ia(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        commande = data.get("commande", "")
        restaurant_id = data.get("restaurant_id")

        if not restaurant_id:
            return {"error": "restaurant_id manquant"}

        commande_propre = commande.lstrip(", ").strip()

        new_order = Order(
            restaurant_id=restaurant_id,
            items=commande_propre,
            status="accepted"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        print(f"✅ Commande IA enregistrée : {commande_propre} pour restaurant {restaurant_id}")

        return {"message": "Commande IA enregistrée ✅", "order_id": new_order.id}

    except Exception as e:
        return {"error": f"Erreur lors de l'enregistrement : {str(e)}"}
