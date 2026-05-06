import sys
from pathlib import Path

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.auth.routes import router as auth_router
from backend.dashboard import router as dashboard_router
from backend.database import engine, Base
from backend.equipment import router as equipment_router
from backend.threats import router as threats_router
from backend.troops import router as troops_router
from backend.users.routes import router as users_router

app = FastAPI(title="Full Stack API")

logger = logging.getLogger(__name__)


@app.on_event("startup")
def initialize_database():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as error:
        logger.error("Database initialization failed during startup: %s", error)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(threats_router, prefix="/api")
app.include_router(troops_router, prefix="/api")
app.include_router(equipment_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "API is running"}
