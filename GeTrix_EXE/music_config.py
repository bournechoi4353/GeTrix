# Auto-generated music configuration
# Created by fix_music.py

MIXER_CONFIG = {'frequency': 44100, 'size': -16, 'channels': 2, 'buffer': 4096}

def direct_play_music(file_path):
    """
    Direct music playback function that bypasses the music manager.
    Use this if the regular music playback is not working.
    """
    import pygame
    import os
    from pathlib import Path
    
    # Make sure pygame is initialized
    if not pygame.get_init():
        pygame.init()
    
    # Initialize mixer with working configuration
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    
    # Apply the working configuration
    if MIXER_CONFIG:
        pygame.mixer.init(**MIXER_CONFIG)
    else:
        pygame.mixer.init()
    
    # Resolve the file path
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        print(f"Error: Music file not found: {file_path}")
        return False
    
    # Play the music
    try:
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play(-1)  # Loop indefinitely
        return True
    except Exception as e:
        print(f"Error playing music: {e}")
        return False
