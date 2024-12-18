from shapely.geometry import shape, mapping
import ee
import geemap
import os
from datetime import datetime
import traceback
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import pickle
import rasterio
from rasterio.plot import reshape_as_image
from PIL import Image
import numpy as np
import logging
import asyncio
import traceback
import pyproj
from functools import partial
from shapely.ops import transform
from pathlib import Path



from google.oauth2 import service_account
from googleapiclient.discovery import build

# Dictionary to track task statuses
task_statuses = {}

logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "saved_pngs"

# Visualization configurations for different band types
visualizations = {
    'TrueColor': {
        'image': lambda sentinel: sentinel.select(['B4', 'B3', 'B2']),
        'vis_params': {
            'min': 0,
            'max': 3000,
            'bands': ['B4', 'B3', 'B2']
        }
    },
    'NDWI': {
        'image': lambda sentinel: sentinel.normalizedDifference(['B3', 'B8']),
        'vis_params': {
            'min': -1,
            'max': 1,
            'palette': ['red', 'yellow', 'green', 'cyan', 'blue']
        }
    },
    'AgriColor': {
        'image': lambda sentinel: sentinel.select(['B8', 'B4', 'B3']),
        'vis_params': {
            'min': 0,
            'max': 3000,
            'bands': ['B8', 'B4', 'B3']
        }
    },
    'MSAVI2': {
        'image': lambda sentinel: (
            sentinel.expression(
                '(2 * NIR + 1 - sqrt(pow(2 * NIR + 1, 2) - 8 * (NIR - RED))) / 2',
                {
                    'NIR': sentinel.select('B8'),
                    'RED': sentinel.select('B4')
                }
            )
        ),
        'vis_params': {
            'min': -1,
            'max': 1,
            'palette': ['red', 'yellow', 'green']
        }
    }
}

def calculate_area_in_sq_km(polygon_geojson):
    """Calculate the area of a GeoJSON polygon in square kilometers."""
    # Convert GeoJSON to Shapely geometry
    polygon = shape(polygon_geojson)
    
    # Get the centroid of the polygon for better accuracy
    centroid = polygon.centroid
    
    # Create a projection centered on the polygon's centroid
    proj = pyproj.Proj(
        proj='aea',  # Albers Equal Area projection
        lat_1=polygon.bounds[1],  # Southern parallel
        lat_2=polygon.bounds[3],  # Northern parallel
        lat_0=centroid.y,  # Latitude of origin
        lon_0=centroid.x,  # Longitude of origin
        datum='WGS84'
    )
    
    # Create transformer from WGS84 to the custom projection
    wgs84 = pyproj.Proj('EPSG:4326')  # WGS84
    project = partial(
        pyproj.transform,
        wgs84,
        proj
    )
    
    # Transform the polygon to the projected CRS
    polygon_projected = transform(project, polygon)
    
    # Calculate area in square meters and convert to square kilometers
    area_sq_km = polygon_projected.area / 1_000_000
    
    return area_sq_km


def get_drive_service():
    """Get Google Drive service using service account."""
    SERVICE_ACCOUNT_FILE = 'ee-nmiksis-7aa1d0ba5ab4.json'
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    
    return build('drive', 'v3', credentials=credentials)

# # Initialize Google Drive service
# def get_drive_service():
#     """Get or create Google Drive service."""
#     SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
#     creds = None
    
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
            
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'client_secret.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)

#     return build('drive', 'v3', credentials=creds)

async def find_and_download_file(file_name: str, folder_name: str, max_retries: int = 10) -> str:
    """Find and download a file from Google Drive."""
    service = get_drive_service()
    
    for attempt in range(max_retries):
        try:
            # Search for the folder
            folder_results = service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            if not folder_results.get('files'):
                await asyncio.sleep(5)
                continue
                
            folder_id = folder_results['files'][0]['id']
            
            # Search for the file in the folder
            file_results = service.files().list(
                q=f"name='{file_name}' and '{folder_id}' in parents",
                fields="files(id, name)"
            ).execute()
            
            if not file_results.get('files'):
                await asyncio.sleep(5)
                continue
                
            file_id = file_results['files'][0]['id']
            
            # Download the file
            output_path = OUTPUT_DIR / file_name
            request = service.files().get_media(fileId=file_id)
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                
            fh.seek(0)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(fh.read())
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            await asyncio.sleep(5)
            
    return None

