// frontend/src/app/page.tsx
'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import BoundarySearch from '@/components/BoundarySearch';
import AnalysisResults from '@/components/AnalysisResults';
import { api } from '@/lib/api';

// Dynamically import Map component with no SSR
const MapWithNoSSR = dynamic(
  () => import('@/components/Map'),
  { ssr: false }
);

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [polygonId, setPolygonId] = useState<number | null>(null);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [selectedPolygonId, setSelectedPolygonId] = useState<number | null>(null);
  const [analysisResults, setAnalysisResults] = useState<any | null>(null);
  const [croplandAnalysis, setCroplandAnalysis] = useState<any | null>(null);
  const [satelliteImagery, setSatelliteImagery] = useState<any | null>(null);
  const handlePolygonCreate = async (
    geometry: any, 
    sessionId: string, 
    name: string = `Analysis ${Date.now()}`
  ) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Creating polygon:', {
        name,
        geometry,
        sessionId
      });

      const polygon = await api.createPolygon({
        name,
        geometry,
        sessionId
      });
      
      setPolygonId(polygon.id);
      
      // Analyze the polygon
      const analysisResult = await api.analyzePolygon(polygon.id);
      setCroplandAnalysis(analysisResult);
      // Get the complete polygon data with analysis results
      const updatedPolygon = await api.getPolygon(polygon.id);
      
      // Update results and select the new polygon
      setResults(prev => [...prev, updatedPolygon]);
      setSelectedResult(updatedPolygon);
      setLoading(false);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  const handlePolygonClick = async (id: number) => {
    try {
      const polygon = results.find(p => p.id === id);
      if (polygon) {
        setSelectedResult(polygon);
        setPolygonId(id);
      }
    } catch (error) {
      console.error('Error handling polygon click:', error);
    }
  };

  const handleSessionClear = () => {

    console.log('Clearing session');
    setSelectedPolygonId(null);
    setAnalysisResults(null);
    setSatelliteImagery(null);
    setCroplandAnalysis(null);
    setSelectedResult(null);
    setResults([]);
  };

  // Load initial polygons
  useEffect(() => {
    const loadPolygons = async () => {
      try {
        const polygons = await api.getAnalyzedPolygons();
        setResults(polygons);
      } catch (error) {
        console.error('Error loading polygons:', error);
      }
    };
    loadPolygons();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <BoundarySearch 
          onAnalysisStart={() => setLoading(true)}
          onAnalysisComplete={(result) => {
            setResults(prev => [...prev, result]);
            setSelectedResult(result);
            setLoading(false);
          }}
          onBoundarySelect={(geometry, name) => {
            const sessionId = localStorage.getItem('sessionId');
            if (!sessionId) {
              console.error('No session ID available');
              return;
            }
            handlePolygonCreate(geometry, sessionId, name);
          }}
        />
        
        <div className="space-y-4">
          <MapWithNoSSR 
            onPolygonCreated={(geometry, sessionId) => {
              handlePolygonCreate(geometry, sessionId);
            }}
            onPolygonClick={handlePolygonClick}
            polygons={results}
            isAnalyzing={loading}
            onSessionClear={handleSessionClear}
          />

          {selectedResult && (
            <AnalysisResults 
              polygonId={selectedResult.id} 
              results={selectedResult} 
            />
          )}
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </main>
  );
}