"""
Vercel Python Serverless Function Entry Point.
This file wraps the FastAPI app for deployment on Vercel.
"""
import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Override DATABASE_URL to use SQLite in /tmp (writable on Vercel)
# For production, set DATABASE_URL env var in Vercel dashboard to a real Postgres URL
if not os.environ.get("DATABASE_URL") or "mysql" in os.environ.get("DATABASE_URL", ""):
    _db_path = "/tmp/oraldysplasia.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"

# Override upload dir to /tmp (writable on Vercel)
if not os.environ.get("UPLOAD_DIR"):
    os.environ["UPLOAD_DIR"] = "/tmp/uploads"

from app.main import app  # noqa: E402 — import after env setup
