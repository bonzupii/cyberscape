#!/usr/bin/env python3
"""
Sound file evaluator for Cyberscape: Digital Dread
Plays each sound file and logs user responses.
"""

import os
import sys
import json
import logging
import pygame
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pygame mixer
pygame.mixer.init()

def get_sound_files() -> List[Tuple[str, Path]]:
    """Get all WAV files in the audio directory and its subdirectories."""
    sound_files = []
    base_dir = Path(__file__).parent
    
    for category_dir in base_dir.iterdir():
        if category_dir.is_dir():
            for file in category_dir.glob("*.wav"):
                # Skip temp files
                if not file.name.startswith("temp_"):
                    # Verify file exists and has content
                    if file.stat().st_size > 0:
                        sound_files.append((category_dir.name, file))
                    else:
                        logger.warning(f"Skipping empty file: {file}")
    
    return sorted(sound_files)

def play_sound(file_path: Path) -> bool:
    """Play a sound file and wait for it to finish."""
    try:
        # Verify file exists and has content
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
            
        if file_path.stat().st_size == 0:
            logger.error(f"File is empty: {file_path}")
            return False
            
        # Try to load and play the sound
        sound = pygame.mixer.Sound(str(file_path))
        channel = sound.play()
        
        # Wait for sound to finish playing
        while channel.get_busy():
            pygame.time.wait(100)
            
        return True
    except Exception as e:
        logger.error(f"Error playing {file_path}: {str(e)}")
        return False

def get_user_response() -> str:
    """Get user response (y/n) for a sound file."""
    while True:
        response = input("Is this sound suitable? (y/n/q to quit): ").lower()
        if response in ['y', 'n', 'q']:
            return response
        print("Please enter 'y', 'n', or 'q'")

def log_response(category: str, filename: str, response: str, log_file: Path) -> None:
    """Log the user's response to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} | {category}/{filename} | {response}\n")

def main():
    """Main function to play and evaluate sound files."""
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(__file__).parent / f"sound_evaluation_{timestamp}.txt"
    
    # Write header to log file
    with open(log_file, 'w') as f:
        f.write("Timestamp | Sound File | Response\n")
        f.write("-" * 50 + "\n")
    
    # Get all sound files
    sound_files = get_sound_files()
    total_files = len(sound_files)
    
    if total_files == 0:
        print("No valid sound files found!")
        return
        
    print(f"\nFound {total_files} sound files to evaluate.")
    print("Press Enter to start...")
    input()
    
    for i, (category, file_path) in enumerate(sound_files, 1):
        print(f"\n[{i}/{total_files}] Playing: {category}/{file_path.name}")
        
        if play_sound(file_path):
            response = get_user_response()
            if response == 'q':
                print("\nEvaluation stopped by user.")
                break
            
            log_response(category, file_path.name, response, log_file)
            print(f"Response logged: {response}")
        else:
            print("Skipping to next file...")
    
    print(f"\nEvaluation complete. Results logged to: {log_file}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nEvaluation stopped by user.")
    finally:
        pygame.mixer.quit() 