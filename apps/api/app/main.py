from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from app.config import get_settings
from app.errors import unhandled_exception_handler
from app.routes import checks, me


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.supabase = create_client(
        settings.supabase_url, settings.supabase_service_role_key)
    yield


app = FastAPI(
    title="VendorCheck API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Catch-all for unhandled exceptions
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routes
app.include_router(me.router, prefix="/api/v1")
app.include_router(checks.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
