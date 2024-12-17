# backend/app/services/raster_analysis.py
from typing import Dict, Any, Optional
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import shape, mapping
import logging

logger = logging.getLogger(__name__)

class RasterAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path

    async def extract_mask(self, geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and analyze masked raster data for a polygon
        """
        try:
            with rasterio.open(self.file_path) as src:
                # Convert GeoJSON to shapely then to rasterio geometry
                geom = shape(geometry)
                geom_bounds = geom.bounds
                
                # Check if geometry intersects with raster
                raster_bounds = src.bounds
                if not (raster_bounds.left < geom_bounds[2] and 
                       raster_bounds.right > geom_bounds[0] and
                       raster_bounds.top > geom_bounds[1] and
                       raster_bounds.bottom < geom_bounds[3]):
                    return None

                # Mask raster with geometry
                masked_data, transform = mask(src, [mapping(geom)], 
                                           crop=True, 
                                           all_touched=True,
                                           nodata=0)
                
                # Analyze masked data
                valid_data = masked_data[0]  # Get first band
                unique, counts = np.unique(valid_data[valid_data != 0], 
                                         return_counts=True)
                
                # Calculate areas (approximate)
                pixel_area = abs(transform[0] * transform[4])  # in square degrees
                areas = {}
                
                for val, count in zip(unique, counts):
                    val_int = int(val)
                    area_sqkm = count * pixel_area * 12321  # rough conversion to km2
                    areas[val_int] = {
                        "pixel_count": int(count),
                        "area_km2": float(area_sqkm),
                        "area_ha": float(area_sqkm * 100)
                    }

                return {
                    "status": "success",
                    "bounds": {
                        "minx": geom_bounds[0],
                        "miny": geom_bounds[1],
                        "maxx": geom_bounds[2],
                        "maxy": geom_bounds[3]
                    },
                    "pixel_stats": {
                        "total": int(valid_data.size),
                        "valid": int(np.sum(valid_data != 0))
                    },
                    "areas": areas,
                    "metadata": {
                        "transform": transform.to_gdal(),
                        "crs": str(src.crs)
                    }
                }

        except Exception as e:
            logger.error(f"Error in raster analysis: {str(e)}")
            return None