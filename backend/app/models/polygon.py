# backend/app/models/polygon.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from geoalchemy2.types import Geometry
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class AnalysisPolygon(Base):
    __tablename__ = "analysis_polygons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    session_id = Column(String, index=True)  # Add this line
    
    geometry = Column(Geometry('POLYGON', srid=4326, spatial_index=False))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Analysis results
    sentinel_data = Column(JSON, nullable=True)
    cropland_data = Column(JSON, nullable=True)
    vision_results = Column(JSON, nullable=True)
    carbon_estimates = Column(JSON, nullable=True)
    
    # Metadata for verification
    analysis_metadata = Column(JSON, nullable=True)  # Store versions, timestamps, etc.
    analysis_history = Column(JSON, nullable=True)  # Track processing steps
    analysis_status = Column(String, nullable=True)  # Add this line
    # Relationship with Export model
    exports = relationship("Export", back_populates="polygon")
    vision_analyses = relationship("VisionAnalysis", back_populates="polygon")