# backend/app/routers/polygons.py
from fastapi import APIRouter, Depends, HTTPException, Response, Body
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from typing import List, Dict, Any
from datetime import datetime
import logging
import json
import traceback
from shapely.geometry import mapping  # Add this import
import math
from pathlib import Path
from ..core.config import settings
from app.models.polygon import AnalysisPolygon

from sqlalchemy import create_engine, text
# from app.core.config import settings
from app.database import engine

from shapely.wkt import loads as wkt_loads

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.plot import reshape_as_image
from PIL import Image
import io

from app.database import get_db
from app.models.polygon import AnalysisPolygon
from app.schemas.polygon import PolygonCreate, PolygonResponse
from app.services import sentinel, vision, carbon
from app.services.file_manager import LGRIPFileManager
from app.services.raster_analysis import RasterAnalyzer
from shapely.ops import unary_union, polygonize
from shapely.validation import explain_validity
from sqlalchemy.sql import func
from sqlalchemy import text
from shapely.geometry import mapping, shape
from shapely.wkt import loads as wkt_loads
from pathlib import Path
from ..core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

import os
import uuid

# Update DATA_DIR to use absolute path
DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data"
# This will resolve to backend/app/data/


# Load LGRIP30 tile reference
with open('app/data/LGRIP30_v001_tiles.json', 'r') as f:
    TILE_REFERENCE = json.load(f)


@router.post("/", response_model=PolygonResponse)
async def create_polygon(
    polygon: PolygonCreate,
    db: Session = Depends(get_db)
):
    """Create a new polygon"""
    name = polygon.name
    geometry = polygon.geometry
    session_id = polygon.session_id
    
    logger.info(f"Creating polygon with name: {name}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Geometry: {geometry}")
    
    try:
        # Convert GeoJSON to Shapely geometry
        geom = shape(geometry)
        
        # Handle MultiPolygon case
        if geom.geom_type == 'MultiPolygon':
            # Get the largest polygon from the MultiPolygon
            largest_polygon = max(geom.geoms, key=lambda x: x.area)
            geom = largest_polygon
        elif geom.geom_type != 'Polygon':
            raise ValueError(f"Unsupported geometry type: {geom.geom_type}")
        
        # Ensure the geometry is valid
        if not geom.is_valid:
            geom = make_valid(geom)
            if geom.geom_type != 'Polygon':
                if geom.geom_type == 'MultiPolygon':
                    geom = max(geom.geoms, key=lambda x: x.area)
                else:
                    raise ValueError(f"Could not convert to valid Polygon, got {geom.geom_type}")
        
        db_polygon = AnalysisPolygon(
            name=name,
            geometry=from_shape(geom, srid=4326),
            session_id=session_id
        )
        
        db.add(db_polygon)
        db.commit()
        db.refresh(db_polygon)
        
        # Convert WKB back to GeoJSON for response
        response_data = {
            **db_polygon.__dict__,
            'geometry': json.loads(db.scalar(db_polygon.geometry.ST_AsGeoJSON()))
        }
        
        logger.info(f"Successfully created polygon with ID: {db_polygon.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error creating polygon: {str(e)}")
        logger.exception(e)  # This will log the full traceback
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating polygon: {str(e)}"
        )
    
@router.get("/{polygon_id}", response_model=PolygonResponse)
async def get_polygon(polygon_id: int, db: Session = Depends(get_db)):
    """Get polygon by ID"""
    polygon = db.query(AnalysisPolygon).filter(AnalysisPolygon.id == polygon_id).first()
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")
# Ensure metadata exists
    if not hasattr(polygon, 'analysis_metadata'):
        polygon.analysis_metadata = {}
        
    return PolygonResponse.from_orm(polygon)
    
