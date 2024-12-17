interface OSMElement {
  type: string;
  id: number;
  lat?: number;
  lon?: number;
  nodes?: number[];
  members?: Array<{
    type: string;
    ref: number;
    role: string;
  }>;
  tags?: {
    name?: string;
    'admin_level'?: string;
    boundary?: string;
    [key: string]: string | undefined;
  };
}

interface OSMResponse {
  elements: OSMElement[];
}

function osmToGeoJSON(osmData: OSMResponse): GeoJSON.FeatureCollection {
  // Create lookup tables for nodes and ways
  const nodes = new Map<number, [number, number]>();
  const ways = new Map<number, number[]>();
  const relations = new Map<number, OSMElement>();
  
  // First pass: organize elements by type
  osmData.elements.forEach(element => {
    switch (element.type) {
      case 'node':
        if (element.lat && element.lon) {
          nodes.set(element.id, [element.lon, element.lat]);
        }
        break;
      case 'way':
        if (element.nodes) {
          ways.set(element.id, element.nodes);
        }
        break;
      case 'relation':
        if (element.tags?.boundary === 'administrative') {
          relations.set(element.id, element);
        }
        break;
    }
  });

  // Convert relations to features
  const features: GeoJSON.Feature[] = [];
  
  relations.forEach(relation => {
    if (!relation.members) return;

    // Collect all ways that form the boundary
    const rings: number[][] = [];
    let currentRing: number[] = [];
    
    relation.members
      .filter(member => member.type === 'way')
      .forEach(member => {
        const wayNodes = ways.get(member.ref);
        if (!wayNodes) return;
        
        // Convert way nodes to coordinates
        const coordinates = wayNodes
          .map(nodeId => nodes.get(nodeId))
          .filter((coord): coord is [number, number] => !!coord);
          
        if (coordinates.length > 0) {
          currentRing.push(...coordinates.map(coord => coord));
        }
    });

    // Only add valid rings
    if (currentRing.length > 3) {
      // Close the ring if needed
      if (currentRing[0] !== currentRing[currentRing.length - 1]) {
        currentRing.push(currentRing[0]);
      }
      rings.push(currentRing);
    }

    // Create the feature
    if (rings.length > 0) {
      features.push({
        type: 'Feature',
        properties: {
          name: relation.tags?.name || 'Unknown',
          admin_level: relation.tags?.admin_level || '',
          id: relation.id.toString(),
          type: 'boundary'
        },
        geometry: {
          type: 'Polygon',
          coordinates: rings
        }
      });
    }
  });

  return {
    type: 'FeatureCollection',
    features
  };
}

export const ADMIN_LEVELS = {
  0: 'Country',
  1: 'State/Province', 
  2: 'County/District',
  3: 'Municipality',
  4: 'Locality'
} as const;

export const getBoundaryData = async (
  countryCode: string,
  adminLevel: number
): Promise<GeoJSON.FeatureCollection> => {
  try {
    // Use Natural Earth for state level (adminLevel === 1)
    if (adminLevel === 1) {
      const url = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson';
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch boundary data: ${response.statusText}`);
      }
      const data = await response.json();
      
      // Filter for specific country
      return {
        type: 'FeatureCollection',
        features: data.features.filter(f => 
          f.properties.adm0_a3 === countryCode || 
          f.properties.iso_a2 === countryCode
        ).map(f => ({
          ...f,
          properties: {
            ...f.properties,
            id: f.properties.woe_id || f.properties.adm1_code,
            name: f.properties.name || f.properties.gn_name || 'Unknown'
          }
        }))
      };
    }
    
    // Use Overpass for county/district level (adminLevel === 2)
    const query = `
      [out:json][timeout:25];
      area["ISO3166-1"="${countryCode}"]->.country;
      (
        rel(area.country)["admin_level"="${adminLevel+2}"]["boundary"="administrative"];
      );
      out body;
      >;
      out skel qt;
    `;
    
    const response = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: query
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch OSM data: ${response.statusText}`);
    }
    
    const osmData = await response.json();
    return osmToGeoJSON(osmData);
  } catch (error) {
    console.error('Error fetching boundary data:', error);
    throw error;
  }
};

// Cache management
const boundaryCache = new Map<string, GeoJSON.FeatureCollection>();

export const getCachedBoundary = async (
  countryCode: string,
  adminLevel: number
): Promise<GeoJSON.FeatureCollection> => {
  const cacheKey = `${countryCode}-${adminLevel}`;
  
  if (boundaryCache.has(cacheKey)) {
    return boundaryCache.get(cacheKey)!;
  }
  
  const data = await getBoundaryData(countryCode, adminLevel);
  boundaryCache.set(cacheKey, data);
  return data;
};