def convert_tif_to_png(tif_path, output_dir="app/data/saved_pngs"):
    """Convert GeoTIFF to PNG and save it."""
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Generate output filename
        png_filename = os.path.basename(tif_path).replace('.tif', '.png')
        png_path = os.path.join(output_dir, png_filename)
        
        # Read the GeoTIFF
        with rasterio.open(tif_path) as src:
            # Read all bands and reshape for PIL
            image_array = src.read()
            image_array = reshape_as_image(image_array)
            
            # Normalize the data to 0-255 range
            image_array = ((image_array - image_array.min()) * (255.0 / (image_array.max() - image_array.min()))).astype(np.uint8)
            
            # Convert to PIL Image and save as PNG
            image = Image.fromarray(image_array)
            image.save(png_path)
            
        print(f"Converted {tif_path} to {png_path}")
        return png_path
        
    except Exception as e:
        print(f"Error converting {tif_path} to PNG: {str(e)}")
        return None

async def process_spectral_band(polygon_geojson, band_type):
    """Process a single spectral band and return the file path"""
    try:
        # Calculate area before proceeding
        area = calculate_area_in_sq_km(polygon_geojson)
        if area > 200:
            raise ValueError(f"Area too large: {area:.2f} km². Maximum allowed area is 200 km².")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


        credentials = service_account.Credentials.from_service_account_file(
            'ee-nmiksis-7aa1d0ba5ab4.json',
            scopes=['https://www.googleapis.com/auth/earthengine'])
        ee.Initialize(credentials)


        # ee.Initialize(project="ee-nmiksis")

        # Convert GeoJSON to Shapely geometry
        polygon = shape(polygon_geojson)
        # Get the bounding box of the polygon
        minx, miny, maxx, maxy = polygon.bounds
        region = ee.Geometry.Rectangle([minx, miny, maxx, maxy])

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Get the most recent cloud-free Sentinel-2 image
        sentinel = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                   .filterBounds(region)
                   .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                   .sort('CLOUDY_PIXEL_PERCENTAGE')
                   .first())

        # Get visualization config for the specific band
        vis_config = visualizations[band_type]
        
        folder_name = f"earthbanc_exports_{timestamp}_{band_type}"
        file_name = f'sentinel_{band_type.lower()}_{timestamp}.tif'
        
        # Apply the visualization configuration
        image = vis_config['image'](sentinel)
        image_rgb = image.visualize(**vis_config['vis_params'])
        
        task = ee.batch.Export.image.toDrive(
            image=image_rgb,
            description=f'sentinel_{band_type.lower()}_{timestamp}',
            folder=folder_name,
            scale=10,
            region=region,
            fileFormat='GeoTIFF',
            maxPixels=1e9
        )
        task.start()

        # Update task status
        task_statuses[band_type] = {
            'status': 'processing',
            'fileName': file_name
        }

        # Wait for task completion and process the result
        while True:
            status = task.status()
            if status['state'] == 'COMPLETED':
                task_statuses[band_type]['status'] = 'completed'
                
                # Download and convert the file
                tif_path = await find_and_download_file(file_name, folder_name)
                
                if tif_path:
                    png_path = convert_tif_to_png(tif_path)
                    if png_path:
                        return os.path.basename(png_path)
                break
            elif status['state'] == 'FAILED':
                task_statuses[band_type]['status'] = 'failed'
                break
            await asyncio.sleep(5)

        return None
    except Exception as e:
        logger.error(f"Error processing {band_type}: {str(e)}")
        task_statuses[band_type] = {'status': 'failed', 'error': str(e)}
        return None