@router.post("/{polygon_id}/analyze")
async def analyze_polygon(polygon_id: int, db: Session = Depends(get_db)):
    """Analyze a polygon's area for cropland and other features"""
    try:
        polygon = db.query(AnalysisPolygon).filter(AnalysisPolygon.id == polygon_id).first()
        if not polygon:
            raise HTTPException(status_code=404, detail="Polygon not found")

        # Convert GeoAlchemy geometry to dict/GeoJSON
        geom_dict = db.scalar(func.ST_AsGeoJSON(polygon.geometry))
        if not geom_dict:
            raise HTTPException(status_code=400, detail="Invalid geometry")
            
        # Parse the GeoJSON string to dict
        geom_dict = json.loads(geom_dict)
        
        # Create Shapely geometry
        geom = shape(geom_dict)
        logger.info(f"Geometry type: {geom.geom_type}")
        logger.info(f"Is valid: {geom.is_valid}")

        if not geom.is_valid:
            logger.error(f"Geometry validation issue: {explain_validity(geom)}")
            try:
                # Try to fix the geometry
                fixed = make_valid(geom)
                if fixed.geom_type != 'Polygon':
                    # If we get a MultiPolygon, take the largest polygon
                    if fixed.geom_type == 'MultiPolygon':
                        fixed = max(fixed.geoms, key=lambda x: x.area)
                    # If we get a GeometryCollection, extract polygons and take the largest
                    elif fixed.geom_type == 'GeometryCollection':
                        polygons = [g for g in fixed.geoms if g.geom_type in ('Polygon', 'MultiPolygon')]
                        if not polygons:
                            raise ValueError("No valid polygons in geometry collection")
                        fixed = max(polygons, key=lambda x: x.area)
                        if fixed.geom_type == 'MultiPolygon':
                            fixed = max(fixed.geoms, key=lambda x: x.area)

                if fixed.geom_type != 'Polygon':
                    raise ValueError(f"Could not convert to Polygon, got {fixed.geom_type}")

                geom = fixed
                logger.info(f"Successfully fixed geometry. New type: {geom.geom_type}")
                
                # Update the polygon with fixed geometry using proper SQL casting
                polygon.geometry = db.scalar(func.ST_GeomFromText(geom.wkt, 4326))
                
            except Exception as e:
                logger.error(f"Failed to fix geometry: {str(e)}")
                raise HTTPException(
                    status_code=400, 
                    detail="Could not fix invalid geometry. Please redraw the polygon."
                )

        logger.info(f"Is simple: {geom.is_simple}")
        logger.info(f"Bounds: {geom.bounds}")
        logger.info(f"Area: {geom.area}")

        # Continue with the rest of the analysis...

        # Find required tiles
        try:
            bounds = geom.bounds
            logger.info(f"Finding tiles for bounds: {bounds}")
            
            # Debug: Check if bounds make sense
            if bounds[0] < -180 or bounds[2] > 180 or bounds[1] < -90 or bounds[3] > 90:
                logger.warning(f"Suspicious bounds for polygon {polygon_id}: {bounds}")
            
            required_tiles = []
            for tile_id, tile_info in TILE_REFERENCE['tiles'].items():
                tile_bounds = tile_info['bounds']
                if (bounds[0] < tile_bounds['maxx'] and bounds[2] > tile_bounds['minx'] and
                    bounds[1] < tile_bounds['maxy'] and bounds[3] > tile_bounds['miny']):
                    required_tiles.append((tile_id, tile_info))
            
            logger.info(f"Found {len(required_tiles)} required tiles")
            if not required_tiles:
                logger.error("No tiles found for polygon bounds!")
                raise HTTPException(status_code=400, detail="No data available for this area")
                
        except Exception as e:
            logger.error(f"Error finding tiles: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error finding tiles: {str(e)}")

        # Store masked datasets for merging
        masked_datasets = []
        results = []
        missing_tiles = []
        file_manager = LGRIPFileManager()
        
        # Process tiles with proper masking
        for tile_id, tile_info in required_tiles:
            try:
                file_path, status = await file_manager.get_file_path(tile_info)
                if file_path:
                    with rasterio.open(file_path) as src:
                        # Get center latitude for area calculation
                        bounds = geom.bounds
                        center_lat = (bounds[1] + bounds[3]) / 2
                        
                        # Mask with proper nodata handling
                        masked_data, out_transform = mask(
                            src, 
                            [mapping(geom)], 
                            crop=True, 
                            all_touched=True,
                            nodata=src.nodata
                        )
                        
                        # Store masked dataset for merging
                        masked_datasets.append({
                            'data': masked_data[0],
                            'transform': out_transform,
                            'nodata': src.nodata,
                            'crs': src.crs
                        })
                        
                        # Calculate areas
                        pixel_area = calculate_pixel_area(center_lat)
                        data = masked_data[0]
                        
                        areas = {
                            'no_data': np.sum(data == src.nodata) * pixel_area,
                            1: np.sum(data == 1) * pixel_area,
                            2: np.sum(data == 2) * pixel_area,
                            3: np.sum(data == 3) * pixel_area
                        }
                        
                        results.append({
                            'areas': areas,
                            'total_pixels': data.size,
                            'valid_pixels': np.sum(data != src.nodata)
                        })
                        
            except Exception as e:
                logger.error(f"Error processing tile {tile_id}: {str(e)}")
                missing_tiles.append(tile_id)

        # Merge masked rasters if we have data
        if masked_datasets:
            polygon_dir = DATA_DIR / str(polygon_id)
            polygon_dir.mkdir(exist_ok=True)
            masked_path = polygon_dir / f"masked_raster_{polygon_id}.tif"

            # Create temporary rasters for merging
            temp_rasters = []
            src_files_to_mosaic = []
            
            try:
                # Get the bounds of all datasets to determine output size
                bounds = None
                for dataset in masked_datasets:
                    if bounds is None:
                        bounds = rasterio.transform.array_bounds(
                            dataset['data'].shape[0],
                            dataset['data'].shape[1],
                            dataset['transform']
                        )
                    else:
                        dataset_bounds = rasterio.transform.array_bounds(
                            dataset['data'].shape[0],
                            dataset['data'].shape[1],
                            dataset['transform']
                        )
                        bounds = (
                            min(bounds[0], dataset_bounds[0]),
                            min(bounds[1], dataset_bounds[1]),
                            max(bounds[2], dataset_bounds[2]),
                            max(bounds[3], dataset_bounds[3])
                        )

                # Calculate appropriate resolution
                res = 0.000277778  # Standard 30m resolution at equator
                
                for idx, dataset in enumerate(masked_datasets):
                    temp_path = polygon_dir / f"temp_{idx}.tif"
                    profile = {
                        'driver': 'GTiff',
                        'dtype': dataset['data'].dtype,
                        'nodata': dataset['nodata'],
                        'width': dataset['data'].shape[1],
                        'height': dataset['data'].shape[0],
                        'count': 1,
                        'crs': dataset['crs'],
                        'transform': dataset['transform'],
                        'compress': 'lzw'  # Add compression
                    }
                    
                    with rasterio.open(temp_path, 'w', **profile) as tmp:
                        tmp.write(dataset['data'], 1)
                    temp_rasters.append(temp_path)
                    src = rasterio.open(temp_path)
                    src_files_to_mosaic.append(src)

                # Merge rasters with consistent resolution
                mosaic, out_transform = merge(
                    src_files_to_mosaic,
                    res=(res, res),  # Specify resolution
                    method='first',  # Use first non-null value
                    nodata=src_files_to_mosaic[0].nodata
                )
                
                # Write merged raster with compression
                out_profile = src_files_to_mosaic[0].profile.copy()
                out_profile.update({
                    'height': mosaic.shape[1],
                    'width': mosaic.shape[2],
                    'transform': out_transform,
                    'compress': 'lzw',  # Add compression
                    'predictor': 2,     # Add prediction for better compression
                    'tiled': True       # Enable tiling
                })

                with rasterio.open(masked_path, 'w', **out_profile) as dst:
                    dst.write(mosaic)

            finally:
                # Clean up
                for src in src_files_to_mosaic:
                    src.close()
                for temp_path in temp_rasters:
                    if temp_path.exists():
                        temp_path.unlink()

        # Convert numpy types to Python native types
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        # Combine results properly
        total_areas = {
            0: 0,  # Ocean/Water bodies/No data
            1: 0,  # Non-croplands
            2: 0,  # Irrigated croplands
            3: 0   # Rainfed croplands
        }

        total_pixels = 0
        valid_pixels = 0
        
        for result in results:
            for key, area in result['areas'].items():
                # Map 'no_data' to 0 and keep other values as is
                mapped_key = 0 if key == 'no_data' else key
                total_areas[mapped_key] += float(area)
            total_pixels += int(result['total_pixels'])
            valid_pixels += int(result['valid_pixels'])            

        # Calculate total valid area (excluding ocean/water/no data)
        total_valid_area = float(sum(v for k, v in total_areas.items() if k != 0))
        
        # Updated key map with proper descriptions
        key_map = {
            0: 'Ocean and Water bodies',
            1: 'Non-croplands',
            2: 'Irrigated croplands',
            3: 'Rainfed croplands'
        }

        formatted_results = {
            'areas': {
                key_map[k]: {
                    'area_m2': float(v),
                    'area_ha': float(v / 10000),
                    'area_km2': float(v / 1000000),
                    'area_acres': float(v / 4046.86),
                    'area_sq_mile': float(v / 2589988.11),
                    'percentage': float(v / total_valid_area * 100) if k != 0 else 0.0
                }
                for k, v in total_areas.items()
            },
            'total_area_km2': float(total_valid_area / 1000000),
            'total_area_sq_mile': float(total_valid_area / 2589988.11),
            'total_pixels': int(total_pixels),
            'valid_pixels': int(valid_pixels)
        }
        
        # Update database
        polygon.cropland_data = formatted_results
        db.commit()

        return {"status": "success", "message": "Analysis complete"}
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PolygonResponse])
async def get_polygons(db: Session = Depends(get_db)):
    """Get all polygons"""
    polygons = db.query(AnalysisPolygon).all()
    return [PolygonResponse.from_orm(polygon) for polygon in polygons]

