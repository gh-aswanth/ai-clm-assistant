import asyncio
import logging
import os

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Load backend/.env so all service credentials are available at startup
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router as api_router
from app.api.ws_graph_chat import router as ws_graph_chat_router
from app.api.ws_notifications import router as ws_notifications_router
from app.api.guidelines import router as guidelines_router
from app.api.docx_editor import router as docx_editor_router
from app.api.auth import router as auth_router, seed_default_admin
from app.db.database import engine, Base, SessionLocal
from app.models import models  # import models so metadata is fully loaded

app = FastAPI(title="CLM System API")


@app.on_event("startup")
def ensure_database_schema() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()


@app.on_event("startup")
async def capture_event_loop() -> None:
    from app.services.notifier import notifier
    notifier.set_loop(asyncio.get_running_loop())

# Serve LLM result viewer (notebook folder) at /viewer
_notebook_dir = Path(__file__).resolve().parents[2] / "notebook"
if _notebook_dir.exists():
    app.mount("/viewer", StaticFiles(directory=str(_notebook_dir), html=True), name="viewer")



# Configure CORS — origins read from CORS_ALLOWED_ORIGINS env var (comma-separated)
_cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(guidelines_router, prefix="/api")
app.include_router(docx_editor_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(ws_graph_chat_router, prefix="/ws")
app.include_router(ws_notifications_router, prefix="/ws")

# Serve compiled frontend from frontend/dist
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.exists():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(_frontend_dist / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        candidate = _frontend_dist / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_frontend_dist / "index.html"))

    @app.exception_handler(404)
    async def spa_404_handler(request: Request, exc):
        if request.url.path.startswith("/api") or request.url.path.startswith("/ws"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(str(_frontend_dist / "index.html"))
