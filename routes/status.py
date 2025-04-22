from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(tags=["Status"])

@router.get("/status")
def check_database_connection(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "OK ✅", "message": "Connexion à la base de données réussie"}
    except Exception as e:
        return {"status": "ERROR ❌", "message": f"Erreur de connexion : {str(e)}"}
