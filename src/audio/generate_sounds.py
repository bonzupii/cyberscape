import numpy as np
from scipy.io import wavfile
import os

def generate_completion_sound():
    """Generate a subtle completion sound effect."""
    # Parameters
    sample_rate = 44100
    duration = 0.2  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Generate a soft "click" sound
    frequency = 1000
    decay = np.exp(-10 * t)
    signal = 0.5 * np.sin(2 * np.pi * frequency * t) * decay
    
    # Add a subtle high-frequency component
    high_freq = 2000
    high_signal = 0.2 * np.sin(2 * np.pi * high_freq * t) * decay
    
    # Combine signals
    final_signal = signal + high_signal
    
    # Normalize
    final_signal = final_signal / np.max(np.abs(final_signal))
    
    # Convert to 16-bit PCM
    final_signal = (final_signal * 32767).astype(np.int16)
    
    # Save to file
    wavfile.write('sounds/completion.wav', sample_rate, final_signal)

def generate_suggestion_sound():
    """Generate a subtle suggestion sound effect."""
    # Parameters
    sample_rate = 44100
    duration = 0.3  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Generate a soft "pop" sound
    frequency = 800
    decay = np.exp(-5 * t)
    signal = 0.4 * np.sin(2 * np.pi * frequency * t) * decay
    
    # Add a subtle sweep
    sweep_freq = np.linspace(1200, 800, len(t))
    sweep_signal = 0.2 * np.sin(2 * np.pi * sweep_freq * t) * decay
    
    # Combine signals
    final_signal = signal + sweep_signal
    
    # Normalize
    final_signal = final_signal / np.max(np.abs(final_signal))
    
    # Convert to 16-bit PCM
    final_signal = (final_signal * 32767).astype(np.int16)
    
    # Save to file
    wavfile.write('sounds/suggestion.wav', sample_rate, final_signal)

def main():
    """Generate all sound effects."""
    # Create sounds directory if it doesn't exist
    os.makedirs('sounds', exist_ok=True)
    
    # Generate sounds
    generate_completion_sound()
    generate_suggestion_sound()
    
    print("Sound effects generated successfully!")

if __name__ == '__main__':
    main() 