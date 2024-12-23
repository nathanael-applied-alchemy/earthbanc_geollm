# # backend/app/routers/analysis.py
# from fastapi import APIRouter, HTTPException
# from app.services.raster_analysis import RasterAnalyzer
# from typing import Dict, Any
# import json
# from shapely.geometry import shape
# router = APIRouter()

# # Load tile reference
# with open('app/data/LGRIP30_v001_tiles.json', 'r') as f:
#     TILE_REFERENCE = json.load(f)

# @router.post("/analyze_polygon")
# async def analyze_polygon(geometry: Dict[str, Any]):
#     """Analyze LGRIP30 data for a polygon"""
#     try:
#         # Get bounds and find relevant tiles
#         bounds = shape(geometry).bounds
#         relevant_tiles = []
        
#         for tile_id, tile_info in TILE_REFERENCE['tiles'].items():
#             tile_bounds = tile_info['bounds']
#             if (bounds[0] < tile_bounds['maxx'] and bounds[2] > tile_bounds['minx'] and
#                 bounds[1] < tile_bounds['maxy'] and bounds[3] > tile_bounds['miny']):
#                 relevant_tiles.append(tile_info)

#         # Analyze each relevant tile
#         results = []
#         for tile in relevant_tiles:
#             analyzer = RasterAnalyzer(tile['path'])
#             result = await analyzer.analyze_polygon(geometry)
#             results.append(result)

#         # Combine results
#         combined_areas = {}
#         for result in results:
#             for class_id, area_info in result['areas'].items():
#                 if class_id not in combined_areas:
#                     combined_areas[class_id] = {
#                         "pixel_count": 0,
#                         "area_km2": 0.0,
#                         "area_ha": 0.0
#                     }
#                 combined_areas[class_id]["pixel_count"] += area_info["pixel_count"]
#                 combined_areas[class_id]["area_km2"] += area_info["area_km2"]
#                 combined_areas[class_id]["area_ha"] += area_info["area_ha"]

#         return {
#             "status": "success",
#             "areas": combined_areas,
#             "tiles_analyzed": len(results)
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))