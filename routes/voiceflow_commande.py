from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel
from routes.auth import decode_token

router = APIRouter()

print("✅ voiceflow_commande.py bien chargé")

# Fonction d'accès à la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
async def recevoir_commande(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        commande_brute = data.get("commande", "")
        restaurant_id = data.get("restaurant_id")

        if not restaurant_id:
            return {"error": "restaurant_id manquant"}

        commande_propre = commande_brute.lstrip(", ").strip()

        # ✅ Enregistrement dans la base
        new_order = OrderModel(
            restaurant_id=restaurant_id,
            items=commande_propre,
            status="accepted"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        print("✅ Commande IA insérée :", commande_propre)
        return {"status": "ok", "commande": commande_propre, "order_id": new_order.id}

    except Exception as e:
        print("❌ Erreur JSON :", str(e))
        return {"error": str(e)}
