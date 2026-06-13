"""OralDysplasia AI — FastAPI Application Entry Point."""

import os
import sys
import asyncio
from contextlib import asynccontextmanager

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, DB_STATUS
from app.routers import auth, slides, analysis, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup (dev convenience)."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if DB_STATUS == "sqlite_fallback":
        print("=" * 80)
        print("  [WARNING] ORAL DYSPLASIA BACKEND DETECTED XAMPP MYSQL OFFLINE!")
        print("  Falling back to SQLite database at: backend/oraldysplasia.db")
        print("  Data created in this mode will NOT sync with your MySQL database!")
        print("=" * 80)
    else:
        print(f"[OK] {settings.PROJECT_NAME} backend ready - connected to {DB_STATUS.upper()}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Secure Medical AI platform for Oral Epithelial Dysplasia grading",
    version="2.1.0",
    lifespan=lifespan,
)

# CORS — allow Android emulator and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(slides.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "database_status": DB_STATUS
    }


from fastapi.staticfiles import StaticFiles

# Locate the web/ directory — works both locally and on Vercel
_this_file   = os.path.abspath(__file__)                  # .../app/main.py
_app_dir     = os.path.dirname(_this_file)                # .../app/
_backend_dir = os.path.dirname(_app_dir)                  # .../backend/  OR  .../app/ on Vercel
_project_dir = os.path.dirname(_backend_dir)              # project root

# Try each candidate in order
_web_candidates = [
    os.path.join(_project_dir, "web"),   # local: oral-dysplasia-ai/web
    os.path.join(_backend_dir, "web"),   # fallback: backend/web
    os.path.join(_app_dir, "..", "..", "web"),  # Vercel: api/../web
]
frontend_dir = next((p for p in _web_candidates if os.path.isdir(p)), None)

if frontend_dir:
    os.makedirs(frontend_dir, exist_ok=True)
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
else:
    print("[WARN] web/ directory not found — static files will not be served.")
