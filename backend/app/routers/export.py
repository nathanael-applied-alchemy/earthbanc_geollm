# backend/app/routers/export.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.export import ExportService

router = APIRouter()
export_service = ExportService()

@router.get("/{analysis_id}")
async def export_analysis(analysis_id: int, format: str):
    """Export analysis with full transparency data"""
    try:
        return await export_service.export_analysis(analysis_id, format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/formats")
async def get_supported_formats():
    """List available export formats"""
    return {
        "formats": list(export_service.supported_formats.keys()),
        "default": "geojson"
    }