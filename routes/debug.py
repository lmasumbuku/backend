from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/debug/drop-menu-items")
def drop_menu_items(db: Session = Depends(get_db)):
    db.execute("DROP TABLE IF EXISTS menu_items CASCADE")
    db.commit()
    return {"message": "✅ Table menu_items supprimée"}
