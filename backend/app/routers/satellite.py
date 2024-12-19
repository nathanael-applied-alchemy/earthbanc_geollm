from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from pathlib import Path
import os
import traceback
import asyncio
import logging
from app.services.satellite import process_spectral_band, task_statuses

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"

class PolygonRequest(BaseModel):
    polygon_geojson: dict

router = APIRouter()

@router.post("/retrieve-satellite-image")
async def retrieve_satellite_image(request: PolygonRequest):
    # try:
        # Create tasks for each spectral band
    spectral_tasks = [
        process_spectral_band(request.polygon_geojson, 'TrueColor'),
        process_spectral_band(request.polygon_geojson, 'NDWI'),
        process_spectral_band(request.polygon_geojson, 'AgriColor'),
        process_spectral_band(request.polygon_geojson, 'MSAVI2')
    ]
    
    # Process all spectral bands concurrently
    png_files = await asyncio.gather(*spectral_tasks, return_exceptions=True)
    
    # Filter out any errors and collect successful results
    successful_files = [f for f in png_files if isinstance(f, str) and f is not None]
    
    if successful_files:
        return {"message": "Satellite images retrieved successfully", "files": successful_files}
    else:
        raise HTTPException(status_code=500, detail="Failed to retrieve satellite images")
    # except Exception as e:
    #     logger.error(f"Error retrieving satellite images: {str(e)}")
    #     logger.error(f"Traceback: {traceback.format_exc()}")
    #     raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-status")
async def get_task_status():
    return task_statuses

@router.get("/get-image/{image_name}")
async def get_saved_satellite_image(image_name: str):
    """Get or create and serve the raster preview image"""
    try:
        image_dir = DATA_DIR / "saved_images"
        png_path = image_dir / f"{image_name}.png"
        
        if not png_path.exists():
            raise HTTPException(status_code=404, detail="Raster PNG not found")
        
        return Response(
            content=png_path.read_bytes(),
            media_type="image/png"
        )
        
    except Exception as e:
        logger.error(f"Error serving raster preview: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
