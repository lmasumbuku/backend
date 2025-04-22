# config.py

import os
from dotenv import load_dotenv

# ✅ Charge les variables depuis un fichier .env si présent
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-par-defaut")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours
