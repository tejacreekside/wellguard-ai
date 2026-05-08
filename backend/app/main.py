from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.services.persistence_service import persistence_service


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="AI-native operational intelligence for oil and gas production surveillance.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)

if settings.api_prefix.rstrip("/") != "/api":
    app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    persistence_service.init_db()
