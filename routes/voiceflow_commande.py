from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order as OrderModel
from routes.auth import decode_token
from models import Restaurant

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
        numero_appel = data.get("restaurant_id")

        if not numero_appel:
            return {"error": "Le numéro d'appel est manquant."}
            
            # Recherche du restaurant correspondant au numéro d'appel
        restaurant = db.query(Restaurant).filter(Restaurant.numero_appel == numero_appel).first()

        if not restaurant:
            return {"error": f"Aucun restaurant trouvé avec le numéro {numero_appel}"}

        commande_propre = commande_brute.lstrip(", ").strip()

        # ✅ Enregistrement dans la base
        new_order = OrderModel(
            restaurant_id=restaurant_id,
            items=commande_propre,
            status="accepted",
            source="ia"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        print("✅ Commande IA insérée pour le restaurant {restaurant.nom_restaurant} :", commande_propre)
        return {"status": "ok", "commande": commande_propre, "order_id": new_order.id}

    except Exception as e:
        print("❌ Erreur JSON :", str(e))
        return {"error": str(e)}
