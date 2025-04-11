from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/commande")
async def recevoir_commande(request: Request):
    print("✅ Requête reçue")
    data = await request.json()
        print("✅ Nouvelle commande reçue depuis Voiceflow :", data)
        return {"status": "ok", "recu": data}
    except Exception as e:
        print("❌ Erreur JSON :", str(e))
        return JSONResponse(status_code=400, content={"error": "Requête invalide", "details": str(e)})
