"""
FastAPI Backend - Main Application

Production-ready REST API serving Barcelona Housing data from SQLite.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from api.routers import barrios, demographics, housing
from api.database import verify_database_exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Barcelona Housing Demographics API",
    description="REST API serving housing and demographic data for Barcelona",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration - Allow React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(barrios.router, prefix="/api", tags=["Barrios"])
app.include_router(demographics.router, prefix="/api", tags=["Demographics"])
app.include_router(housing.router, prefix="/api", tags=["Housing"])


@app.on_event("startup")
async def startup_event():
    """Verify database exists on startup"""
    logger.info("Starting Barcelona Housing Demographics API...")
    verify_database_exists()
    logger.info("API ready to serve requests")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Barcelona Housing API"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Barcelona Housing Demographics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
