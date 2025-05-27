#!/usr/bin/env python3
"""
Sound file downloader and processor for Cyberscape: Digital Dread
Downloads and processes sound files from various sources.
"""

import os
import sys
import json
import logging
import requests
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# Sound file sources and URLs
SOUND_SOURCES = {
    # Ambient sounds
    "ambient/ambient_hum.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2875/2875-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 10.0
    },
    
    # Corruption sounds
    "corruption/whispering_voices.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2876/2876-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 4.0
    },
    
    # Entity sounds
    "entity/dr_voss_typing.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2877/2877-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 2.0
    },
    
    # System sounds
    "system/error.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2878/2878-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 0.5
    },
    "system/keypress.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2879/2879-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 0.1
    },
    "system/typing_normal.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2880/2880-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 1.0
    },
    "system/glitch.wav": {
        "url": "https://assets.mixkit.co/active_storage/sfx/2881/2881-preview.mp3",
        "source": "Mixkit",
        "license": "Free License",
        "duration": 0.2
    }
}

def download_file(url, output_path, force=False):
    """Download a file from URL to the specified path."""
    if os.path.exists(output_path) and not force:
        logger.info(f"File already exists: {output_path}")
        return True
        
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False

def convert_to_wav(input_path, output_path, force=False):
    """Convert audio file to WAV format using ffmpeg."""
    if os.path.exists(output_path) and not force:
        logger.info(f"WAV file already exists: {output_path}")
        return True
        
    try:
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output files
            '-i', input_path,
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '44100',  # 44.1kHz sample rate
            '-ac', '1',  # mono
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting {input_path}: {e.stderr.decode()}")
        return False

def process_sound(sound_path, sound_info, force=False):
    """Process a single sound file: download and convert to WAV."""
    logger.info(f"Processing {sound_path}...")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(sound_path), exist_ok=True)
    
    # Download the file
    temp_path = f"{sound_path}.temp"
    if not download_file(sound_info['url'], temp_path, force):
        return False
        
    # Convert to WAV
    if not convert_to_wav(temp_path, sound_path, force):
        os.remove(temp_path)
        return False
        
    # Clean up temp file
    os.remove(temp_path)
    
    # Save metadata
    metadata_path = f"{sound_path}.json"
    with open(metadata_path, 'w') as f:
        json.dump(sound_info, f, indent=2)
    
    logger.info(f"Successfully processed {sound_path}")
    return True

def main():
    """Main function to process all sound files."""
    force = '--force' in sys.argv
    
    # Process each sound file
    success_count = 0
    total_count = len(SOUND_SOURCES)
    
    for sound_path, sound_info in SOUND_SOURCES.items():
        if process_sound(sound_path, sound_info, force):
            success_count += 1
            
    logger.info(f"Processed {success_count}/{total_count} sound files successfully")

if __name__ == "__main__":
    main() 