# backend/app/schemas/polygon.py
from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional, Dict, Any
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

class PolygonBase(BaseModel):
    name: str
    geometry: Dict[str, Any]  # GeoJSON format
    session_id: str

class PolygonCreate(PolygonBase):
    pass

class PolygonResponse(PolygonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    sentinel_data: Optional[Dict[str, Any]]
    cropland_data: Optional[Dict[str, Any]]
    vision_results: Optional[Dict[str, Any]]
    carbon_estimates: Optional[Dict[str, Any]]
    analysis_metadata: Optional[Dict[str, Any]]
    session_id: Optional[str]
    
    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def convert_geometry(cls, data):
        if hasattr(data, '__dict__'):
            # Convert model instance to dict
            data = data.__dict__
        
        if isinstance(data, dict) and 'geometry' in data:
            if hasattr(data['geometry'], '__class__') and data['geometry'].__class__.__name__ == 'WKBElement':
                # Convert WKBElement to GeoJSON
                shape = to_shape(data['geometry'])
                data['geometry'] = mapping(shape)
        return data