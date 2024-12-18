// frontend/src/lib/api.ts
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';

console.log('API_BASE:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007');

export interface AreaInfo {
  pixel_count: number;
  area_km2: number;
  area_ha: number;
}

export interface CroplandData {
  status: string;
  areas: {
    [key: string]: AreaInfo;
  };
  tiles_analyzed: number;
  missing_tiles: any;
  timestamp: string;
}

export interface Polygon {
  id: number;
  name: string;
  geometry: any;
  created_at: string;
  updated_at?: string;
  sentinel_data?: any;
  vision_results?: any;
  carbon_estimates?: any;
  analysis_metadata?: any;
  cropland_data?: CroplandData;
}

export interface AnalysisResult {
  status: string;
  polygon_id: number;
  cropland_analysis: CroplandData;
  metadata: any;
  message: string;
}

export const api = {
  async createPolygon(data: { name: string; geometry: any; sessionId: string }) {
    const response = await fetch(`${API_BASE}/api/polygons/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: data.name,
        geometry: data.geometry,
        session_id: data.sessionId
      }),
    });
    if (!response.ok) throw new Error('Failed to create polygon');
    return response.json();
  },

  async getPolygon(id: number): Promise<Polygon> {
    const response = await fetch(`${API_BASE}/api/polygons/${id}`);
    if (!response.ok) throw new Error('Failed to fetch polygon');
    return response.json();
  },

  async analyzePolygon(id: number): Promise<AnalysisResult> {
    const response = await fetch(`${API_BASE}/api/polygons/${id}/analyze`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to analyze polygon');
    return response.json();
  },

  async getAllPolygons(): Promise<Polygon[]> {
    const response = await fetch(`${API_BASE}/api/polygons/`);
    if (!response.ok) throw new Error('Failed to fetch polygons');
    return response.json();
  },

  async getAnalyzedPolygons(): Promise<Polygon[]> {
    const polygons = await this.getAllPolygons();
    return polygons.filter(p => p.cropland_data);
  }
};

// Constants for cropland classes
export const CROPLAND_CLASSES = {
  '1': 'Non-croplands',
  '2': 'Irrigated croplands',
  '3': 'Rainfed croplands'
} as const;