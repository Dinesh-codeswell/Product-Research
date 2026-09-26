"""PulseRadar FastAPI Application Entrypoint"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
import app.models.entities
import app.models.seo_entities
from app.api.v1.research import router as research_router, settings_router
from app.api.v1.seo import router as seo_router
from app.api.v1.models import router as models_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pulseradar")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PulseRadar database...")
    await init_db()
    logger.info("PulseRadar database initialized successfully.")
    yield
    logger.info("PulseRadar shutting down.")

app = FastAPI(
    title="PulseRadar API",
    description="Autonomous Multi-Channel Product Research & Synthesis Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration (supports localhost, vercel.app, and custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(research_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(seo_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "PulseRadar API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