def calculate_pixel_area(latitude_deg, pixel_size_deg=0.000277778):
    """Calculate accurate pixel area accounting for latitude"""
    R = 6371000  # Earth's radius in meters
    lat = math.radians(latitude_deg)
    width = R * math.cos(lat) * math.radians(pixel_size_deg)
    height = R * math.radians(pixel_size_deg)
    return width * height

def make_valid(geom):
    """
    Make a geometry valid using multiple strategies.
    Returns a valid Shapely geometry.
    """
    # First try buffer(0)
    try:
        fixed = geom.buffer(0)
        if fixed.is_valid and fixed.geom_type == 'Polygon':
            return fixed
    except Exception:
        pass

    # If buffer(0) fails or produces wrong type, try ST_MakeValid
    try:
        # Convert to WKT
        wkt = geom.wkt
        
        # Create a database connection
        # engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
        with engine.connect() as connection:
            # Use PostGIS ST_MakeValid
            result = connection.execute(
                text("SELECT ST_AsText(ST_MakeValid(:geom));"),
                {"geom": wkt}
            ).scalar()
            
            if result:
                fixed = wkt_loads(result)
                return fixed
    except Exception as e:
        logger.error(f"ST_MakeValid failed: {str(e)}")
        raise

    raise ValueError("Could not make geometry valid")

