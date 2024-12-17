# from .demo_table import router as demo_table_router

# backend/app/routers/__init__.py
from fastapi import APIRouter
# from . import export, sentinel, carbon, polygons, vision
from . import export, polygons, satellite

router = APIRouter()

router.include_router(export.router, prefix="/export", tags=["export"])
# router.include_router(sentinel.router, prefix="/sentinel", tags=["sentinel"])
# router.include_router(carbon.router, prefix="/carbon", tags=["carbon"])
router.include_router(polygons.router, prefix="/polygons", tags=["polygons"])
router.include_router(satellite.router, prefix="/satellite", tags=["satellite"])
# router.include_router(vision.router, prefix="/vision", tags=["vision"])
