// "use client"

// import React, { useState, useEffect } from 'react'
// import type { FormEvent } from 'react'

// const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';


// export default function SatelliteController() {
//   const [geojson, setGeojson] = useState('')
//   const [tasks, setTasks] = useState<{ name: string; status: string; fileName?: string }[]>([])
//   const [error, setError] = useState('')

//   const handleSubmit = async (e: FormEvent) => {
//     e.preventDefault()
//     setError('')
//     setTasks([])

//     try {
//       const response = await fetch(`${API_BASE}/api/satellite/retrieve-satellite-image`, {
//         method: 'POST',
//         headers: { 
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ polygon_geojson: JSON.parse(geojson) }),
//       })

//       const data = await response.json()
//       if (response.ok) {
//         setTasks(data.tasks.map((task: any) => ({ name: task.name, status: 'processing' })))
//       } else {
//         setError('Failed to start image retrieval')
//         console.error('Error starting image retrieval:', data)
//       }
//     } catch (error) {
//       setError('An error occurred')
//       console.error('Error:', error)
//     }
//   }

//   useEffect(() => {
//     const interval = setInterval(async () => {
//       if (tasks.some(task => task.status === 'processing')) {
//         try {
//           const response = await fetch(`${API_BASE}/api/satellite/task-status`)
//           const data = await response.json()
//           if (response.ok) {
//             setTasks(prevTasks =>
//               prevTasks.map(task => ({
//                 ...task,
//                 status: data[task.name]?.status || task.status,
//                 fileName: data[task.name]?.fileName || task.fileName,
//               }))
//             )
//           }
//         } catch (error) {
//           console.error('Error fetching task status:', error)
//         }
//       }
//     }, 5000)

//     return () => clearInterval(interval)
//   }, [tasks])

//   return (
//     <div className="container mx-auto p-4">
//       <h1 className="text-2xl font-bold mb-4">Satellite Image Retrieval</h1>
//       <form onSubmit={handleSubmit} className="space-y-4">
//         <textarea
//           value={geojson}
//           onChange={(e) => setGeojson(e.target.value)}
//           placeholder="Enter Polygon GeoJSON"
//           className="w-full p-2 border border-gray-300 rounded"
//           rows={6}
//         />
//         <button
//           type="submit"
//           className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
//         >
//           Retrieve Images
//         </button>
//       </form>
//       {error && <p className="mt-4 text-red-500">{error}</p>}
//       <div className="mt-4 space-y-2">
//         {tasks.map((task, index) => (
//           <div key={index} className="p-4 border border-gray-300 rounded bg-gray-100">
//             <p className="font-semibold">{task.name}</p>
//             {task.status === 'processing' ? (
//               <div className="flex items-center">
//                 <div className="loader mr-2"></div>
//                 <span>Processing...</span>
//               </div>
//             ) : (
//               <p className="text-green-500">Completed: {task.fileName}</p>
//             )}
//           </div>
//         ))}
//       </div>
//     </div>
//   )
// }

// frontend/src/app/satellite_controller/page.tsx

"use client"
import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';



// Helper function to calculate rough area estimate on client side
const calculateRoughArea = (geojson) => {
  try {
    const coordinates = geojson.coordinates[0];
    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;
    
    // Find bounds
    coordinates.forEach(([lng, lat]) => {
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });
    
    // Rough conversion factors (at equator)
    const KM_PER_LAT_DEGREE = 111;  // roughly constant
    const KM_PER_LNG_DEGREE = Math.cos((minLat + maxLat) / 2 * Math.PI / 180) * 111;
    
    // Calculate rough area
    const heightKm = (maxLat - minLat) * KM_PER_LAT_DEGREE;
    const widthKm = (maxLng - minLng) * KM_PER_LNG_DEGREE;
    
    return heightKm * widthKm;
  } catch (error) {
    console.error('Error calculating area:', error);
    return Infinity;  // Return Infinity to fail validation if calculation fails
  }
};


export default function SatelliteController() {
  const [geojson, setGeojson] = useState('');
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState('');



  // Initialize tasks based on backend visualization types
  const initializeTasks = () => {
    const taskNames = {
      'TrueColor': 'sentinel_truecolor',
      'NDWI': 'sentinel_ndwi',
      'AgriColor': 'sentinel_agricolor',
      'MSAVI2': 'sentinel_msavi2'
    };


    return Object.entries(taskNames).map(([displayName, taskName]) => ({
      displayName,
      name: taskName,
      status: 'processing',
      fileName: null
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {


      const parsedGeojson = JSON.parse(geojson);
      
      // Client-side area validation
      const roughArea = calculateRoughArea(parsedGeojson);
      if (roughArea > 225) { // Using 25 as client threshold to account for estimation differences
        throw new Error(`Selected area is too large (approximately ${roughArea.toFixed(1)} km²). Maximum allowed area is 200 km².`);
      }

      // Initialize tasks at submission
      const initialTasks = initializeTasks();
      setTasks(initialTasks);

      const response = await fetch(`${API_BASE}/api/satellite/retrieve-satellite-image`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ polygon_geojson: JSON.parse(geojson) }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTasks(data.tasks.map(task => ({ 
        name: task.name, 
        status: 'processing',
        fileName: null 
      })));
    } catch (error) {
      setError(`Error: ${error.message}`);
      console.error('Submission error:', error);
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
        console.log('Status update:', statusData);
        
        if (mounted) {
          setTasks(prevTasks =>
            prevTasks.map(task => {
              const taskStatus = statusData[task.displayName] || {};
              return {
                ...task,
                status: taskStatus.status || task.status,
                fileName: taskStatus.fileName || task.fileName
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
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ marginBottom: '20px' }}>Satellite Image Retrieval</h1>
      
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <div>
          <textarea
            value={geojson}
            onChange={(e) => setGeojson(e.target.value)}
            placeholder="Enter Polygon GeoJSON"
            rows={6}
            style={{ 
              width: '100%', 
              marginBottom: '10px',
              padding: '10px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          />
        </div>
        <button 
          type="submit"
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retrieve Images
        </button>
      </form>

      {error && (
        <div style={{ 
          color: 'red', 
          padding: '10px', 
          marginBottom: '20px',
          border: '1px solid red',
          borderRadius: '4px',
          backgroundColor: '#fff5f5'
        }}>
          {error}
        </div>
      )}

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px' 
      }}>
        {tasks.map((task, index) => (
          <div 
            key={index} 
            style={{ 
              padding: '15px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: '#fff'
            }}
          >
            <h3 style={{ marginBottom: '10px' }}>{task.displayName}</h3>
            <p>Status: {task.status}</p>
            {task.status === 'completed' && task.fileName && (
              <div>
                <img 
                  src={`${API_BASE}/api/satellite/get-image/${task.fileName.replace('.tif', '')}`}
                  alt={task.displayName}
                  style={{ 
                    width: '100%', 
                    height: 'auto',
                    marginTop: '10px',
                    borderRadius: '4px'
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}