# Create data directory if it doesn't exist
DATA_DIR = Path(settings.DATA_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/{polygon_id}/results")
async def get_polygon_results(polygon_id: int, db: Session = Depends(get_db)):
    """Get all analysis results and file paths for a polygon"""
    polygon = db.query(AnalysisPolygon).filter(AnalysisPolygon.id == polygon_id).first()
    if not polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")

    # Get file paths
    polygon_dir = DATA_DIR / str(polygon_id)
    results = {
        "id": polygon_id,
        "name": polygon.name,
        "geometry": json.loads(db.scalar(func.ST_AsGeoJSON(polygon.geometry))),
        "cropland_data": polygon.cropland_data,
        "files": {
            "geojson": f"/api/polygons/{polygon_id}/export/geojson",
            "kml": f"/api/polygons/{polygon_id}/export/kml",
            "masked_raster": f"/api/polygons/{polygon_id}/raster",
        }
    }
    
    return results

@router.get("/{polygon_id}/export/{format}")
async def export_polygon(
    polygon_id: int, 
    format: str, 
    db: Session = Depends(get_db)
):
    """Export polygon in specified format"""
    try:
        logger.info(f"Exporting polygon {polygon_id} in {format} format")
        
        polygon = db.query(AnalysisPolygon).filter(AnalysisPolygon.id == polygon_id).first()
        if not polygon:
            logger.error(f"Polygon {polygon_id} not found")
            raise HTTPException(status_code=404, detail="Polygon not found")

        # Get GeoJSON representation of the geometry
        geojson = json.loads(db.scalar(func.ST_AsGeoJSON(polygon.geometry)))
        
        if format == "geojson":
            feature = {
                "type": "Feature",
                "properties": {
                    "name": polygon.name,
                    "id": polygon.id,
                    "cropland_data": polygon.cropland_data
                },
                "geometry": geojson
            }
            logger.info(f"Returning GeoJSON for polygon {polygon_id}")
            return JSONResponse(content=feature)
        
        elif format == "kml":
            # Simple KML conversion
            kml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <kml xmlns="http://www.opengis.net/kml/2.2">
              <Document>
                <Placemark>
                  <name>{polygon.name}</name>
                  {geojson_to_kml(geojson)}
                </Placemark>
              </Document>
            </kml>"""
            logger.info(f"Returning KML for polygon {polygon_id}")
            return Response(
                content=kml,
                media_type="application/vnd.google-earth.kml+xml",
                headers={"Content-Disposition": f"attachment; filename=polygon_{polygon_id}.kml"}
            )
        
        logger.error(f"Unsupported format: {format}")
        raise HTTPException(status_code=400, detail="Unsupported format")
        
    except Exception as e:
        logger.exception(f"Error exporting polygon {polygon_id}")
        raise HTTPException(status_code=500, detail=str(e))

def geojson_to_kml(geojson):
    """Convert GeoJSON geometry to KML"""
    if geojson["type"] != "Polygon":
        raise ValueError("Only Polygon geometries supported")
        
    coords = geojson["coordinates"][0]  # Outer ring only
    coord_str = " ".join(f"{c[0]},{c[1]}" for c in coords)
    
    return f"""
        <Polygon>
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>{coord_str}</coordinates>
                </LinearRing>
            </outerBoundaryIs>
        </Polygon>
    """


@router.get("/{polygon_id}/raster-download")
async def get_raster(polygon_id: int, db: Session = Depends(get_db)):
    """Get the raster visualization for a polygon"""
    try:
        polygon = db.query(AnalysisPolygon).filter(AnalysisPolygon.id == polygon_id).first()
        if not polygon:
            logger.error(f"Polygon {polygon_id} not found")
            raise HTTPException(status_code=404, detail="Polygon not found")
        
        raster_path = DATA_DIR / str(polygon_id) / f"masked_raster_{polygon_id}.tif"
        logger.info(f"Looking for raster at: {raster_path}")
        
        if not raster_path.exists():
            logger.error(f"Raster file not found at {raster_path}")
            # Check if the directory exists
            if not (DATA_DIR / str(polygon_id)).exists():
                logger.error(f"Directory {DATA_DIR / str(polygon_id)} does not exist")
            raise HTTPException(status_code=404, detail=f"Raster not found at {raster_path}")
            
        logger.info(f"Serving raster from {raster_path}")
        return FileResponse(
            str(raster_path),
            media_type="image/tiff",
            filename=f"masked_raster_{polygon_id}.tif"
        )
    except Exception as e:
        logger.exception(f"Error serving raster for polygon {polygon_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{polygon_id}/raster-preview/")
async def get_raster_preview(polygon_id: int):
    """Get or create and serve the raster preview image"""
    try:

        polygon_dir = DATA_DIR / str(polygon_id)
        polygon_dir.mkdir(exist_ok=True)
        # masked_path = polygon_dir / f"masked_raster_{polygon_id}.tif"

        # Define paths
        tiff_path = polygon_dir / f"masked_raster_{polygon_id}.tif"
        jpg_path = polygon_dir / f"masked_raster_{polygon_id}.jpg"
        
        # Check if TIFF exists
        if not tiff_path.exists():
            raise HTTPException(status_code=404, detail="Raster TIFF not found")
        
        # Check if JPG exists, if not, create it
        if not jpg_path.exists():
            jpg_path.parent.mkdir(parents=True, exist_ok=True)
            with rasterio.open(tiff_path) as src:
                # Read the first band
                band1 = src.read(1)
                # Normalize the band to 0-255
                band1 = ((band1 - band1.min()) / (band1.max() - band1.min()) * 255).astype('uint8')
                # Create an image from the band
                img = Image.fromarray(band1)
                img.save(jpg_path, 'JPEG', quality=85)
        
        # Serve the JPG
        return Response(
            content=jpg_path.read_bytes(),
            media_type="image/jpeg"
        )
        
    except Exception as e:
        logger.error(f"Error serving raster preview: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{polygon_id}/download-raster-preview")
async def download_raster_preview(polygon_id: int):
    """Download the raster preview image, creating it if needed"""
    try:
        # Define paths
        polygon_dir = DATA_DIR / str(polygon_id)
        polygon_dir.mkdir(exist_ok=True)
        # masked_path = polygon_dir / f"masked_raster_{polygon_id}.tif"

        # Define paths
        tiff_path = polygon_dir / f"masked_raster_{polygon_id}.tif"
        jpg_path = polygon_dir / f"masked_raster_{polygon_id}.jpg"
        
        # Check if TIFF exists
        if not tiff_path.exists():
            raise HTTPException(status_code=404, detail="Raster TIFF not found")
        
        # Check if JPG exists, if not, create it
        if not jpg_path.exists():
            jpg_path.parent.mkdir(parents=True, exist_ok=True)
            with rasterio.open(tiff_path) as src:
                # Read the first band
                band1 = src.read(1)
                # Normalize the band to 0-255
                band1 = ((band1 - band1.min()) / (band1.max() - band1.min()) * 255).astype('uint8')
                # Create an image from the band
                img = Image.fromarray(band1)
                img.save(jpg_path, 'JPEG', quality=85)
        
        # Get file size for headers
        file_size = jpg_path.stat().st_size
        filename = f"cropland-analysis-{polygon_id}.jpg"
        
        # Serve the file as a download
        return FileResponse(
            path=jpg_path,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size)
            },
            media_type="image/jpeg",
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading raster preview: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session")
async def create_session():
    """Create a new session ID"""
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session: {session_id}")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear/{session_id}")
async def clear_session(session_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Clearing session: {session_id}")
        # Delete all polygons with this session_id
        db.query(AnalysisPolygon).filter(
            AnalysisPolygon.session_id == session_id
        ).delete()
        db.commit()
        return {"message": "Session cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))