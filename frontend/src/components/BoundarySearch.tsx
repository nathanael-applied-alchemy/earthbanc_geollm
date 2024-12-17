import { useState, useEffect } from 'react';
import { getCachedBoundary, ADMIN_LEVELS } from '@/lib/boundaries';
import { api } from '@/lib/api';

interface BoundarySearchProps {
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: any) => void;
  onBoundarySelect: (geometry: any, name: string) => void;
}

interface Region {
  id: string;
  name: string;
  geometry: any;
}

// Define admin level hierarchies for different countries
const COUNTRY_ADMIN_LEVELS: { [key: string]: number[] } = {
  'US': [1, 2], // States (1), Counties (2)
  'GB': [1, 2, 3], // Countries (1), Counties (2), Districts (3)
  'KE': [1, 2], // Counties (1), Sub-Counties (2)
  'IN': [1, 2, 3], // States (1), Districts (2), Sub-Districts (3)
  'BR': [1, 2] // States (1), Municipalities (2)
};

export default function BoundarySearch({ 
  onAnalysisStart, 
  onAnalysisComplete,
  onBoundarySelect 
}: BoundarySearchProps) {
  const [country, setCountry] = useState('');
  const [level, setLevel] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Store available regions for each level
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);

  // Get available admin levels for selected country
  const getAvailableLevels = (countryCode: string) => {
    return COUNTRY_ADMIN_LEVELS[countryCode] || [];
  };

  // Load regions when country/level changes
  useEffect(() => {
    if (country && level !== null) {
      loadRegions();
    } else {
      setRegions([]);
      setSelectedRegion(null);
    }
  }, [country, level]);

  const loadRegions = async () => {
    setLoading(true);
    setError(null);
    try {
      const boundaryData = await getCachedBoundary(country, level!);
      const availableRegions = boundaryData.features.map(feature => ({
        id: feature.properties?.id?.toString() || '',
        name: feature.properties?.name || 'Unnamed Region',
        geometry: feature.geometry
      }));
      setRegions(availableRegions);
    } catch (err) {
      setError('Failed to load regions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedRegion) return;
    
    onBoundarySelect(
      selectedRegion.geometry,
      `${selectedRegion.name} Analysis`
    );
  };

  return (
    <div className="space-y-4 p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Analyze Administrative Region</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <select 
            value={country} 
            onChange={e => {
              setCountry(e.target.value);
              setLevel(null);
              setSelectedRegion(null);
              setRegions([]);
            }}
            className="w-full p-2 border rounded"
            disabled={loading}
          >
            <option value="">Select Country...</option>
            <option value="US">United States</option>
            <option value="GB">United Kingdom</option>
            <option value="KE">Kenya</option>
            <option value="IN">India</option>
            <option value="BR">Brazil</option>
          </select>
        </div>

        {country && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Administrative Level
            </label>
            <select
              value={level ?? ''}
              onChange={e => {
                const newLevel = Number(e.target.value);
                setLevel(newLevel);
                setSelectedRegion(null);
                setRegions([]); // Clear regions when level changes
              }}
              className="w-full p-2 border rounded"
              disabled={loading}
            >
              <option value="">Select Level...</option>
              {getAvailableLevels(country).map(lvl => (
                <option key={lvl} value={lvl}>
                  {ADMIN_LEVELS[lvl]}
                </option>
              ))}
            </select>
          </div>
        )}

        {level !== null && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select {ADMIN_LEVELS[level]}
            </label>
            <select
              value={selectedRegion?.id || ''}
              onChange={e => {
                const region = regions.find(r => r.id === e.target.value);
                setSelectedRegion(region || null);
              }}
              className="w-full p-2 border rounded"
              disabled={loading}
            >
              <option value="">Select {ADMIN_LEVELS[level]}...</option>
              {regions.map(region => (
                <option key={region.id} value={region.id}>
                  {region.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedRegion && (
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className={`w-full p-2 rounded text-white ${
              loading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {loading ? 'Analyzing...' : 'Analyze Region'}
          </button>
        )}

        {error && (
          <div className="text-red-500 text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}