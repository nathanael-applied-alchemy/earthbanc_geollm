import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';

interface SatelliteImageProps {
  geojson: any;  // The polygon GeoJSON to analyze
  onError?: (error: string) => void;
}

// Helper function to calculate rough area estimate on client side
const calculateRoughArea = (geojson: any) => {
  try {
    const coordinates = geojson.coordinates[0];
    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;
    
    coordinates.forEach(([lng, lat]: [number, number]) => {
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });
    
    const KM_PER_LAT_DEGREE = 111;
    const KM_PER_LNG_DEGREE = Math.cos((minLat + maxLat) / 2 * Math.PI / 180) * 111;
    
    const heightKm = (maxLat - minLat) * KM_PER_LAT_DEGREE;
    const widthKm = (maxLng - minLng) * KM_PER_LNG_DEGREE;
    
    return heightKm * widthKm;
  } catch (error) {
    console.error('Error calculating area:', error);
    return Infinity;
  }
};

export default function SatelliteImages({ geojson, onError }: SatelliteImageProps) {
  const [tasks, setTasks] = useState<Array<{
    displayName: string;
    name: string;
    status: string;
    fileName: string | null;
  }>>([
    { displayName: 'TrueColor', name: 'sentinel_truecolor', status: 'waiting', fileName: null },
    { displayName: 'NDWI', name: 'sentinel_ndwi', status: 'waiting', fileName: null },
    { displayName: 'AgriColor', name: 'sentinel_agricolor', status: 'waiting', fileName: null },
    { displayName: 'MSAVI2', name: 'sentinel_msavi2', status: 'waiting', fileName: null }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const retrieveSatelliteImages = async () => {
    setIsLoading(true);
    
    try {
      const roughArea = calculateRoughArea(geojson);
      if (roughArea > 225) {
        throw new Error(`Selected area is too large (approximately ${roughArea.toFixed(1)} km²). Maximum allowed area is 200 km².`);
      }

      // Set all tasks to processing state
      setTasks(prevTasks => 
        prevTasks.map(task => ({
          ...task,
          status: 'processing',
          fileName: null
        }))
      );

      const response = await fetch(`${API_BASE}/api/satellite/retrieve-satellite-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ polygon_geojson: geojson }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error occurred' }));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Update tasks based on returned files
      if (data.files && Array.isArray(data.files)) {
        setTasks(prevTasks => 
          prevTasks.map(task => {
            const fileName = data.files.find((f: string) => f.includes(task.name.toLowerCase()));
            return {
              ...task,
              status: fileName ? 'completed' : 'processing',
              fileName: fileName ? fileName.split('.')[0] : null
            };
          })
        );
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to retrieve satellite imagery';
      onError?.(errorMessage);
      console.error('Satellite retrieval error:', error);
      
      setTasks(prevTasks => 
        prevTasks.map(task => ({
          ...task,
          status: 'waiting',
          fileName: null
        }))
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const interval = setInterval(async () => {
      // Only poll if we have any processing tasks
      if (!tasks.some(task => task.status === 'processing')) {
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/api/satellite/task-status`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const statusData = await response.json();
        
        if (mounted) {
          setTasks(prevTasks =>
            prevTasks.map(task => {
              const taskStatus = statusData[task.displayName];
              if (!taskStatus) return task;
              
              // Update task status and filename when completed
              if (taskStatus.status === 'completed' && taskStatus.fileName) {
                return {
                  ...task,
                  status: 'completed',
                  fileName: taskStatus.fileName.split('.')[0]  // Remove file extension
                };
              }
              
              return {
                ...task,
                status: taskStatus.status || task.status
              };
            })
          );
        }
      } catch (error) {
        console.error('Status check error:', error);
      }
    }, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [tasks]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Satellite Imagery</h3>
        <button
          onClick={retrieveSatelliteImages}
          disabled={isLoading}
          className={`px-4 py-2 rounded ${
            isLoading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white`}
        >
          {isLoading ? 'Retrieving...' : 'Get Satellite Images'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {tasks.map((task, index) => (
          <div 
            key={index} 
            className="p-4 border rounded-lg bg-white"
          >
            <h3 className="font-medium mb-2">{task.displayName}</h3>
            {task.status === 'processing' ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                <span>Processing...</span>
              </div>
            ) : task.status === 'completed' && task.fileName ? (
              <div>
                <img 
                  src={`${API_BASE}/api/satellite/get-image/${task.fileName.split('.')[0]}`}
                  alt={task.displayName}
                  className="w-full h-auto rounded mt-2"
                />
              </div>
            ) : (
              <p className="text-gray-500">Waiting to start...</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}