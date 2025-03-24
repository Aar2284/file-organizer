import time
import os
import sys
import shutil
import logging
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.cloud import vision
from google.cloud import videointelligence_v1 as videointelligence
from google.cloud import speech
import pdfplumber
from mistralai import Mistral

# Configure logging with multiple handlers
logger = logging.getLogger('FileOrganizer')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler('file_organization.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Debug credentials before initializing clients
cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')
logger.info(f"GOOGLE_APPLICATION_CREDENTIALS: {cred_path}")
if os.path.exists(cred_path):
    with open(cred_path, 'r') as f:
        content = f.read()
        logger.info(f"Credentials file content: {repr(content[:50])}...")  # Truncate for brevity
else:
    logger.error(f"Credentials file not found at {cred_path}")

# Initialize Google clients
try:
    vision_client = vision.ImageAnnotatorClient()
    video_client = videointelligence.VideoIntelligenceServiceClient()
    speech_client = speech.SpeechClient()
    logger.info("Google clients initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google clients: {str(e)}")
    raise

# Initialize Mistral AI client
MISTRAL_API_KEY = "MISTRAL_API_KEY"
mistral_client = Mistral(api_key=MISTRAL_API_KEY)
