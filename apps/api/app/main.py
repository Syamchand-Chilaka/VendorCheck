from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import unhandled_exception_handler
from app.routes import checks, documents, me, metrics, reviews, vendors


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB engine is lazily initialized on first request via get_db()
    yield


app = FastAPI(
    title="VendorCheck API",
    version="0.2.0",
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
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
