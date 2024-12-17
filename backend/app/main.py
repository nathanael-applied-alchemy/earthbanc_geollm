# backend/app/main.py



# https://e4ftl01.cr.usgs.gov//DP109/COMMUNITY/LGRIP30.001/2014.01.01/LGRIP30_2015_N00E30_001_2023014175240.tif?_ga=2.61306988.1710895569.1734132909-1600426111.1734132909


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import app.routers
import os
from dotenv import load_dotenv

# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from geoalchemy2 import Geometry
from shapely.geometry import shape
from datetime import datetime
from app.routers.polygons import router as polygon_router
from app.routers.satellite import router as satellite_router
# Load environment variables from the project's .env
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load environment variables from the project root .env
load_dotenv(PROJECT_ROOT / '.env')

app = FastAPI(
    title="geollm",
    version="0.1.0",
    description="API for geollm",
)

# Get ports from environment
FRONTEND_PORT = os.getenv('FRONTEND_PORT', '3007')
API_PORT = os.getenv('API_PORT', '8007')

# CORS configuration with dynamic ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{FRONTEND_PORT}",
        f"http://localhost:3007",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.post("/api/analyze")
async def analyze_polygon(polygon: dict):
    try:
        # Validate GeoJSON
        geometry = shape(polygon["geometry"])
        area_hectares = geometry.area * 10000  # Example calculation
        return {"area_hectares": area_hectares}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Middleware to add trailing slashes
@app.middleware("http")
async def add_trailing_slash(request: Request, call_next):
    # Don't add trailing slash to API routes
    if request.url.path.startswith("/api/"):
        response = await call_next(request)
        return response
    
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=str(request.url) + "/")
    response = await call_next(request)
    return response

# Include routers
app.include_router(polygon_router, prefix="/api/polygons", tags=["polygons"])
app.include_router(satellite_router, prefix="/api/satellite", tags=["satellite"])

# app.include_router(demo_table_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "app": "geollm",
        "version": "0.1.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }