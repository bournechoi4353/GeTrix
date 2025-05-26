import os
import pygame
import random
import sys
from pathlib import Path
import urllib.request
import shutil
import json

class MusicManager:
    """
    Music Manager for the Tetris game.
    Handles loading, playing, and managing music tracks for different game modes.
    """
    
    def __init__(self):
        """Initialize the music manager"""
        # Ensure pygame mixer is initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                print("Pygame mixer initialized successfully")
            except Exception as e:
                print(f"Error initializing pygame mixer: {e}")
            
        # Set default volume
        pygame.mixer.music.set_volume(0.5)
        
        # Create music directories if they don't exist
        self.music_dir = Path("music")
        self.music_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different game modes
        self.menu_music_dir = self.music_dir / "menu"
        self.standard_music_dir = self.music_dir / "standard"
        self.crazy_music_dir = self.music_dir / "crazy"
        self.startup_music_dir = self.music_dir / "startup"
        
        self.menu_music_dir.mkdir(exist_ok=True)
        self.standard_music_dir.mkdir(exist_ok=True)
        self.crazy_music_dir.mkdir(exist_ok=True)
        self.startup_music_dir.mkdir(exist_ok=True)
        
        # Create sounds directory structure if it doesn't exist
        self.sounds_dir = Path("sounds")
        self.sounds_dir.mkdir(exist_ok=True)
        
        # Create sound effect directories for different types
        self.block_land_dir = self.sounds_dir / "block_land"
        self.line_clear_dir = self.sounds_dir / "line_clear"
        self.level_up_dir = self.sounds_dir / "level_up"
        self.game_over_dir = self.sounds_dir / "game_over"
        
        self.block_land_dir.mkdir(exist_ok=True)
        self.line_clear_dir.mkdir(exist_ok=True)
        self.level_up_dir.mkdir(exist_ok=True)
        self.game_over_dir.mkdir(exist_ok=True)
        
        # Create custom sounds directory
        self.custom_sounds_dir = self.sounds_dir / "custom"
        self.custom_sounds_dir.mkdir(exist_ok=True)
        
        # Set up sound packs configuration file
        self.sound_packs_config = self.sounds_dir / "sound_packs.json"
        
        # Set default active sound pack
        self.active_sound_pack = "default"
        
        # Sound effects lists for each type
        self.block_land_sounds = []
        self.line_clear_sounds = []
        self.level_up_sounds = []
        self.game_over_sounds = []
        
        # Track lists for each mode
        self.menu_tracks = []
        self.standard_tracks = []
        self.crazy_tracks = []
        
        # Sound effects dictionary
        self.sound_effects = {}
        
        # Sound effect volume - increased for better audibility
        self.sound_volume = 1.0
        
        # Current state
        self.current_mode = None
        self.current_track = None
        self.is_playing = False
        self.is_paused = False
        
        # Load available tracks
        self.refresh_track_lists()
        
        # Load sound effects
        self.load_sound_effects()
    
    def refresh_track_lists(self):
        """Refresh the lists of available music tracks"""
        # Clear existing track lists
        self.menu_tracks = []
        self.standard_tracks = []
        self.crazy_tracks = []
        self.startup_tracks = []
        
        # Load tracks from each directory
        print("Refreshing music track lists...")
        self._load_tracks_from_dir(self.menu_music_dir, self.menu_tracks)
        self._load_tracks_from_dir(self.standard_music_dir, self.standard_tracks)
        self._load_tracks_from_dir(self.crazy_music_dir, self.crazy_tracks)
        self._load_tracks_from_dir(self.startup_music_dir, self.startup_tracks)
        
        # Print summary of loaded tracks
        print(f"Loaded {len(self.menu_tracks)} menu tracks")
        print(f"Loaded {len(self.standard_tracks)} standard tracks")
        print(f"Loaded {len(self.crazy_tracks)} crazy tracks")
        print(f"Loaded {len(self.startup_tracks)} startup tracks")
    
    def _load_tracks_from_dir(self, directory, track_list):
        """Load music tracks from a directory into a track list"""
        if not directory.exists():
            print(f"Music directory not found: {directory}")
            return
            
        print(f"Loading tracks from: {directory}")
        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() in ['.mp3', '.ogg', '.wav']:
                track_list.append(str(file))
                print(f"  Added track: {file.name}")
    
    def play_startup_music(self):
        """
        Play music for the startup animation
        
        Returns:
            bool: True if startup music was found and played, False otherwise
        """
        # First try to play the specific uploaded file
        specific_track = self.startup_music_dir / "Intro Pulse.mp3"
        
        print(f"Attempting to play startup music: {specific_track}")
        print(f"File exists: {specific_track.exists()}")
        
        # Try direct play method on Windows if available
        if sys.platform.startswith('win') and 'DIRECT_MUSIC_PLAY_AVAILABLE' in globals() and globals()['DIRECT_MUSIC_PLAY_AVAILABLE']:
            try:
                from music_config import direct_play_music
                print("Using direct play method for Windows")
                if direct_play_music(specific_track):
                    self.is_playing = True
                    self.is_paused = False
                    self.current_mode = 'startup'
                    return True
                # If direct play failed, continue with normal method
            except ImportError:
                print("Direct play module not available, using standard method")
        
        # Standard method
        if specific_track.exists():
            try:
                print(f"Loading startup music: {specific_track}")
                pygame.mixer.music.load(str(specific_track))
                pygame.mixer.music.play(-1)  # Loop indefinitely until player continues
                self.is_playing = True
                self.is_paused = False
                self.current_mode = 'startup'
                return True
            except pygame.error as e:
                print(f"Error playing specific startup music: {e}")
                # Fall through to try other tracks
        
        # If specific track failed or doesn't exist, try other tracks
        if not self.startup_tracks:
            print("No startup tracks available")
            return False
            
        # Choose a random track from startup tracks
        startup_track = random.choice(self.startup_tracks)
        print(f"Trying alternative startup track: {startup_track}")
        
        # Try direct play method on Windows if available
        if sys.platform.startswith('win') and 'DIRECT_MUSIC_PLAY_AVAILABLE' in globals() and globals()['DIRECT_MUSIC_PLAY_AVAILABLE']:
            try:
                from music_config import direct_play_music
                print("Using direct play method for alternative track on Windows")
                if direct_play_music(startup_track):
                    self.is_playing = True
                    self.is_paused = False
                    self.current_mode = 'startup'
                    print("Alternative startup track playing successfully via direct play")
                    return True
                # If direct play failed, continue with normal method
            except ImportError:
                print("Direct play module not available for alternative track, using standard method")
        
        # Standard method
        try:
            pygame.mixer.music.load(startup_track)
            pygame.mixer.music.play(-1)  # Loop indefinitely until player continues
            self.is_playing = True
            self.is_paused = False
            print("Alternative startup track playing successfully")
            self.current_mode = 'startup'
            return True
        except pygame.error as e:
            print(f"Error playing startup music: {e}")
            return False
    
    def play_music_for_mode(self, mode, force_restart=False):
        """
        Start playing music appropriate for the given game mode
        
        Args:
            mode: The game mode ('menu', 'standard', 'crazy', 'startup')
            force_restart: If True, restart music even if already playing in this mode
        """
        if mode == self.current_mode and self.is_playing and not force_restart:
            return
            
        self.current_mode = mode
        print(f"Playing music for mode: {mode}")
        
        # Select track list based on mode
        if mode == 'menu':
            tracks = self.menu_tracks
        elif mode == 'crazy':
            tracks = self.crazy_tracks
        elif mode == 'startup':
            tracks = self.startup_tracks
        else:  # standard, dual, etc.
            tracks = self.standard_tracks
            
        # If no tracks available for this mode, stop music
        if not tracks:
            self.stop_music()
            print(f"No tracks available for {mode} mode")
            return
            
        # Choose a random track
        self.current_track = random.choice(tracks)
        print(f"Selected track for {mode} mode: {self.current_track}")
        
        # Try direct play method on Windows if available
        if sys.platform.startswith('win') and 'DIRECT_MUSIC_PLAY_AVAILABLE' in globals() and globals()['DIRECT_MUSIC_PLAY_AVAILABLE']:
            try:
                from music_config import direct_play_music
                print(f"Using direct play method for {mode} mode on Windows")
                if direct_play_music(self.current_track):
                    self.is_playing = True
                    self.is_paused = False
                    print(f"Music for {mode} mode playing successfully via direct play")
                    return
                # If direct play failed, continue with normal method
                print("Direct play failed, falling back to standard method")
            except ImportError:
                print("Direct play module not available, using standard method")
        
        # Standard method
        try:
            pygame.mixer.music.load(self.current_track)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.is_playing = True
            self.is_paused = False
            print(f"Music for {mode} mode playing successfully")
        except pygame.error as e:
            print(f"Error playing music: {e}")
            self.is_playing = False
    
    def stop_music(self):
        """Stop the currently playing music"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
    
    def pause_music(self):
        """Pause the currently playing music"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
    
    def unpause_music(self):
        """Unpause the music if it's paused"""
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
    
    def set_volume(self, volume):
        """
        Set the music volume
        
        Args:
            volume: Volume level from 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        pygame.mixer.music.set_volume(volume)
    
    def set_sound_volume(self, volume):
        """
        Set the sound effects volume
        
        Args:
            volume: Volume level from 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        self.sound_volume = volume
        
        # Update volume for all loaded sound effects
        for sound in self.sound_effects.values():
            if sound:
                sound.set_volume(volume)
    
    def next_track(self):
        """Play the next track for the current mode"""
        if not self.current_mode:
            return
            
        self.play_music_for_mode(self.current_mode, force_restart=True)
    
    def get_upload_instructions(self):
        """Return instructions for uploading music files"""
        instructions = f"""
        Music Upload Instructions:
        
        1. Place your music files (.mp3, .ogg, or .wav) in the appropriate directory:
           - Menu music: {self.menu_music_dir}
           - Standard game music: {self.standard_music_dir}
           - Crazy mode music: {self.crazy_music_dir}
           
        2. The game will automatically detect and play your music files.
        
        3. Music will loop continuously during gameplay.
        
        4. You can add or remove music files while the game is closed.
        """
        return instructions
    
    def create_example_readme(self):
        """Create a README file with instructions in the music directory"""
        readme_path = self.music_dir / "README.txt"
        
        with open(readme_path, 'w') as f:
            f.write("""TETRIS GAME MUSIC INSTRUCTIONS
            
This directory contains music for the Tetris game.

Directory Structure:
- music/menu/: Music that plays on the menu screens
- music/standard/: Music that plays during standard gameplay
- music/crazy/: Music that plays during crazy mode

Supported File Formats:
- MP3 (.mp3)
- OGG Vorbis (.ogg)
- WAV (.wav)

How to Add Music:
1. Simply place your music files in the appropriate directory
2. Restart the game to detect new music
3. The game will randomly select and play tracks from each directory

Tips:
- For the best experience, use music that loops well
- Keep file sizes reasonable for better performance
- The game will automatically adjust volume through the settings menu
            """)
        
        return str(readme_path)
        
    def create_sounds_readme(self):
        """Create a README file with instructions in the sounds directory"""
        readme_path = self.sounds_dir / "README.txt"
        
        with open(readme_path, 'w') as f:
            f.write("""TETRIS GAME SOUND EFFECTS INSTRUCTIONS
            
This directory contains sound effects for the Tetris game.

Supported Sound Effects:
- block_land.wav: Plays when a block lands on the ground
- line_clear.wav: Plays when a line is cleared
- level_up.wav: Plays when the player levels up
- game_over.wav: Plays when the game ends

Supported File Formats:
- MP3 (.mp3)
- OGG Vorbis (.ogg)
- WAV (.wav)

How to Add Custom Sound Effects:
1. Simply replace the existing files with your own
2. Make sure to use the same filenames
3. Restart the game to use your custom sounds
            """)
        
        return str(readme_path)


    def load_sound_effects(self):
        """Load sound effects from the sounds directory"""
        print("\n[DEBUG] Loading sound effects...")
        # Clear existing sound lists
        self.block_land_sounds = []
        self.line_clear_sounds = []
        self.level_up_sounds = []
        self.game_over_sounds = []
        
        # Clear existing sound effects dictionary
        self.sound_effects = {}
        
        print(f"[DEBUG] Block land directory: {self.block_land_dir}")
        print(f"[DEBUG] Line clear directory: {self.line_clear_dir}")
        print(f"[DEBUG] Level up directory: {self.level_up_dir}")
        print(f"[DEBUG] Game over directory: {self.game_over_dir}")
        
        # Load block land sounds
        for sound_file in self.block_land_dir.glob('*.wav'):
            try:
                self.block_land_sounds.append(str(sound_file))
                print(f"Found block_land sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.block_land_dir.glob('*.mp3'):
            try:
                self.block_land_sounds.append(str(sound_file))
                print(f"Found block_land sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.block_land_dir.glob('*.ogg'):
            try:
                self.block_land_sounds.append(str(sound_file))
                print(f"Found block_land sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
        
        # Load line clear sounds
        for sound_file in self.line_clear_dir.glob('*.wav'):
            try:
                self.line_clear_sounds.append(str(sound_file))
                print(f"Found line_clear sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.line_clear_dir.glob('*.mp3'):
            try:
                self.line_clear_sounds.append(str(sound_file))
                print(f"Found line_clear sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.line_clear_dir.glob('*.ogg'):
            try:
                self.line_clear_sounds.append(str(sound_file))
                print(f"Found line_clear sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
        
        # Load level up sounds
        for sound_file in self.level_up_dir.glob('*.wav'):
            try:
                self.level_up_sounds.append(str(sound_file))
                print(f"Found level_up sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.level_up_dir.glob('*.mp3'):
            try:
                self.level_up_sounds.append(str(sound_file))
                print(f"Found level_up sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.level_up_dir.glob('*.ogg'):
            try:
                self.level_up_sounds.append(str(sound_file))
                print(f"Found level_up sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
        
        # Load game over sounds
        for sound_file in self.game_over_dir.glob('*.wav'):
            try:
                self.game_over_sounds.append(str(sound_file))
                print(f"Found game_over sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.game_over_dir.glob('*.mp3'):
            try:
                self.game_over_sounds.append(str(sound_file))
                print(f"Found game_over sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
                
        for sound_file in self.game_over_dir.glob('*.ogg'):
            try:
                self.game_over_sounds.append(str(sound_file))
                print(f"Found game_over sound: {sound_file.name}")
            except Exception as e:
                print(f"Error loading sound: {e}")
        
        # Create default silent sounds if no sounds are found
        if not self.block_land_sounds:
            try:
                buffer = bytearray(44100 // 10)
                self.sound_effects['block_land'] = pygame.mixer.Sound(buffer=buffer)
                print("Created silent fallback for block_land")
            except Exception as e:
                print(f"Error creating silent fallback: {e}")
        
        if not self.line_clear_sounds:
            try:
                buffer = bytearray(44100 // 10)
                self.sound_effects['line_clear'] = pygame.mixer.Sound(buffer=buffer)
                print("Created silent fallback for line_clear")
            except Exception as e:
                print(f"Error creating silent fallback: {e}")
        
        if not self.level_up_sounds:
            try:
                buffer = bytearray(44100 // 10)
                self.sound_effects['level_up'] = pygame.mixer.Sound(buffer=buffer)
                print("Created silent fallback for level_up")
            except Exception as e:
                print(f"Error creating silent fallback: {e}")
        
        if not self.game_over_sounds:
            try:
                buffer = bytearray(44100 // 10)
                self.sound_effects['game_over'] = pygame.mixer.Sound(buffer=buffer)
                print("Created silent fallback for game_over")
            except Exception as e:
                print(f"Error creating silent fallback: {e}")
    
    def play_sound(self, sound_name):
        """Play a sound effect by name"""
        print(f"\n[DEBUG] Attempting to play sound: {sound_name}")
        print(f"[DEBUG] Sound volume: {self.sound_volume}")
        
        # If we already have the sound loaded, play it
        if sound_name in self.sound_effects and self.sound_effects[sound_name]:
            try:
                print(f"[DEBUG] Playing cached sound: {sound_name}")
                self.sound_effects[sound_name].play()
                return
            except pygame.error as e:
                print(f"Error playing sound effect {sound_name}: {e}")
        
        # Otherwise, try to load and play a random sound from the appropriate list
        sound_list = []
        if sound_name == 'block_land' and self.block_land_sounds:
            sound_list = self.block_land_sounds
            print(f"[DEBUG] Block land sounds available: {len(self.block_land_sounds)}")
        elif sound_name == 'line_clear' and self.line_clear_sounds:
            sound_list = self.line_clear_sounds
            print(f"[DEBUG] Line clear sounds available: {len(self.line_clear_sounds)}")
        elif sound_name == 'level_up' and self.level_up_sounds:
            sound_list = self.level_up_sounds
            print(f"[DEBUG] Level up sounds available: {len(self.level_up_sounds)}")
        elif sound_name == 'game_over' and self.game_over_sounds:
            sound_list = self.game_over_sounds
            print(f"[DEBUG] Game over sounds available: {len(self.game_over_sounds)}")
        
        if sound_list:
            # Choose a random sound from the list
            sound_path = random.choice(sound_list)
            print(f"[DEBUG] Selected sound path: {sound_path}")
            try:
                sound = pygame.mixer.Sound(sound_path)
                sound.set_volume(self.sound_volume)
                print(f"[DEBUG] Playing sound from path: {sound_path}")
                sound.play()
                # Cache the sound for future use
                self.sound_effects[sound_name] = sound
            except pygame.error as e:
                print(f"Error playing sound effect {sound_name}: {e}")
        else:
            print(f"No sounds available for {sound_name}")
    
    def create_sounds_readme(self):
        """Create a README file with instructions in the sounds directory"""
        readme_path = self.sounds_dir / "README.txt"
        
        with open(readme_path, 'w') as f:
            f.write("""TETRIS GAME SOUND EFFECTS INSTRUCTIONS
            
This directory contains sound effects for the Tetris game.

Supported Sound Effects:
- block_land.wav: Plays when a block lands on the ground
- line_clear.wav: Plays when a line is cleared
- level_up.wav: Plays when the player levels up
- game_over.wav: Plays when the game ends

Supported File Formats:
- MP3 (.mp3)
- OGG Vorbis (.ogg)
- WAV (.wav)

How to Add Custom Sound Effects:
1. Simply replace the existing files with your own
2. Make sure to use the same filenames
3. Restart the game to use your custom sounds
            """)
        
        return str(readme_path)


def create_music_directories():
    """
    Create the necessary music directories and README file.
    This can be run as a standalone function to set up the music structure.
    """
    manager = MusicManager()
    readme_path = manager.create_example_readme()
    sounds_readme_path = manager.create_sounds_readme()
    print(f"Created music directories and README at {readme_path}")
    print(f"Created sounds directory and README at {sounds_readme_path}")
    

# Add custom sound pack methods to the MusicManager class
def get_default_sound_packs_config(self):
    return {
        "active_pack": "default",
        "packs": {
            "default": {
                "name": "Default Sounds",
                "description": "The default sound effects for the game",
                "sounds": {
                    "block_land": "default",
                    "line_clear": "default",
                    "level_up": "default",
                    "game_over": "default"
                }
            }
        }
    }

def create_default_sound_packs_config(self):
    """Create the default sound packs configuration file"""
    default_config = self.get_default_sound_packs_config()
    
    with open(self.sound_packs_config, 'w') as f:
        json.dump(default_config, f, indent=4)
        
    # Create a README file in the custom sounds directory
    readme_path = self.custom_sounds_dir / "README.txt"
    with open(readme_path, 'w') as f:
        f.write("""CUSTOM SOUND PACKS INSTRUCTIONS
        
This directory allows you to create and manage custom sound packs for the Tetris game.

How to Create a Custom Sound Pack:
1. Create a new folder in this directory with your sound pack name (e.g., 'my_sounds')
2. Add your custom sound files to this folder using these filenames:
   - block_land.wav: Plays when a block lands on the ground
   - line_clear.wav: Plays when a line is cleared
   - level_up.wav: Plays when the player levels up
   - game_over.wav: Plays when the game ends
3. The game will automatically detect your sound pack

Supported File Formats:
- MP3 (.mp3)
- OGG Vorbis (.ogg)
- WAV (.wav)
        """)
    return default_config

def load_sound_packs_config(self):
    """Load the sound packs configuration"""
    if self.sound_packs_config.exists():
        try:
            with open(self.sound_packs_config, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sound packs config: {e}")
            return self.create_default_sound_packs_config()
    else:
        return self.create_default_sound_packs_config()

def scan_custom_sound_packs(self):
    """Scan for custom sound packs in the custom_sounds directory"""
    # Get the current configuration
    config = self.load_sound_packs_config()
    
    # Scan for directories in the custom_sounds folder
    for item in self.custom_sounds_dir.iterdir():
        if item.is_dir() and item.name != '__pycache__':
            # Check if this is a valid sound pack (has at least one sound file)
            has_sound_files = False
            for sound_name in ['block_land', 'line_clear', 'level_up', 'game_over']:
                for ext in ['.wav', '.mp3', '.ogg']:
                    if (item / f"{sound_name}{ext}").exists():
                        has_sound_files = True
                        break
                if has_sound_files:
                    break
            
            if has_sound_files:
                # Add this pack to the configuration if it's not already there
                if item.name not in config['packs']:
                    config['packs'][item.name] = {
                        "name": item.name.replace('_', ' ').title(),
                        "description": f"Custom sound pack: {item.name}",
                        "sounds": {}
                    }
                    
                    # Detect which sound files are available
                    for sound_name in ['block_land', 'line_clear', 'level_up', 'game_over']:
                        for ext in ['.wav', '.mp3', '.ogg']:
                            if (item / f"{sound_name}{ext}").exists():
                                config['packs'][item.name]['sounds'][sound_name] = f"{sound_name}{ext}"
                                break
                        if sound_name not in config['packs'][item.name]['sounds']:
                            config['packs'][item.name]['sounds'][sound_name] = "default"
    
    # Save the updated configuration
    with open(self.sound_packs_config, 'w') as f:
        json.dump(config, f, indent=4)
    
    return config

def set_active_sound_pack(self, pack_name):
    """Set the active sound pack"""
    # Make sure the pack exists
    config = self.load_sound_packs_config()
    if pack_name in config['packs']:
        config['active_pack'] = pack_name
        self.active_sound_pack = pack_name
        
        # Save the updated configuration
        with open(self.sound_packs_config, 'w') as f:
            json.dump(config, f, indent=4)
        
        # Reload sound effects with the new pack
        self.load_sound_effects()
        return True
    return False

# Add the methods to the MusicManager class
MusicManager.get_default_sound_packs_config = get_default_sound_packs_config
MusicManager.create_default_sound_packs_config = create_default_sound_packs_config
MusicManager.load_sound_packs_config = load_sound_packs_config
MusicManager.scan_custom_sound_packs = scan_custom_sound_packs
MusicManager.set_active_sound_pack = set_active_sound_pack


if __name__ == "__main__":
    # When run directly, create the music directories and README
    create_music_directories()
