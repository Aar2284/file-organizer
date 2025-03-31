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
MISTRAL_API_KEY = "xj2ajSe3s2XzqJKM5lo9r8CyAhIfc3Mj"
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

class FileHandler(FileSystemEventHandler):
    """
    Handles file events in the inbox folder, categorizing and sub-categorizing
    files into Images, Videos, Audio, Documents, Archives, and Code using
    Google Cloud APIs and Mistral AI for intelligent subfolder naming.
    """
    FILE_CATEGORIES = {
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.md', '.pages', '.wps', '.tex', '.epub', '.csv', '.tsv', '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp', '.ico', '.psd', '.raw', '.heic', '.heif', '.ai', '.eps', '.exr', '.jp2'],
        'Videos': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.m4v', '.3gp', '.ogv', '.vob', '.ts', '.rm', '.rmvb', '.divx'],
        'Audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma', '.m4a', '.aiff', '.alac', '.ape', '.opus', '.mid', '.midi', '.amr'],
        'Archives': ['.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz', '.iso', '.cab', '.arj', '.z', '.tgz', '.tbz2', '.ace'],
        'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.ts', '.sh', '.bat', '.pl', '.swift', '.kt', '.lua', '.sql', '.r', '.asm', '.vbs']
    }

    def __init__(self, destination_path):
        self.destination_path = destination_path
        for category in list(self.FILE_CATEGORIES.keys()) + ['Others']:
            os.makedirs(os.path.join(destination_path, category), exist_ok=True)
    def get_category(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        for category, extensions in self.FILE_CATEGORIES.items():
            if ext in extensions:
                return category
        return 'Others'

    def analyze_image(self, file_path):
        try:
            with open(file_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = vision_client.label_detection(image=image)
            labels = [label.description for label in response.label_annotations[:3]]
            logger.info(f"Image labels for {file_path}: {labels}")
            return labels
        except Exception as e:
            logger.error(f"Vision API error for {file_path}: {str(e)}")
            return ["unknown"]

    def analyze_video(self, file_path):
        try:
            with open(file_path, 'rb') as video_file:
                content = video_file.read()
            operation = video_client.annotate_video(
                request={
                    'input_content': content,
                    'features': [videointelligence.Feature.LABEL_DETECTION]
                }
            )
            result = operation.result(timeout=120)
            labels = [label.entity.description for label in result.annotation_results[0].segment_label_annotations[:3]]
            logger.info(f"Video labels for {file_path}: {labels}")
            return labels
        except Exception as e:
            logger.error(f"Video Intelligence error for {file_path}: {str(e)}")
            return ["unknown"]

    def analyze_audio(self, file_path):
        try:
            with open(file_path, 'rb') as audio_file:
                content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=44100,
                language_code="en-US"
            )
            response = speech_client.recognize(config=config, audio=audio)
            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            logger.info(f"Audio transcript for {file_path}: {transcript[:50]}...")
            return [transcript[:100]]
        except Exception as e:
            logger.error(f"Speech-to-Text error for {file_path}: {str(e)}")
            return ["unknown"]

    def analyze_document(self, file_path):
        try:
            if file_path.endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    text = " ".join(page.extract_text() or "" for page in pdf.pages)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            logger.info(f"Document text excerpt for {file_path}: {text[:50]}...")
            return [text[:100]]
        except Exception as e:
            logger.error(f"Document analysis error for {file_path}: {str(e)}")
            return ["unknown"]

    def suggest_subfolder(self, category, content):
        existing_folders = [f.name for f in os.scandir(os.path.join(self.destination_path, category)) if f.is_dir()]
        prompt = f"Given the content: {', '.join(content)}, and existing subfolders: {', '.join(existing_folders) or 'none'}, suggest a single-word or short-phrase subfolder name (max 20 characters) within {category}. Return only the name, no explanation. Use an existing folder if it fits, otherwise a new one."

        try:
            response = mistral_client.chat.complete(
                model="mistral-tiny",
                messages=[{"role": "user", "content": prompt}]
            )
            subfolder = response.choices[0].message.content.strip().lower().replace(" ", "_")
            subfolder = subfolder[:20]
            subfolder = ''.join(c for c in subfolder if c.isalnum() or c == '_')
            if not subfolder:
                subfolder = "misc"
            logger.info(f"Mistral suggested subfolder: {subfolder}")
            return subfolder
        except Exception as e:
            logger.error(f"Mistral AI error: {str(e)}")
            return "misc"

    def generate_metadata(self, original_path, category, dest_path, subfolder=None):
        metadata = {
            'original_path': original_path,
            'category': category,
            'destination_path': dest_path,
            'timestamp': datetime.now().isoformat()
        }
        if subfolder:
            metadata['subfolder'] = subfolder
        return metadata

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            logger.info(f"New file detected: {file_path}")
            time.sleep(1)

            category = self.get_category(file_path)
            dest_folder = os.path.join(self.destination_path, category)

            if category == 'Images':
                content = self.analyze_image(file_path)
                subfolder = self.suggest_subfolder(category, content)
            elif category == 'Videos':
                content = self.analyze_video(file_path)
                subfolder = self.suggest_subfolder(category, content)
            elif category == 'Audio':
                content = self.analyze_audio(file_path)
                subfolder = self.suggest_subfolder(category, content)
            elif category == 'Documents':
                content = self.analyze_document(file_path)
                subfolder = self.suggest_subfolder(category, content)
            else:
                subfolder = None

            if subfolder:
                dest_folder = os.path.join(dest_folder, subfolder)
                os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, os.path.basename(file_path))

            try:
                shutil.move(file_path, dest_path)
                logger.info(f"Moved to: {dest_path}")

                metadata = self.generate_metadata(file_path, category, dest_path, subfolder)
                metadata_path = dest_path + '.metadata.json'
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=4)
                logger.info(f"Metadata generated: {metadata_path}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

def start_monitoring():
    watch_path = "./inbox"
    destination_path = "./destination"
    os.makedirs(watch_path, exist_ok=True)
    os.makedirs(destination_path, exist_ok=True)

    event_handler = FileHandler(destination_path)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=False)
    observer.start()

    logger.info(f"Started monitoring {watch_path}. Drop files to test!")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Monitoring stopped.")
    observer.join()

if __name__ == "__main__":
    start_monitoring()
