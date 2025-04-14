from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/commande")
async def recevoir_commande(request: Request):
    body = await request.body()
    print("🧾 Corps brut reçu :", body.decode("utf-8"))  # <- Affiche même si c'est malformé

    try:
        data = await request.json()
        print("✅ JSON bien reçu :", data)

        # 🔧 Nettoyage de la commande
        commande_brute = data.get("commande", "")
        commande_propre = commande_brute.lstrip(", ").strip()  # Supprime virgule et espaces

        print("🍽️ Commande nettoyée :", commande_propre)

        return {"status": "ok", "commande": commande_propre}

    except Exception as e:
        print("❌ Erreur lors du parse JSON :", str(e))
        return {"error": str(e)}
