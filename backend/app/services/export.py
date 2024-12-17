# backend/app/services/export.py
from dataclasses import dataclass
from datetime import datetime
import json
import geopandas as gpd
import pandas as pd
from typing import Dict, Any, List

@dataclass
class AnalysisMetadata:
    timestamp: datetime
    model_version: str
    confidence_score: float
    data_sources: List[str]
    processing_steps: List[Dict[str, Any]]

class ExportService:
    def __init__(self):
        self.supported_formats = {
            'shapefile': self._to_shapefile,
            'geojson': self._to_geojson,
            'geopackage': self._to_geopackage,
            'csv': self._to_csv,
            'report': self._to_detailed_report
        }

    async def export_analysis(self, analysis_id: int, format: str) -> bytes:
        """Export analysis results in specified format with full metadata"""
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
        
        # Fetch analysis data and metadata
        analysis_data = await self._get_analysis_data(analysis_id)
        
        # Add provenance and verification data
        analysis_data['metadata'] = self._generate_metadata(analysis_data)
        
        return await self.supported_formats[format](analysis_data)

    def _generate_metadata(self, analysis_data: Dict) -> AnalysisMetadata:
        """Generate comprehensive metadata for verification"""
        return AnalysisMetadata(
            timestamp=datetime.utcnow(),
            model_version=self._get_model_version(),
            confidence_score=analysis_data['confidence'],
            data_sources=[
                'Sentinel-2 MSI Level-2A',
                'Global Cropland Raster 30m',
                'Vision Model Analysis'
            ],
            processing_steps=self._get_processing_steps(analysis_data)
        )

    def _get_processing_steps(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """Record each step of the analysis for transparency"""
        return [
            {
                'step': 'satellite_data_fetch',
                'timestamp': analysis_data['sentinel_timestamp'],
                'source': 'Sentinel-2',
                'bands_used': ['B02', 'B03', 'B04', 'B08'],
                'resolution': '10m'
            },
            {
                'step': 'vision_model_analysis',
                'model_id': analysis_data['model_id'],
                'confidence': analysis_data['confidence'],
                'timestamp': analysis_data['analysis_timestamp']
            },
            {
                'step': 'soc_estimation',
                'method': 'ml_ensemble',
                'uncertainty_range': analysis_data['soc_uncertainty'],
                'validation_metrics': analysis_data['validation_stats']
            }
        ]

    async def _to_shapefile(self, data: Dict) -> bytes:
        """Export to Shapefile with embedded metadata"""
        gdf = gpd.GeoDataFrame(data['features'])
        # Add metadata as attributes
        gdf['metadata'] = json.dumps(data['metadata'].__dict__)
        return gdf.to_file('memory', driver='ESRI Shapefile')

    async def _to_geojson(self, data: Dict) -> Dict:
        """Export to GeoJSON with metadata in properties"""
        geojson = {
            'type': 'FeatureCollection',
            'features': data['features'],
            'metadata': data['metadata'].__dict__,
            'verification': {
                'hash': self._generate_hash(data),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        return geojson

    async def _to_detailed_report(self, data: Dict) -> bytes:
        """Generate detailed PDF report with all analysis steps"""
        # Implementation for generating detailed PDF report
        pass

    async def _to_csv(self, data: Dict) -> bytes:
        """Export to CSV with embedded metadata"""
        gdf = gpd.GeoDataFrame(data['features'])
        # Add metadata as attributes
        gdf['metadata'] = json.dumps(data['metadata'].__dict__)
        return gdf.to_csv('memory', index=False)




    async def _to_geopackage(self, data: Dict) -> bytes:
        """Export to GeoPackage with embedded metadata"""
        gdf = gpd.GeoDataFrame(data['features'])
        # Add metadata as attributes (you may need to adjust this for compatibility with GeoPackage)
        gdf['metadata'] = json.dumps(data['metadata'].__dict__)
        
        # Save to a GeoPackage in memory (use a BytesIO stream)
        from io import BytesIO
        output = BytesIO()
        gdf.to_file(output, driver='GPKG', layer='analysis')
        output.seek(0)
        return output.read()
