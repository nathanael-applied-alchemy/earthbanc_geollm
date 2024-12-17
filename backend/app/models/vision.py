# backend/app/models/vision.py
from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class VisionAnalysis(Base):
    __tablename__ = "vision_analyses"
    
    id = Column(Integer, primary_key=True)
    polygon_id = Column(Integer, ForeignKey('analysis_polygons.id'))
    model_version = Column(String)
    confidence_score = Column(Float)
    results = Column(JSON)  # Store detailed analysis results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    polygon = relationship("AnalysisPolygon", back_populates="vision_analyses")