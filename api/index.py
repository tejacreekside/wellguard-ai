from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app as backend_app  # noqa: E402


app = FastAPI(title="WellGuard AI Vercel Gateway")
app.mount("/api", backend_app)
app.mount("/", backend_app)
