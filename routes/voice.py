# routes/voice.py
from __future__ import annotations

import os
import re
import secrets
import unicodedata
from typing import Dict, List, Tuple, Optional
from urllib.parse import unquote_plus

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Restaurant, MenuItem, Order as OrderModel
from schemas import (
    RestaurantInfo,
    VoiceOrderIn,     # payload déjà structuré: items [ {name, quantity, note?}, ...]
    OrderOut,
    OrderLineOut,
)

# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/voice", tags=["voice"])

# -----------------------------------------------------------------------------
# DB session
# -----------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Sécurité par API Key (header x-api-key ou query ?key=)
# -----------------------------------------------------------------------------
VOICE_API_KEY = os.getenv("VOICE_API_KEY", "change-me")

def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    key: Optional[str] = Query(default=None),  # fallback si Voiceflow n'envoie pas le header
):
    expected = VOICE_API_KEY
    provided_raw = x_api_key or key
    if provided_raw is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    # URL-decoder (au cas où)
    provided = unquote_plus(provided_raw).strip()

    # Comparaison sûre
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


# -----------------------------------------------------------------------------
# Utils généraux
# -----------------------------------------------------------------------------
def normalize_number(num: str) -> str:
    """Garde que les chiffres, supprime éventuels 00 initiaux (ex. 0033...)."""
    if not num:
        return ""
    digits = "".join(c for c in str(num) if c.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


# -----------------------------------------------------------------------------
# Endpoints de debug
# -----------------------------------------------------------------------------
@router.get("/ping", dependencies=[Depends(require_api_key)])
def ping():
    return {"ok": True}

@router.get("/debug/headers", dependencies=[Depends(require_api_key)])
def debug_headers(request: Request):
    return {"headers": dict(request.headers)}


# -----------------------------------------------------------------------------
# GET /voice/restaurant/by-number/{called_number}
#   -> infos du resto + menu
# -----------------------------------------------------------------------------
@router.get(
    "/restaurant/by-number/{called_number}",
    response_model=RestaurantInfo,
    dependencies=[Depends(require_api_key)],
)
def get_restaurant_by_number(called_number: str, db: Session = Depends(get_db)):
    num = normalize_number(called_number)

    # Recherche souple (le champ en base s'appelle "numero_appel")
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    match: Optional[Restaurant] = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            match = r
            break

    if not match:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.query(MenuItem).filter(MenuItem.restaurant_id == match.id).all()

    return {
        "id": match.id,
        "nom_restaurant": getattr(match, "nom_restaurant", None),
        "numero_appel": getattr(match, "numero_appel", None),
        "menu": [
            {
                "id": i.id,
                "name": i.name,
                "price": i.price,
                "aliases": getattr(i, "aliases", []) or [],  # si pas de colonne, on renvoie []
            }
            for i in items
        ],
    }


# -----------------------------------------------------------------------------
# POST /voice/order  (crée une commande à partir d'items déjà structurés)
# -----------------------------------------------------------------------------
@router.post(
    "/order",
    response_model=OrderOut,
    dependencies=[Depends(require_api_key)],
)
def create_order_from_voice(payload: VoiceOrderIn, db: Session = Depends(get_db)):
    """
    Crée une commande à partir d'items déjà structurés (name, quantity, note).
    Valide 'name' sur le menu (insensible à la casse).
    """
    num = normalize_number(payload.restaurant_number)

    # Trouver le resto
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    resto: Optional[Restaurant] = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()
    by_name = {i.name.strip().lower(): i for i in menu_items}

    lines: List[OrderLineOut] = []
    total = 0.0
    for it in payload.items:
        key = (it.name or "").strip().lower()
        mi = by_name.get(key)
        if not mi:
            raise HTTPException(status_code=400, detail=f"Item not in menu: {it.name}")
        qty = max(1, int(it.quantity or 1))
        total += mi.price * qty
        lines.append(
            OrderLineOut(name=mi.name, unit_price=mi.price, quantity=qty, note=it.note or "")
        )

    # Stockage compatible: items = ["2 x Margherita", ...]
    items_str = [f"{l.quantity} x {l.name}" for l in lines]
    new_order = OrderModel(
        restaurant_id=resto.id,
        items=items_str,
        status="accepted",
        source="ia",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return OrderOut(
        id=new_order.id,
        restaurant_id=resto.id,
        total=round(total, 2),
        status=new_order.status,
        lines=lines,
    )


# -----------------------------------------------------------------------------
# Parsing d'une phrase libre -> lignes de commande (fuzzy FR)
# -----------------------------------------------------------------------------
# RapidFuzz si dispo (meilleur), sinon fallback difflib
try:
    from rapidfuzz import process, fuzz
    _HAS_RAPIDFUZZ = True
except Exception:
    from difflib import SequenceMatcher
    _HAS_RAPIDFUZZ = False

_FR_NUM_WORDS = {
    "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
    "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10
}
_STOPWORDS = {
    "et", "svp", "s'il", "sil", "te", "plait", "stp", "merci", "je",
    "voudrais", "veux", "prends", "prendre", "donne", "rajoute", "ajoute", "mettre",
}

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _norm(s: str) -> str:
    s = (_strip_accents(s or "")).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _split_chunks(utt: str) -> List[str]:
    tmp = re.sub(r"[,+;/]", " et ", utt, flags=re.I)
    parts = re.split(r"\bet\b", tmp, flags=re.I)
    return [p.strip() for p in parts if p and p.strip()]

def _extract_qty_and_label(chunk: str) -> Tuple[int, str]:
    c = _norm(chunk)
    tokens = [t for t in c.split() if t not in _STOPWORDS]

    qty = 1
    if tokens and re.fullmatch(r"\d{1,3}", tokens[0]):  # nombre
        qty = max(1, int(tokens[0]))
        tokens = tokens[1:]
    elif tokens and tokens[0] in _FR_NUM_WORDS:        # “deux”, “trois”…
        qty = _FR_NUM_WORDS[tokens[0]]
        tokens = tokens[1:]

    label = " ".join(tokens).strip()
    label = re.sub(r"s\b", "", label)  # pizza(s) -> pizza (très basique)
    return qty, label

def _fuzzy_best_match(label: str, candidates: List[str]) -> Tuple[str, float]:
    if not label or not candidates:
        return "", 0.0
    if _HAS_RAPIDFUZZ:
        best, score, _ = process.extractOne(label, candidates, scorer=fuzz.WRatio)
        return best, float(score)
    # fallback difflib
    best = ""
    best_score = 0.0
    for c in candidates:
        s = SequenceMatcher(None, label, c).ratio() * 100.0
        if s > best_score:
            best, best_score = c, s
    return best, best_score

def parse_order_utterance(utterance: str, menu_items: List[MenuItem]) -> List[Dict]:
    """
    -> [{name, unit_price, quantity}]
    """
    chunks = _split_chunks(utterance)
    if not chunks:
        chunks = [utterance]

    idx_map: Dict[str, MenuItem] = {}
    keys: List[str] = []

    for it in menu_items:
        base = _norm(it.name)
        idx_map[base] = it
        keys.append(base)

        for alias in getattr(it, "aliases", []) or []:
            a = _norm(alias)
            idx_map[a] = it
            keys.append(a)

    lines: Dict[int, Dict] = {}  # item_id -> line

    for ch in chunks:
        qty, label = _extract_qty_and_label(ch)
        if not label:
            continue
        best_key, score = _fuzzy_best_match(label, keys)
        if score < 70 or best_key not in idx_map:   # seuil ajustable
            continue

        mi = idx_map[best_key]
        if mi.id in lines:
            lines[mi.id]["quantity"] += qty
        else:
            lines[mi.id] = {
                "name": mi.name,
                "unit_price": float(mi.price),
                "quantity": qty,
            }

    return list(lines.values())


# -----------------------------------------------------------------------------
# POST /voice/order/parse  (NLP + fuzzy + création optionnelle)
# -----------------------------------------------------------------------------
class ParseOrderIn(BaseModel):
    restaurant_number: str
    utterance: str
    create: bool = False  # si True -> crée la commande en base

class ParsedOrderOut(BaseModel):
    lines: List[OrderLineOut]
    total: float
    created_order_id: Optional[int] = None

@router.post(
    "/order/parse",
    response_model=ParsedOrderOut,
    dependencies=[Depends(require_api_key)],
)
def parse_and_optionally_create(payload: ParseOrderIn, db: Session = Depends(get_db)):
    num = normalize_number(payload.restaurant_number)

    # Trouver le resto
    restos = db.query(Restaurant).filter(Restaurant.numero_appel.isnot(None)).all()
    resto: Optional[Restaurant] = None
    for r in restos:
        if normalize_number(getattr(r, "numero_appel", "")) == num:
            resto = r
            break
    if not resto:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == resto.id).all()

    parsed = parse_order_utterance(payload.utterance, menu_items)
    if not parsed:
        return ParsedOrderOut(lines=[], total=0.0, created_order_id=None)

    total = sum(p["unit_price"] * p["quantity"] for p in parsed)
    lines_out = [
        OrderLineOut(name=p["name"], unit_price=p["unit_price"], quantity=p["quantity"], note="")
        for p in parsed
    ]

    created_id: Optional[int] = None
    if payload.create:
        items_str = [f"{l.quantity} x {l.name}" for l in lines_out]
        new_order = OrderModel(
            restaurant_id=resto.id,
            items=items_str,
            status="accepted",
            source="ia",
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        created_id = new_order.id

    return ParsedOrderOut(lines=lines_out, total=round(total, 2), created_order_id=created_id)
