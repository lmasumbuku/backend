from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/commande")
async def recevoir_commande(request: Request):
    body = await request.body()
    print("🧾 Corps brut reçu :", body.decode("utf-8"))  # <- Affiche même si c'est malformé
    try:
        data = await request.json()
        print("✅ JSON bien reçu :", data)
        return {"status": "ok", "recu": data}
    except Exception as e:
        print("❌ Erreur lors du parse JSON :", str(e))
        return {"error": str(e)}
