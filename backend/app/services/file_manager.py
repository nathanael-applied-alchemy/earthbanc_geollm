# backend/app/services/file_manager.py
import os
import requests
from typing import Optional, Tuple
from pathlib import Path
import logging
from fastapi import HTTPException
from dotenv import load_dotenv
from tqdm import tqdm
import netrc
import time



load_dotenv()

logger = logging.getLogger(__name__)

class LGRIPFileManager:
    def __init__(self):
        self.local_dir = Path("app/data/lgrip30_files")
        self.nasa_username = os.getenv("NASA_EARTHDATA_USERNAME")
        self.nasa_password = os.getenv("NASA_EARTHDATA_PASSWORD")
        self.session = None
        
        print(self.nasa_username)
        print(self.nasa_password)

        # Ensure local directory exists
        self.local_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .netrc file for authentication
        self._setup_netrc()

    def _setup_netrc(self):
        """Setup .netrc file for NASA Earthdata authentication"""
        netrc_path = os.path.expanduser("~/.netrc")
        

        print(netrc_path)

        if not os.path.exists(netrc_path):
        
            print("Creating .netrc file")
            print(f"""machine urs.earthdata.nasa.gov login {self.nasa_username} password {self.nasa_password}
machine e4ftl01.cr.usgs.gov login {self.nasa_username} password {self.nasa_password}""")
            with open(netrc_path, 'w') as f:
                f.write(f"""machine urs.earthdata.nasa.gov login {self.nasa_username} password {self.nasa_password}
machine e4ftl01.cr.usgs.gov login {self.nasa_username} password {self.nasa_password}""")
            os.chmod(netrc_path, 0o600)
            logger.info("Created .netrc file for NASA Earthdata authentication")

    async def get_session(self) -> Optional[requests.Session]:
        """Create authenticated session for NASA Earthdata"""
        try:
            session = requests.Session()
            
            # Use .netrc authentication
            session.auth = (self.nasa_username, self.nasa_password)
            
            # Add required headers
            session.headers.update({
                'Accept': 'application/json',
                'User-Agent': 'geollm-backend/1.0'
            })
            
            self.session = session
            return session
                
        except Exception as e:
            logger.error(f"Error creating NASA Earthdata session: {str(e)}")
            return None

    async def get_file_path(self, tile_info: dict) -> Tuple[Optional[str], str]:
        """Check for file locally, then remotely."""
        filename = os.path.basename(tile_info['path'])
        local_path = self.local_dir / filename
        
        # Check local file first
        if local_path.exists():
            if local_path.stat().st_size > 0:
                return str(local_path), "local"
            else:
                local_path.unlink()
        
        # If not local, check remote
        if not self.session:
            self.session = await self.get_session()
            if not self.session:
                return None, "auth_failed"
        
        try:
            # Check if remote file exists
            head_response = self.session.head(tile_info['path'])
            if head_response.status_code == 200:
                # Try to download the file
                file_path = await self.download_file(tile_info)
                if file_path:
                    return file_path, "downloaded"
                return None, "download_failed"
            else:
                return None, f"remote_error_{head_response.status_code}"
                
        except Exception as e:
            logger.error(f"Error checking remote file: {str(e)}")
            return None, "remote_error"

    async def download_file(self, tile_info: dict) -> Optional[str]:
        """Download file from NASA Earthdata"""
        try:
            if not self.session:
                self.session = await self.get_session()
                if not self.session:
                    return None
                    
            filename = os.path.basename(tile_info['path'])
            local_path = self.local_dir / filename
            
            # Get file size first
            head_response = self.session.head(tile_info['path'])
            total_size = int(head_response.headers.get('content-length', 0))
            
            logger.info(f"Starting download of {filename} ({total_size/1024/1024:.1f} MB)")
            
            # Stream download with progress tracking
            with self.session.get(tile_info['path'], stream=True) as r:
                r.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                size = f.write(chunk)
                                pbar.update(size)
            
            # Verify file size after download
            if local_path.stat().st_size == total_size:
                logger.info(f"Successfully downloaded {filename}")
                return str(local_path)
            else:
                logger.error(f"Downloaded file size mismatch for {filename}")
                local_path.unlink()
                return None
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            if local_path.exists():
                local_path.unlink()
            return None


# https://e4ftl01.cr.usgs.gov//DP109/COMMUNITY/LGRIP30.001/2014.01.01/LGRIP30_2015_N00E30_001_2023014175240.tif?_ga=2.233075934.1710895569.1734132909-1600426111.1734132909
