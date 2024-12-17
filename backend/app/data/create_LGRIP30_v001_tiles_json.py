import json
from datetime import datetime

def generate_LGRIP30_v001_tiles():
    tiles = {}
    
    # Generate for all latitudes (-80 to 80 in steps of 10)
    for lat in range(-80, 90, 10):
        # Generate for all longitudes (-180 to 170 in steps of 10)
        for lon in range(-180, 180, 10):
            # Determine N/S
            ns_prefix = 'N' if lat >= 0 else 'S'
            lat_str = f"{abs(lat):02d}"
            
            # Determine E/W
            ew_prefix = 'E' if lon >= 0 else 'W'
            lon_str = f"{abs(lon):02d}"
            
            # Create tile key
            tile_key = f"{ns_prefix}{lat_str}{ew_prefix}{lon_str}"
            
            # Create tile data with correct URL format
            tiles[tile_key] = {
                "path": f"https://e4ftl01.cr.usgs.gov//DP109/COMMUNITY/LGRIP30.001/2014.01.01/LGRIP30_2015_{ns_prefix}{lat_str}{ew_prefix}{lon_str}_001_2023014175240.tif",
                "bounds": {
                    "minx": lon,
                    "miny": lat,
                    "maxx": lon + 10,
                    "maxy": lat + 10
                },
                "last_updated": "2024-01-16",
                "file_size_gb": 2.3
            }
    
    # Create the full JSON structure
    data = {
        "metadata": {
            "description": "LGRIP30 v001 10-degree tile references",
            "version": "1.0",
            "date_updated": "2024-01-16",
            "coverage": "Global 10-degree tiles"
        },
        "tiles": tiles
    }
    
    # Create or overwrite the file
    with open('LGRIP30_v001_tiles.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    generate_LGRIP30_v001_tiles()