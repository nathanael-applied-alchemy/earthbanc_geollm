# backend/app/models/export.py
from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Export(Base):
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True)
    polygon_id = Column(Integer, ForeignKey('analysis_polygons.id'))
    format = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String)  # If you're storing exports
    
    polygon = relationship("AnalysisPolygon", back_populates="exports")