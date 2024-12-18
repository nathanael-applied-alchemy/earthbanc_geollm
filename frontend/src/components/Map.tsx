// frontend/src/components/Map.tsx
'use client';

import { MapContainer, TileLayer, FeatureGroup, GeoJSON, useMap } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import type { FeatureGroup as FeatureGroupType } from 'leaflet';
import { useRef, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_BASE } from '@/lib/api';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import '@/styles/leaflet-overrides.css';

// Import Draw explicitly
import 'leaflet-draw';

interface MapProps {
  onPolygonCreated?: (geometry: any, sessionId: string) => void;
  polygons?: Array<any>;
  onPolygonClick?: (id: number) => void;
  onSessionClear?: () => void;
  isAnalyzing?: boolean;
}

// Create a component to handle draw control initialization
function DrawControl({ onCreated, featureGroupRef }: { 
  onCreated: (e: any) => void;
  featureGroupRef: React.RefObject<FeatureGroupType>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !featureGroupRef.current) return;

    // Make sure we're in the browser
    if (typeof window !== 'undefined') {
      // Create the draw control
      const drawControl = new (L.Control as any).Draw({
        position: 'topleft',
        draw: {
          rectangle: false,
          circle: false,
          circlemarker: false,
          marker: false,
          polyline: false,
          polygon: {
            allowIntersection: false,
            drawError: {
              color: '#e1e100',
              message: '<strong>Cannot draw intersecting lines!</strong>'
            },
            shapeOptions: {
              color: '#3388ff'
            }
          }
        },
        edit: {
          featureGroup: featureGroupRef.current,
          edit: false,
          remove: false
        }
      });

      map.addControl(drawControl);

      map.on(L.Draw.Event.CREATED, onCreated);

      return () => {
        map.removeControl(drawControl);
        map.off(L.Draw.Event.CREATED, onCreated);
      };
    }
  }, [map, onCreated, featureGroupRef]);

  return (
    <FeatureGroup ref={featureGroupRef}>
      {/* Children will be GeoJSON layers */}
    </FeatureGroup>
  );
}

const Map = ({ onPolygonCreated, polygons = [], onPolygonClick, onSessionClear, isAnalyzing }: MapProps) => {
  const [mapReady, setMapReady] = useState(false);
  const [selectedPolygon, setSelectedPolygon] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [localPolygons, setLocalPolygons] = useState(polygons);
  const featureGroupRef = useRef<FeatureGroupType | null>(null);
  const router = useRouter();

  // Debug: Log props changes
  useEffect(() => {
    console.log('Map props updated:', { polygons, isAnalyzing });
  }, [polygons, isAnalyzing]);

  useEffect(() => {
    console.log('Checking for existing session...');
    const storedSessionId = localStorage.getItem('sessionId');
    if (storedSessionId) {
      console.log('Found stored session:', storedSessionId);
      setSessionId(storedSessionId);
    } else {
      console.log('No stored session found, creating new session...');
      createSession();
    }
  }, []);

  // Debug: Log when sessionId changes
  useEffect(() => {
    console.log('Current sessionId:', sessionId);
  }, [sessionId]);

  const clearSession = async () => {
    if (!sessionId) {
      console.log('No session to clear');
      return;
    }
    
    try {
      console.log('Clearing session:', sessionId);
      const response = await fetch(`${API_BASE}/api/polygons/clear/${sessionId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Clear session response:', response.status, errorData);
        throw new Error('Failed to clear session');
      }
      
      // Clear local state
      setLocalPolygons([]);
      setSelectedPolygon(null);
      
      // Clear the draw layer
      if (featureGroupRef.current) {
        featureGroupRef.current.clearLayers();
      }
      
      // Notify parent component
      onSessionClear?.();
      
      console.log('Session cleared successfully');
      
    } catch (error) {
      console.error('Error clearing session:', error);
      throw error;
    }
  };
  const createSession = async () => {
    try {
      console.log('Making request to create session...');
      const response = await fetch(`${API_BASE}/api/polygons/session`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const data = await response.json();
      console.log('Session created:', data);
      setSessionId(data.session_id);
      localStorage.setItem('sessionId', data.session_id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const handleCreated = async (e: any) => {
    console.log('Draw event:', e);
    console.log('Draw event type:', e.layerType);
    
    const layer = e.layer;
    console.log('Layer:', layer);
    
    const geoJSON = layer.toGeoJSON().geometry;
    console.log('GeoJSON geometry:', geoJSON);
    
    if (!sessionId) {
      console.error('No session ID available');
      return;
    }

    console.log('Calling onPolygonCreated with:', {
      geometry: geoJSON,
      sessionId: sessionId
    });

    if (onPolygonCreated) {
      onPolygonCreated(geoJSON, sessionId);
    }
    
    // Clear the draw layer after creating
    if (featureGroupRef.current) {
      featureGroupRef.current.clearLayers();
      console.log('Cleared drawing layers');
    }
  };

  // Update localPolygons when props change
  useEffect(() => {
    console.log('Updating local polygons:', polygons);
    setLocalPolygons(polygons);
  }, [polygons]);

  return (
    <div className="w-full space-y-4">
      <div className="flex justify-end">
        <button
          onClick={clearSession}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded shadow"
        >
          Clear Session
        </button>
      </div>

      <div className="h-[600px] relative border rounded-lg overflow-hidden">
        {isAnalyzing && (
          <div className="absolute top-0 left-0 right-0 z-50 bg-blue-500 text-white px-4 py-2 text-center">
            Analyzing area...
          </div>
        )}
        
        <div className="absolute top-2 left-12 z-[1000] bg-white px-4 py-2 rounded shadow">
          <p className="text-sm">Click the polygon icon to start drawing an area</p>
        </div>
        
        <MapContainer
          center={[0, 0]}
          zoom={2}
          className="w-full h-full"
          whenReady={() => {
            console.log('MapContainer ready');
            setMapReady(true);
          }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          <DrawControl onCreated={handleCreated} featureGroupRef={featureGroupRef} />

          {mapReady && localPolygons.map((polygon) => (
            <GeoJSON
              key={polygon.id}
              data={{
                type: 'Feature',
                geometry: polygon.geometry,
                properties: { id: polygon.id }
              }}
              style={() => ({
                color: selectedPolygon?.id === polygon.id ? '#ff4444' : '#3388ff',
                weight: 3,
                opacity: 0.65
              })}
              eventHandlers={{
                click: () => {
                  setSelectedPolygon(polygon);
                  onPolygonClick && onPolygonClick(polygon.id);
                }
              }}
            />
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default Map;