import os
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "SiteGuard AI")
    
    # Storage paths (relative to project root)
    VIDEO_INPUT_DIR: str = os.getenv("VIDEO_INPUT_DIR", "data/videos")
    VIDEO_OUTPUT_DIR: str = os.getenv("VIDEO_OUTPUT_DIR", "data/outputs")
    
    # Safety Engine configurations
    YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolo11n.pt")

settings = Settings()
