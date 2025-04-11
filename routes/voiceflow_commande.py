from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/commande")
async def recevoir_commande(request: Request):
    print("✅ Requête reçue")
    try:
        data = await request.json()
        print("✅ Nouvelle commande reçue depuis Voiceflow :", data)
        return {"status": "ok", "recu": data}
    except Exception as e:
        print("❌ Erreur lors de la réception de la commande :", str(e))
        return JSONResponse(status_code=500, content={
            "error": "Erreur serveur",
            "details": str(e)
        })
