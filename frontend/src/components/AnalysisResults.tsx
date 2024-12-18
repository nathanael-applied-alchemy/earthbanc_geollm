import { useState } from 'react';
import SatelliteImages from '@/components/SatelliteImages';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';

interface AnalysisResultsProps {
  polygonId: number;
  results: {
    id: number;
    name: string;
    geometry: any;
    status: string;
    message: string;
    areas: any;
    cropland_data: {
      areas: {
        [key: string]: number;
      };
      total_area_km2: number;
      total_pixels: number;
      valid_pixels: number;
    } | null;
    created_at: string;
    updated_at: string;
    analysis_metadata?: any;
    carbon_estimates?: any;
    sentinel_data?: any;
    vision_results?: any;
  };
  geojson: string;
}

export default function AnalysisResults({ polygonId, geojson, results }: AnalysisResultsProps) {
  const [copySuccess, setCopySuccess] = useState('');
  const [satelliteError, setSatelliteError] = useState('');

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(results.geometry, null, 2))
      .then(() => {
        setCopySuccess('GeoJSON copied to clipboard!');
        setTimeout(() => setCopySuccess(''), 2000);
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
        setCopySuccess('Failed to copy GeoJSON');
      });
  };

  // if (!results) {
  //   return (
  //     <div className="p-6 bg-white rounded-lg shadow">
  //       <p>No analysis results available</p>
  //     </div>
  //   );
  // }

  if (!results) return null;

  return (
    <div className="mt-4 p-4 bg-white rounded-lg shadow">

      {/* Only show analysis if areas data exists */}
      {results.cropland_data && results.cropland_data.total_area_km2 >= 0.01 && (

  <div className="space-y-6 bg-white rounded-lg shadow">
        <h2 className="text-2xl font-bold px-6 pt-6">{results.name}</h2>

        {/* Polygon Info */}
        <div className="space-y-2 px-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Polygon Information</h3>
            <div className="flex items-center space-x-2">
              {copySuccess && <span className="text-green-500">{copySuccess}</span>}
              <button
                type="button"
                onClick={handleCopyToClipboard}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Copy GeoJSON
              </button>

              <a
                href={`/api/polygons/${polygonId}/export/kml`}
                download={`polygon-${polygonId}.kml`}
                className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50"
              >
                Download KML
              </a>
              <a
                href={`/api/polygons/${polygonId}/export/geojson`}
                download={`polygon-${polygonId}.geojson`}
                className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50"
              >
                Download GeoJSON
              </a>
            </div>
          </div>
          <div className="bg-gray-50 rounded">
            <div className="max-h-32 overflow-y-auto p-4">
              <pre className="text-sm whitespace-pre-wrap">
                {JSON.stringify(results.geometry, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Analysis Results with Satellite Images */}
        {results.cropland_data && (
          <div className="space-y-2 px-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold analysis-results">Analysis Results</h3>
            </div>
            <div className="p-4 bg-gray-50 rounded">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium">Areas</h4>
                  {Object.entries(results.cropland_data.areas).map(([key, value]) => (
                    <div key={key} className="space-y-1">
                      <div className="font-medium">{key}:</div>
                      {typeof value === 'object' && value !== null && (
                        <div className="pl-4 text-sm">
                          {value.area_km2 !== undefined && (
                            <div>Area: {value.area_km2.toFixed(2)} km²</div>
                          )}
                          {value.area_ha !== undefined && (
                            <div>Area: {value.area_ha.toFixed(2)} ha</div>
                          )}
                          {value.area_m2 !== undefined && (
                            <div>Area: {value.area_m2.toFixed(2)} m²</div>
                          )}
                          {value.area_acres !== undefined && (
                            <div>Area: {value.area_acres.toFixed(2)} acres</div>
                          )}
                          {value.area_sq_mile !== undefined && (
                            <div>Area: {value.area_sq_mile.toFixed(2)} sq. miles</div>
                          )}
                          {value.percentage !== undefined && (
                            <div>Percentage: {value.percentage.toFixed(2)}%</div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div>
                  <div>Total Area: {typeof results.cropland_data.total_area_km2 === 'number' ? 
                    results.cropland_data.total_area_km2.toFixed(2) : results.cropland_data.total_area_km2} km²</div>
                  <div>Total Area: {typeof results.cropland_data.total_area_sq_mile === 'number' ? 
                    results.cropland_data.total_area_sq_mile.toFixed(2) : results.cropland_data.total_area_sq_mile} sq. miles</div>
                  <div>Total Pixels: {results.cropland_data.total_pixels}</div>
                  <div>Valid Pixels: {results.cropland_data.valid_pixels}</div>
                </div>
              </div>
            </div>
          </div>


)}

        {/* Raster Preview */}
        {polygonId && (
          <div className="space-y-2 px-6 pb-6">
            <h3 className="text-lg font-semibold cropland-analysis">Cropland Analysis</h3>
            <div className="relative w-full h-[300px] bg-gray-100 rounded overflow-hidden">
              <img 
                src={`/api/polygons/${polygonId}/raster-preview/`}
                alt="Cropland Analysis"
                className="object-contain w-full h-full"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.onerror = null;
                  target.parentElement!.innerHTML = `
                    <div class="flex items-center justify-center h-full bg-gray-100 text-gray-500">
                      No raster data available for this area
                    </div>
                  `;
                }}
              />
              <div className="absolute bottom-0 right-0 p-2 space-x-2 bg-white bg-opacity-75">
                <a
                  href={`/api/polygons/${polygonId}/raster-preview`}
                  download={`cropland-analysis-${polygonId}.jpg`}
                  className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50"
                >
                  Download JPG
                </a>
                <a
                  href={`/api/polygons/${polygonId}/raster-download`}
                  download={`cropland-analysis-${polygonId}.tif`}
                  className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50"
                >
                  Download TIFF
                </a>
              </div>
            </div>
          </div>

)}
</div>



)}



        {/* Satellite Images Section */}
        <div className="px-6">
          <SatelliteImages 
            geojson={results.geometry}
            onError={(error) => setSatelliteError(error)}
          />
          {satelliteError && (
            <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
              {satelliteError}
            </div>
          )}
        </div>


      </div>

    );
  }