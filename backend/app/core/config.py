import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATA_DIR = Path(__file__).parent.parent / 'data'
    LGRIP_DATA_DIR = DATA_DIR / 'LGRIP30'
    SENTINEL_DATA_DIR = DATA_DIR / 'sentinel'
    CARBON_DATA_DIR = DATA_DIR / 'carbon'
    OVERPASS_DATA_DIR = DATA_DIR / 'overpass'
    NATURAL_EARTH_DATA_DIR = DATA_DIR / 'natural_earth'

settings = Settings()

