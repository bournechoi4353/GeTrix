#!/usr/bin/env python3
import pygame
import random
import time
import sys
import math
import os
from pathlib import Path
from store_data import load_store_data, save_store_data, add_line_chips, get_active_skin, get_line_chips, purchase_skin, set_active_skin
from music_manager import MusicManager

# Initialize Pygame
pygame.init()
icon = pygame.image.load("logo.png")  # must be .png
pygame.display.set_icon(icon)
# Asset paths
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')

# Create directories if they don't exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Function to load images from assets folder
def load_image(filename, subfolder=None, scale=None, convert_alpha=True):
    """Load an image from the assets folder with optional scaling
    
    Args:
        filename (str): Name of the image file
        subfolder (str, optional): Subfolder within the images directory (e.g. 'buttons/standard')
        scale (tuple or float, optional): Scale dimensions or factor
        convert_alpha (bool): Whether to use convert_alpha for transparency
    
    Returns:
        pygame.Surface or None: The loaded image or None if not found
    """
    try:
        # Determine the correct path based on subfolder
        if subfolder:
            filepath = os.path.join(IMAGES_DIR, subfolder, filename)
        else:
            filepath = os.path.join(IMAGES_DIR, filename)
            
        # Check if the file exists
        if os.path.exists(filepath):
            if convert_alpha:
                image = pygame.image.load(filepath).convert_alpha()
            else:
                image = pygame.image.load(filepath).convert()
                
            if scale:
                if isinstance(scale, tuple):
                    # Scale to specific dimensions
                    image = pygame.transform.scale(image, scale)
                else:
                    # Scale by factor
                    size = image.get_size()
                    image = pygame.transform.scale(image, (int(size[0] * scale), int(size[1] * scale)))
            return image
        else:
            print(f"Warning: Image file not found: {filepath}")
            return None
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        return None

# Constants
# 1:1 aspect ratio (square window)
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
GRID_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = 10, 20
PREVIEW_SIZE = 4

# Game modes
MODE_NORMAL = "normal"
MODE_BRAINFCK = "brainfck"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (30, 30, 40)
LIGHT_GRAY = (220, 220, 230)

# Neon tetromino colors with glow effect
RED = (255, 41, 117)         # Neon Pink
GREEN = (0, 255, 170)         # Neon Green
BLUE = (41, 121, 255)         # Neon Blue
CYAN = (0, 234, 255)          # Electric Cyan
MAGENTA = (255, 64, 255)      # Electric Purple
YELLOW = (255, 236, 39)       # Neon Yellow
ORANGE = (255, 121, 0)        # Neon Orange

# Bright versions for hover effects
BRIGHT_WHITE = (255, 255, 255)  # Pure white
BRIGHT_GREEN = (128, 255, 200)  # Brighter neon green
BRIGHT_CYAN = (128, 255, 255)   # Brighter electric cyan
BRIGHT_MAGENTA = (255, 128, 255) # Brighter electric purple
BRIGHT_YELLOW = (255, 255, 128)  # Brighter neon yellow

# UI Colors - Cyberpunk/Synthwave inspired
BG_COLOR = (15, 15, 35)       # Deep space blue
UI_BG_COLOR = (25, 25, 45)    # Slightly lighter space blue
UI_ACCENT = (0, 255, 255)     # Cyan accent
UI_HIGHLIGHT = (255, 0, 255)  # Magenta highlight
UI_TEXT = (240, 240, 255)     # Soft white
UI_GRID_LINE = (60, 60, 100)  # Subtle grid lines
UI_GRID_BG = (20, 20, 40)     # Grid background
BUTTON_BG = (40, 40, 80)      # Button background
BUTTON_HOVER = (60, 60, 120)  # Button hover color

# Gradient colors for backgrounds
GRADIENT_TOP = (25, 25, 90)   # Deep blue
GRADIENT_BOTTOM = (90, 30, 90) # Deep purple

# Particle effect colors
PARTICLE_COLORS = [
    (255, 0, 128),  # Hot pink
    (0, 255, 255),  # Cyan
    (255, 255, 0),  # Yellow
    (128, 0, 255),  # Purple
    (0, 255, 128)   # Mint
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # J
    [[1, 1, 1], [0, 0, 1]],  # L
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Colors for each shape
SHAPE_COLORS = [CYAN, YELLOW, MAGENTA, BLUE, ORANGE, GREEN, RED]

class Tetromino:
    def __init__(self, x, y, shape_idx=None):
        if shape_idx is None:
            self.shape_idx = random.randint(0, len(SHAPES) - 1)
        else:
            self.shape_idx = shape_idx
        self.shape = SHAPES[self.shape_idx]
        
        # Use active skin if available
        store_data = load_store_data()
        active_skin = store_data["active_skin"]
        skin_info = store_data["available_skins"].get(active_skin)
        
        if skin_info and skin_info["owned"]:
            if skin_info["type"] == "basic":
                # Basic skins just change colors
                self.color = skin_info["colors"][self.shape_idx]
            elif skin_info["type"] == "special" and "effect" in skin_info:
                # Special skins might have effects (like gradients, patterns, etc.)
                self.color = skin_info["colors"][self.shape_idx]
                self.effect = skin_info["effect"]
            else:
                self.color = skin_info["colors"][self.shape_idx]
        else:
            # Default colors
            self.color = SHAPE_COLORS[self.shape_idx]
        self.x = x
        self.y = y
        self.rotation = 0

    def rotate(self):
        # Create a new rotated shape
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = self.shape[r][c]
        
        return rotated

    def get_shape(self):
        return self.shape

class TetrisGame:
    def lighten_color(self, color, amount=50):
        """Return a lighter version of the color"""
        try:
            # Ensure color is a valid RGB tuple
            if not color or len(color) < 3:
                return (255, 255, 255)  # Default to white if invalid
            
            # Take only the RGB components (first 3 values)
            rgb_color = color[:3]
            
            # Create a new RGB tuple with lightened values
            result = tuple(min(255, c + amount) for c in rgb_color)
            
            # Ensure we have exactly 3 components
            while len(result) < 3:
                result = result + (255,)
                
            return result
        except Exception as e:
            print(f"Error in lighten_color: {e}, input color: {color}")
            return (255, 255, 255)  # Default to white on error
    
    def darken_color(self, color, amount=50):
        """Return a darker version of the color"""
        try:
            # Ensure color is a valid RGB tuple
            if not color or len(color) < 3:
                return (0, 0, 0)  # Default to black if invalid
            
            # Take only the RGB components (first 3 values)
            rgb_color = color[:3]
            
            # Create a new RGB tuple with darkened values
            result = tuple(max(0, c - amount) for c in rgb_color)
            
            # Ensure we have exactly 3 components
            while len(result) < 3:
                result = result + (0,)
                
            return result
        except Exception as e:
            print(f"Error in darken_color: {e}, input color: {color}")
            return (0, 0, 0)  # Default to black on error
        
    def get_neon_glow(self, color, intensity=0.7):
        """Add a neon glow effect to a color"""
        try:
            # Ensure color is a valid RGB tuple
            if not color or len(color) < 3:
                return (128, 128, 255)  # Default to light blue if invalid
            
            # Take only the RGB components (first 3 values)
            rgb_color = color[:3]
            
            # Create a softer version of the color for the glow
            glow = tuple(int(c + (255 - c) * intensity) for c in rgb_color)
            
            # Ensure we have exactly 3 components
            while len(glow) < 3:
                glow = glow + (255,)
                
            return glow
        except Exception as e:
            print(f"Error in get_neon_glow: {e}, input color: {color}")
            return (128, 128, 255)  # Default to light blue on error
        
    def __init__(self, x_offset, controls, y_offset=0, mode=MODE_NORMAL):
        self.x_offset = x_offset
        self.y_offset = y_offset  # Original y_offset without additional offset
        self.controls = controls
        self.mode = mode
        self.menu_button_rect = None  # For storing the back to menu button rect
        
        # Rotation for Brainfck mode
        self.rotation_angle = 0
        self.target_rotation = 0
        self.rotation_speed = 2  # Degrees per frame
        
        # Particle effects
        self.particles = []
        self.grid_glow = 0
        self.grid_glow_direction = 1
        self.grid_pulse_speed = 0.5
        
        # Grid line effect
        self.grid_line_offset = 0
        self.grid_line_speed = 0.5
        
        # Shaking effect parameters
        self.shake_intensity = 0
        self.shake_decay = 0.9
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        
        # Illusion effect parameters
        self.illusion_active = False
        self.illusion_timer = 0
        self.illusion_duration = 15  # seconds
        self.illusion_intensity = 0
        self.illusion_wave_time = 0
        
        # Background stars
        self.stars = []
        for _ in range(50):
            self.stars.append({
                'x': random.randint(0, GRID_WIDTH * GRID_SIZE),
                'y': random.randint(0, GRID_HEIGHT * GRID_SIZE),
                'size': random.uniform(0.5, 2),
                'speed': random.uniform(0.2, 1.0),
                'brightness': random.uniform(0.3, 1.0)
            })
            
        # Line clear effect
        self.clear_flash = 0
        self.clear_lines = []
        self.clear_animation_time = 0
        self.clear_animation_duration = 0.5
        
        self.reset()

    def reset(self):
        self.board = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.last_fall_time = time.time()
        self.fall_speed = 0.5  # seconds per fall
        self.last_move_time = time.time()
        self.move_delay = 0.1  # seconds per move
        
        # Reset particles
        self.particles = []
        
        # Reset stars
        for star in self.stars:
            star['x'] = random.randint(0, GRID_WIDTH * GRID_SIZE)
            star['y'] = random.randint(0, GRID_HEIGHT * GRID_SIZE)
            
        # Reset rotation for Brainfck mode
        self.rotation_angle = 0
        self.target_rotation = 0

    def new_piece(self):
        # Create a new piece at the top of the board
        return Tetromino(GRID_WIDTH // 2 - 1, 0)

    def valid_position(self, piece, x_offset=0, y_offset=0, shape=None):
        if shape is None:
            shape = piece.shape
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    board_x = piece.x + x + x_offset
                    board_y = piece.y + y + y_offset
                    
                    # Check if out of bounds
                    if (board_x < 0 or board_x >= GRID_WIDTH or 
                        board_y < 0 or board_y >= GRID_HEIGHT):
                        return False
                    
                    # Check if collides with another piece
                    if board_y >= 0 and self.board[board_y][board_x]:
                        return False
        return True
        
    def check_collision(self, x, y, shape):
        """Check if a piece at position (x,y) with the given shape would collide with anything"""
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    board_x = x + col_idx
                    board_y = y + row_idx
                    
                    # Check if out of bounds
                    if (board_x < 0 or board_x >= GRID_WIDTH or 
                        board_y < 0 or board_y >= GRID_HEIGHT):
                        return True
                    
                    # Check if collides with another piece
                    if board_y >= 0 and self.board[board_y][board_x]:
                        return True
        return False

    def merge_piece(self):
        # First check if we can actually merge (piece has landed)
        # We only do the normal check - bounce mode doesn't affect merging
        if self.valid_position(self.current_piece, y_offset=1):
            return False  # Piece hasn't landed yet
            
        # Merge the piece into the board
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    board_y = self.current_piece.y + y
                    if board_y >= 0:  # Only merge if within bounds
                        self.board[board_y][self.current_piece.x + x] = self.current_piece.color
        
        # Play block land sound
        if hasattr(self, 'music_manager') and self.music_manager:
            self.music_manager.play_sound('block_land')
        
        # Check for completed lines
        completed_lines = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.board[y]):
                completed_lines += 1
                # Move all lines above down
                for y2 in range(y, 0, -1):
                    self.board[y2] = self.board[y2 - 1][:]
                # Clear the top line
                self.board[0] = [0 for _ in range(GRID_WIDTH)]
                y += 1  # Check this line again as new blocks have moved down
            y -= 1
        
        # Update score
        if self.mode == MODE_BRAINFCK:
            # In Brainfck mode, each line is worth 300 points
            self.score += completed_lines * 300 * self.level
        else:
            # Normal scoring
            if completed_lines == 1:
                self.score += 100 * self.level
            elif completed_lines == 2:
                self.score += 300 * self.level
            elif completed_lines == 3:
                self.score += 500 * self.level
            elif completed_lines == 4:
                self.score += 800 * self.level
        
        # Update lines cleared and level
        self.lines_cleared += completed_lines
        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
        
        # Add LineChips for cleared lines (1 LineChip per line cleared)
        if completed_lines > 0:
            add_line_chips(completed_lines)
            
            # Play line clear sound
            if hasattr(self, 'music_manager') and self.music_manager:
                self.music_manager.play_sound('line_clear')
                
        # Check if leveled up
        old_level = (self.lines_cleared - completed_lines) // 10 + 1
        new_level = self.lines_cleared // 10 + 1
        
        if new_level > old_level and hasattr(self, 'music_manager') and self.music_manager:
            # Play level up sound
            self.music_manager.play_sound('level_up')
        
        # Get next piece
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        
        # Check if game over
        if not self.valid_position(self.current_piece):
            self.game_over = True
            
            # Play game over sound
            if hasattr(self, 'music_manager') and self.music_manager:
                self.music_manager.play_sound('game_over')
            
        return True  # Successfully merged

    def move(self, dx, dy):
        current_time = time.time()
        if current_time - self.last_move_time < self.move_delay:
            return
        
        self.last_move_time = current_time
        
        if self.valid_position(self.current_piece, x_offset=dx, y_offset=dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate_piece(self):
        rotated_shape = self.current_piece.rotate()
        if self.valid_position(self.current_piece, shape=rotated_shape):
            self.current_piece.shape = rotated_shape
            return True
        return False

    def hard_drop(self):
        while self.move(0, 1):
            pass
        self.merge_piece()

    def update(self):
        if self.game_over:
            return
        
        current_time = time.time()
        if current_time - self.last_fall_time > self.fall_speed:
            self.last_fall_time = current_time
            # Try to move down
            if not self.move(0, 1):
                # Only merge if the piece can't move down
                if not self.valid_position(self.current_piece, y_offset=1):
                    self.merge_piece()
                    # Trigger shake effect when a piece lands
                    self.trigger_shake(5)
        
        # Update shaking effect
        self.shake_intensity *= self.shake_decay
        if self.shake_intensity > 0.1:
            self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0
            
        # Update illusion effect
        if self.illusion_active:
            self.illusion_timer -= 0.016  # Approximate for 60 FPS
            self.illusion_wave_time += 0.032  # Faster wave movement
            
            # Gradually increase intensity to peak and then decrease
            if self.illusion_timer > self.illusion_duration / 2:
                # Ramping up phase
                progress = 1 - (self.illusion_timer - self.illusion_duration/2) / (self.illusion_duration/2)
                self.illusion_intensity = 0.5 * progress
            else:
                # Ramping down phase
                progress = self.illusion_timer / (self.illusion_duration/2)
                self.illusion_intensity = 0.5 * progress
            
            if self.illusion_timer <= 0:
                self.illusion_active = False
                self.illusion_intensity = 0
        else:
            # Random chance to activate illusion effect (0.05% chance per frame)
            if random.random() < 0.0005:
                self.activate_illusion_effect()
                
    def activate_illusion_effect(self):
        """Activate the illusion effect"""
        self.illusion_active = True
        self.illusion_duration = random.uniform(5.0, 10.0)  # Random duration
        self.illusion_timer = self.illusion_duration  # Start at full duration
        self.illusion_intensity = 0.1  # Start with lower intensity
        self.illusion_wave_time = 0
        self.illusion_pattern = random.choice(['wave', 'spiral', 'pulse', 'zigzag'])
        
    def trigger_shake(self, intensity=5):
        """Trigger a screen shake effect"""
        self.shake_intensity = intensity

    def draw(self, screen, font, ghost_pieces=False):
        # Update rotation for Brainfck mode
        if self.mode == MODE_BRAINFCK:
            # Gradually rotate towards target rotation
            if self.rotation_angle != self.target_rotation:
                diff = self.target_rotation - self.rotation_angle
                # Take the shortest path to the target angle
                if abs(diff) > 180:
                    diff = diff - 360 if diff > 0 else diff + 360
                    
                # Move towards target at rotation_speed
                if abs(diff) <= self.rotation_speed:
                    self.rotation_angle = self.target_rotation
                else:
                    self.rotation_angle += self.rotation_speed if diff > 0 else -self.rotation_speed
                    
                # Keep angle in 0-360 range
                self.rotation_angle %= 360
        
        # Update grid glow effect
        self.grid_glow += 0.01 * self.grid_glow_direction
        if self.grid_glow > 1:
            self.grid_glow = 1
            self.grid_glow_direction = -1
        elif self.grid_glow < 0:
            self.grid_glow = 0
            self.grid_glow_direction = 1
            
        # Update grid line animation
        self.grid_line_offset += self.grid_line_speed
        if self.grid_line_offset > GRID_SIZE * 2:
            self.grid_line_offset = 0
            
        # Update star positions
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > GRID_HEIGHT * GRID_SIZE:
                star['y'] = 0
                star['x'] = random.randint(0, GRID_WIDTH * GRID_SIZE)
                star['brightness'] = random.uniform(0.3, 1.0)
                
        # Calculate shaking and illusion offsets
        shake_x = int(self.shake_offset_x)
        shake_y = int(self.shake_offset_y)
        
        # Apply illusion effect to the offsets if active
        illusion_x, illusion_y = 0, 0
        if self.illusion_active:
            # Create a wavy, distorted effect
            wave_x = math.sin(self.illusion_wave_time * 2.5) * 8 * self.illusion_intensity
            wave_y = math.cos(self.illusion_wave_time * 2.0) * 6 * self.illusion_intensity
            illusion_x = int(wave_x)
            illusion_y = int(wave_y)
        
        # Apply combined offsets
        total_offset_x = self.x_offset + shake_x + illusion_x
        total_offset_y = self.y_offset + shake_y + illusion_y
        
        # Draw cyberpunk-style background with stars
        board_bg = pygame.Rect(total_offset_x - 5, total_offset_y - 5, GRID_WIDTH * GRID_SIZE + 10, GRID_HEIGHT * GRID_SIZE + 10)
        
        # Create a gradient background
        bg_surface = pygame.Surface((board_bg.width, board_bg.height))
        for y in range(board_bg.height):
            # Calculate gradient color
            ratio = y / board_bg.height
            r = int(GRADIENT_TOP[0] * (1 - ratio) + GRADIENT_BOTTOM[0] * ratio)
            g = int(GRADIENT_TOP[1] * (1 - ratio) + GRADIENT_BOTTOM[1] * ratio)
            b = int(GRADIENT_TOP[2] * (1 - ratio) + GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(bg_surface, (r, g, b), (0, y), (board_bg.width, y))
        
        # Draw the gradient background
        screen.blit(bg_surface, (board_bg.x, board_bg.y))
        
        # Draw stars with dizzying effects during illusion
        for star in self.stars:
            # Calculate star position and color
            if self.illusion_active:
                # Create a subtle wave motion for stars during illusion
                wave_x = star['x'] + math.sin(time.time() * 0.8 + star['y'] * 0.02) * 3.0 * self.illusion_intensity
                wave_y = star['y'] + math.cos(time.time() * 0.5 + star['x'] * 0.01) * 2.0 * self.illusion_intensity
                
                # Create a subtle blue-cyan shift for stars
                blue_shift = int(30 * math.sin(time.time() * 1.5 + star['y'] * 0.05))
                brightness = max(0.1, min(1.0, star['brightness'] * (0.7 + 0.3 * math.sin(time.time() * 2.0))))
                # Ensure all color values are valid integers between 0-255
                r = max(0, min(255, int(100 * brightness)))
                g = max(0, min(255, int(150 * brightness)))
                b = max(0, min(255, int(200 * brightness + blue_shift)))
                star_color = (r, g, b)
                
                # Slightly vary star size for dizzying effect
                size_factor = 1.0 + 0.2 * math.sin(time.time() * 3.0 + star['x'] * 0.1)
                # Ensure star size is a valid positive number
                star_size = max(0.1, star['size'] * size_factor)
            else:
                # Normal star rendering
                wave_x = star['x']
                wave_y = star['y']
                star_color = (int(255 * star['brightness']), int(255 * star['brightness']), int(255 * star['brightness']))
                star_size = star['size']
                
            pygame.draw.circle(screen, star_color, 
                             (int(total_offset_x + wave_x), int(total_offset_y + wave_y)), 
                             star_size)
        
        # Draw grid border with neon glow
        glow_intensity = 0.3 + 0.2 * self.grid_glow  # Pulsing glow effect
        glow_color = self.get_neon_glow(UI_ACCENT, glow_intensity)
        pygame.draw.rect(screen, glow_color, board_bg, 3, border_radius=3)
        pygame.draw.rect(screen, UI_ACCENT, board_bg, 1, border_radius=3)
        
        # For Brainfck mode, calculate the center of the grid for rotation
        grid_center_x = total_offset_x + (GRID_WIDTH * GRID_SIZE) // 2
        grid_center_y = total_offset_y + (GRID_HEIGHT * GRID_SIZE) // 2
        
        # Draw grid with cyberpunk style
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Draw grid cell with total offsets and illusion distortion
                if self.illusion_active:
                    # Add per-cell distortion for a more trippy effect
                    cell_distort_x = math.sin((x + y) * 0.2 + self.illusion_wave_time) * 3 * self.illusion_intensity
                    cell_distort_y = math.cos((x - y) * 0.2 + self.illusion_wave_time) * 3 * self.illusion_intensity
                else:
                    cell_distort_x = 0
                    cell_distort_y = 0
                    
                # Apply rotation for Brainfck mode
                if self.mode == MODE_BRAINFCK and self.rotation_angle != 0:
                    # Calculate position relative to grid center
                    rel_x = x * GRID_SIZE - (GRID_WIDTH * GRID_SIZE) // 2
                    rel_y = y * GRID_SIZE - (GRID_HEIGHT * GRID_SIZE) // 2
                    
                    # Rotate the point around the origin
                    angle_rad = math.radians(self.rotation_angle)
                    rot_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
                    rot_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)
                    
                    # Translate back to screen coordinates
                    cell_x = grid_center_x + rot_x + int(cell_distort_x)
                    cell_y = grid_center_y + rot_y + int(cell_distort_y)
                else:
                    cell_x = total_offset_x + x * GRID_SIZE + int(cell_distort_x)
                    cell_y = total_offset_y + y * GRID_SIZE + int(cell_distort_y)
                    
                cell_rect = pygame.Rect(
                    int(cell_x), 
                    int(cell_y), 
                    GRID_SIZE, 
                    GRID_SIZE
                )
                
                # Draw grid lines with a subtle glow effect
                grid_color = UI_GRID_LINE
                # Make horizontal and vertical lines that move for a tron-like effect
                if (x + y + int(self.grid_line_offset / GRID_SIZE)) % 4 == 0:
                    grid_color = self.lighten_color(UI_GRID_LINE, 20)
                
                pygame.draw.rect(screen, grid_color, cell_rect, 1)
                
                # Draw block if present
                if self.board[y][x]:
                    # Apply illusion distortion to blocks
                    if self.illusion_active:
                        block_distort_x = math.sin((x + y) * 0.3 + self.illusion_wave_time) * 4 * self.illusion_intensity
                        block_distort_y = math.cos((x - y) * 0.3 + self.illusion_wave_time) * 4 * self.illusion_intensity
                    else:
                        block_distort_x = 0
                        block_distort_y = 0
                    
                    # Create a slightly larger rect for the glow effect
                    glow_rect = pygame.Rect(
                        total_offset_x + x * GRID_SIZE - 1 + int(block_distort_x), 
                        total_offset_y + y * GRID_SIZE - 1 + int(block_distort_y), 
                        GRID_SIZE + 2, 
                        GRID_SIZE + 2
                    )
                    
                    block_rect = pygame.Rect(
                        total_offset_x + x * GRID_SIZE + 1 + int(block_distort_x), 
                        total_offset_y + y * GRID_SIZE + 1 + int(block_distort_y), 
                        GRID_SIZE - 2, 
                        GRID_SIZE - 2
                    )
                    
                    color = self.board[y][x]
                    
                    # Draw a stronger glow for the active piece
                    glow_intensity = 0.5 + 0.3 * self.grid_glow  # Stronger pulsing effect
                    glow_color = self.get_neon_glow(color, glow_intensity)
                    pygame.draw.rect(screen, glow_color, glow_rect, border_radius=4)
                    
                    # Check if we need to apply special effects for current piece
                    store_data = load_store_data()
                    active_skin = store_data["active_skin"]
                    skin_info = store_data["available_skins"].get(active_skin)
                    
                    if skin_info and skin_info["owned"] and skin_info["type"] == "special" and "effect" in skin_info:
                        effect = skin_info["effect"]
                        
                        if effect == "gradient":
                            # Create a more dramatic gradient effect with neon colors
                            gradient_rect = pygame.Surface((block_rect.width, block_rect.height), pygame.SRCALPHA)
                            for i in range(block_rect.height):
                                # Create a gradient from color to a brighter neon version
                                factor = i / block_rect.height
                                gradient_color = self.get_neon_glow(color, factor * 0.8)
                                pygame.draw.line(gradient_rect, gradient_color, (0, i), (block_rect.width, i))
                            screen.blit(gradient_rect, block_rect)
                            
                            # Add scanline effect
                            for i in range(0, block_rect.height, 2):
                                scanline = pygame.Rect(block_rect.left, block_rect.top + i, block_rect.width, 1)
                                pygame.draw.rect(screen, (0, 0, 0, 100), scanline)
                        elif effect == "sparkle":
                            # Draw the base block with a digital circuit pattern
                            pygame.draw.rect(screen, color, block_rect, border_radius=3)
                            
                            # Draw digital circuit lines
                            circuit_color = self.lighten_color(color, 70)
                            if random.random() < 0.5:  # Horizontal circuit
                                y_pos = block_rect.top + random.randint(2, block_rect.height - 3)
                                pygame.draw.line(screen, circuit_color, 
                                               (block_rect.left, y_pos),
                                               (block_rect.right, y_pos), 1)
                            else:  # Vertical circuit
                                x_pos = block_rect.left + random.randint(2, block_rect.width - 3)
                                pygame.draw.line(screen, circuit_color, 
                                               (x_pos, block_rect.top),
                                               (x_pos, block_rect.bottom), 1)
                            
                            # Add sparkle effect with more intensity
                            if random.random() < 0.2:  # 20% chance for a sparkle
                                for _ in range(random.randint(1, 3)):
                                    sparkle_pos = (
                                        random.randint(block_rect.left, block_rect.right),
                                        random.randint(block_rect.top, block_rect.bottom)
                                    )
                                    sparkle_size = random.randint(1, 3)
                                    pygame.draw.circle(screen, WHITE, sparkle_pos, sparkle_size)
                        else:
                            # Holographic effect for unknown effects
                            pygame.draw.rect(screen, color, block_rect, border_radius=3)
                            
                            # Add holographic lines
                            holo_offset = (time.time() * 2) % block_rect.height
                            for i in range(0, block_rect.height, 4):
                                line_y = (block_rect.top + i + int(holo_offset)) % (block_rect.top + block_rect.height)
                                if line_y >= block_rect.top and line_y < block_rect.top + block_rect.height:
                                    line_color = self.lighten_color(color, 100)
                                    pygame.draw.line(screen, line_color, 
                                                   (block_rect.left, line_y),
                                                   (block_rect.right, line_y), 1)
                    else:
                        # Enhanced standard block drawing with inner glow
                        pygame.draw.rect(screen, color, block_rect, border_radius=3)
                        
                        # Add subtle inner lighting effect
                        inner_rect = pygame.Rect(
                            block_rect.left + 2,
                            block_rect.top + 2,
                            block_rect.width - 4,
                            block_rect.height - 4
                        )
                        inner_color = self.lighten_color(color, 30)
                        pygame.draw.rect(screen, inner_color, inner_rect, border_radius=2)
                    
                    # Draw highlight with more pronounced effect (top-left edges)
                    highlight_points = [
                        (block_rect.left, block_rect.bottom - 3),
                        (block_rect.left, block_rect.top),
                        (block_rect.right - 3, block_rect.top)
                    ]
                    pygame.draw.polygon(screen, self.lighten_color(color, 70), highlight_points)
                    
                    # Draw shadow with more pronounced effect (bottom-right edges)
                    shadow_points = [
                        (block_rect.left + 3, block_rect.bottom),
                        (block_rect.right, block_rect.bottom),
                        (block_rect.right, block_rect.top + 3)
                    ]
                    pygame.draw.polygon(screen, self.darken_color(color, 70), shadow_points)
                    
                    # Randomly add particles when blocks are placed
                    # More subtle particle effects during illusion
                    particle_chance = 0.01
                    particle_count = 2
                    if self.illusion_active:
                        particle_chance = 0.03  # Moderate chance during illusion
                        particle_count = 4      # Fewer particles for subtlety
                        
                    if random.random() < particle_chance:
                        for _ in range(particle_count):
                            # Apply illusion distortion to particle starting position
                            if self.illusion_active:
                                part_distort_x = random.uniform(-5, 5) * self.illusion_intensity
                                part_distort_y = random.uniform(-5, 5) * self.illusion_intensity
                            else:
                                part_distort_x = 0
                                part_distort_y = 0
                                
                            # Make particles more subtle but dizzying during illusion
                            if self.illusion_active:
                                dx_range = (-1.5, 1.5)  # Less horizontal movement
                                dy_range = (-2.5, -0.5)  # Less vertical movement
                                size_range = (1, 3)      # Smaller particles
                                life_range = (0.8, 1.5)  # Shorter lifespan
                            else:
                                dx_range = (-1, 1)
                                dy_range = (-2, -0.5)
                                size_range = (1, 2)
                                life_range = (0.6, 1.2)
                                
                            self.particles.append({
                                'x': total_offset_x + x * GRID_SIZE + GRID_SIZE // 2 + part_distort_x,
                                'y': total_offset_y + y * GRID_SIZE + GRID_SIZE // 2 + part_distort_y,
                                'dx': random.uniform(*dx_range),
                                'dy': random.uniform(*dy_range),
                                'size': random.uniform(*size_range),
                                'color': self.lighten_color(color, 100),
                                'life': random.uniform(*life_range)
                            })
        
        # Update and draw particles
        particles_to_remove = []
        for i, particle in enumerate(self.particles):
            # Update particle position
            # Check if we're using direction/speed or dx/dy
            if 'direction' in particle and 'speed' in particle:
                # Calculate dx and dy from direction and speed
                dx = particle['speed'] * math.cos(particle['direction'])
                dy = particle['speed'] * math.sin(particle['direction'])
                particle['x'] += dx
                particle['y'] += dy
            elif 'dx' in particle and 'dy' in particle:
                # Use dx and dy directly
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                
            # Reduce life if it exists
            if 'life' in particle:
                particle['life'] -= 0.02
            
            # Remove dead particles or particles that have moved off screen
            if ('life' in particle and particle['life'] <= 0) or \
               particle['x'] < -50 or particle['x'] > GRID_WIDTH * GRID_SIZE + 50 or \
               particle['y'] < -50 or particle['y'] > GRID_HEIGHT * GRID_SIZE + 50:
                particles_to_remove.append(i)
                continue
                
            # Draw particle with fading based on life (if it exists) and special effects during illusion
            alpha = int(255 * particle['life']) if 'life' in particle else 255
            
            # Apply subtle color shifting during illusion effect
            if self.illusion_active:
                # Instead of rainbow colors, use a more subtle blue-purple-cyan shift
                # This creates a dizzying, illusion-like effect without being too bright
                
                # Get the original color components
                if len(particle['color']) >= 3:
                    r, g, b = particle['color'][:3]
                else:
                    r, g, b = 100, 100, 200  # Default blue-ish
                
                # Apply a subtle pulsing effect to the blue and cyan channels
                pulse = math.sin(time.time() * 2.0 + particle['x'] * 0.05) * 0.3 + 0.7
                
                # Create a subtle color shift that's more illusion-like
                # Ensure all color values are valid integers between 0-255
                new_r = max(0, min(255, int(r * 0.5)))  # Reduce red
                new_g = max(0, min(255, int(g * (0.6 + pulse * 0.4))))  # Subtle pulse on green
                new_b = max(0, min(255, int(b * (0.8 + pulse * 0.2))))  # Enhance blue with subtle pulse
                
                base_color = (new_r, new_g, new_b)
            else:
                base_color = particle['color']
            
            # Apply alpha
            particle_color = list(base_color)
            if len(particle_color) == 3:
                particle_color.append(min(255, alpha))  # Add alpha channel, capped at 255
            else:
                particle_color[3] = min(255, alpha)  # Update alpha channel, capped at 255
                
            # Convert to tuple to ensure it's a valid color format
            particle_color = tuple(particle_color[:4])  # Limit to 4 components (RGBA)
            
            try:
                # Draw particle with a more subtle glow effect during illusion
                if self.illusion_active and particle['size'] > 1.5:
                    # Add a smaller, more subtle glow around particles
                    glow_size = particle['size'] * 1.5 * particle['life']  # Smaller glow
                    glow_surface = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
                    
                    # Ensure glow_color is a valid RGBA tuple with lower opacity
                    glow_color = list(base_color)
                    while len(glow_color) < 3:
                        glow_color.append(0)  # Ensure RGB components
                    if len(glow_color) == 3:
                        glow_color.append(min(255, alpha // 4))  # Add alpha with lower opacity
                    else:
                        glow_color[3] = min(255, alpha // 4)  # Update alpha with lower opacity
                    glow_color = tuple(glow_color[:4])  # Limit to 4 components (RGBA)
                    
                    pygame.draw.circle(glow_surface, glow_color, 
                                    (int(glow_size), int(glow_size)), 
                                    int(glow_size))
                    screen.blit(glow_surface, 
                               (int(particle['x'] - glow_size), int(particle['y'] - glow_size)))
                    
                # Draw the particle with size based on life
                particle_size = particle['size'] * particle['life']
                if self.illusion_active:
                    # Create a more subtle, dizzying pulse effect
                    # Use multiple sine waves at different frequencies for a more disorienting effect
                    pulse1 = math.sin(time.time() * 3.0 + particle['x'] * 0.05) * 0.15
                    pulse2 = math.sin(time.time() * 1.7 + particle['y'] * 0.03) * 0.1
                    pulse_factor = 1.0 + pulse1 + pulse2
                    particle_size *= pulse_factor
                
                # Ensure particle_color is a valid color format
                if not isinstance(particle_color, tuple):
                    particle_color = tuple(particle_color)
                
                # Make sure we have at least 3 components (RGB)
                if len(particle_color) < 3:
                    particle_color = (255, 0, 255)  # Default to magenta if invalid
                    
                pygame.draw.circle(screen, particle_color, 
                                (int(particle['x']), int(particle['y'])), 
                                int(particle_size))
            except Exception as e:
                print(f"Error drawing particle: {e}, color: {particle_color}")
        
        # Remove dead particles (in reverse order to avoid index issues)
        for i in sorted(particles_to_remove, reverse=True):
            if i < len(self.particles):
                self.particles.pop(i)
        
        # Draw current piece with enhanced neon effect
        if not self.game_over:
            # Handle ghost pieces
            if ghost_pieces:
                # Draw multiple ghost pieces in different positions for a trippy effect
                for ghost_offset in range(-2, 3):
                    if ghost_offset == 0:
                        continue  # Skip the actual position
                    
                    # Only draw if valid position
                    if not self.check_collision(self.current_piece.x + ghost_offset, self.current_piece.y, self.current_piece.shape):
                        ghost_alpha = 100 + int(50 * self.grid_glow)  # Pulsing transparency
                        for y, row in enumerate(self.current_piece.shape):
                            for x, cell in enumerate(row):
                                if cell:
                                    # Create ghost with offset and different color
                                    ghost_rect = pygame.Rect(
                                        total_offset_x + (self.current_piece.x + x + ghost_offset) * GRID_SIZE + 1,
                                        total_offset_y + (self.current_piece.y + y) * GRID_SIZE + 1,
                                        GRID_SIZE - 2, GRID_SIZE - 2
                                    )
                                    
                                    # Create a semi-transparent surface with shifted color
                                    ghost_surface = pygame.Surface((ghost_rect.width, ghost_rect.height), pygame.SRCALPHA)
                                    ghost_color = list(self.current_piece.color[:3])
                                    # Shift hue for each ghost
                                    ghost_color = [(ghost_color[0] + ghost_offset * 40) % 255, 
                                                  (ghost_color[1] + ghost_offset * 60) % 255, 
                                                  (ghost_color[2] + ghost_offset * 80) % 255, 
                                                  ghost_alpha]  # Add alpha for transparency
                                    
                                    pygame.draw.rect(ghost_surface, ghost_color, 
                                                (0, 0, ghost_rect.width, ghost_rect.height), border_radius=3)
                                    screen.blit(ghost_surface, ghost_rect)
            
            # Regular ghost piece showing landing position
            ghost_y = self.current_piece.y
            while not self.check_collision(self.current_piece.x, ghost_y + 1, self.current_piece.shape):
                ghost_y += 1
                
            # Only draw ghost if it's not at the same position as the current piece
            if ghost_y > self.current_piece.y:
                ghost_alpha = 100 + int(50 * self.grid_glow)  # Pulsing transparency
                for y, row in enumerate(self.current_piece.shape):
                    for x, cell in enumerate(row):
                        if cell:
                            # Apply illusion distortion to ghost piece
                            if self.illusion_active:
                                ghost_distort_x = math.sin((x + y) * 0.4 + self.illusion_wave_time * 1.2) * 4 * self.illusion_intensity
                                ghost_distort_y = math.cos((x - y) * 0.4 + self.illusion_wave_time * 1.2) * 4 * self.illusion_intensity
                            else:
                                ghost_distort_x = 0
                                ghost_distort_y = 0
                                
                            # Draw a semi-transparent ghost block with distortion
                            ghost_rect = pygame.Rect(
                                total_offset_x + (self.current_piece.x + x) * GRID_SIZE + 1 + int(ghost_distort_x),
                                total_offset_y + (ghost_y + y) * GRID_SIZE + 1 + int(ghost_distort_y),
                                GRID_SIZE - 2, GRID_SIZE - 2
                            )
                            
                            # Create a semi-transparent surface for the ghost piece
                            ghost_surface = pygame.Surface((ghost_rect.width, ghost_rect.height), pygame.SRCALPHA)
                            ghost_color = list(self.current_piece.color)
                            if len(ghost_color) == 3:
                                ghost_color.append(ghost_alpha)  # Add alpha for transparency
                            else:
                                ghost_color[3] = ghost_alpha
                            pygame.draw.rect(ghost_surface, ghost_color, 
                                           (0, 0, ghost_rect.width, ghost_rect.height), border_radius=3)
                            
                            # Add grid pattern to ghost piece
                            for i in range(0, ghost_rect.width, 4):
                                pygame.draw.line(ghost_surface, (255, 255, 255, 40), 
                                               (i, 0), (i, ghost_rect.height))
                            for i in range(0, ghost_rect.height, 4):
                                pygame.draw.line(ghost_surface, (255, 255, 255, 40), 
                                               (0, i), (ghost_rect.width, i))
                                               
                            screen.blit(ghost_surface, ghost_rect)
            
            # Draw actual current piece with enhanced effects
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        # Create a slightly larger rect for the glow effect
                        glow_rect = pygame.Rect(
                            self.x_offset + (self.current_piece.x + x) * GRID_SIZE - 1,
                            self.y_offset + (self.current_piece.y + y) * GRID_SIZE - 1,
                            GRID_SIZE + 2, GRID_SIZE + 2
                        )
                        
                        block_rect = pygame.Rect(
                            self.x_offset + (self.current_piece.x + x) * GRID_SIZE + 1,
                            self.y_offset + (self.current_piece.y + y) * GRID_SIZE + 1,
                            GRID_SIZE - 2, GRID_SIZE - 2
                        )
                        
                        color = self.current_piece.color
                        
                        # Draw a stronger glow for the active piece
                        glow_intensity = 0.5 + 0.3 * self.grid_glow  # Stronger pulsing effect
                        glow_color = self.get_neon_glow(color, glow_intensity)
                        pygame.draw.rect(screen, glow_color, glow_rect, border_radius=4)
                        
                        # Check if we need to apply special effects for current piece
                        store_data = load_store_data()
                        active_skin = store_data["active_skin"]
                        skin_info = store_data["available_skins"].get(active_skin)
                        
                        if skin_info and skin_info["owned"] and skin_info["type"] == "special" and "effect" in skin_info:
                            effect = skin_info["effect"]
                            
                            if effect == "gradient":
                                # Create an ultra-flashy animated gradient effect with color switching
                                gradient_rect = pygame.Surface((block_rect.width, block_rect.height), pygame.SRCALPHA)
                                
                                # Color cycling based on time
                                time_val = time.time()
                                cycle_speed = 2.0  # Higher = faster color cycling
                                
                                # Create rainbow cycling colors
                                base_hue = (time_val * cycle_speed) % 1.0
                                secondary_hue = ((time_val * cycle_speed) + 0.33) % 1.0
                                tertiary_hue = ((time_val * cycle_speed) + 0.66) % 1.0
                                
                                # Convert HSV to RGB for primary colors
                                def hsv_to_rgb(h, s, v):
                                    h_i = int(h * 6)
                                    f = h * 6 - h_i
                                    p = v * (1 - s)
                                    q = v * (1 - f * s)
                                    t = v * (1 - (1 - f) * s)
                                    
                                    if h_i == 0: return (v, t, p)
                                    if h_i == 1: return (q, v, p)
                                    if h_i == 2: return (p, v, t)
                                    if h_i == 3: return (p, q, v)
                                    if h_i == 4: return (t, p, v)
                                    return (v, p, q)
                                
                                # Generate vibrant colors
                                color1 = tuple(int(c * 255) for c in hsv_to_rgb(base_hue, 1.0, 1.0))
                                color2 = tuple(int(c * 255) for c in hsv_to_rgb(secondary_hue, 1.0, 1.0))
                                color3 = tuple(int(c * 255) for c in hsv_to_rgb(tertiary_hue, 1.0, 1.0))
                                
                                # Make the gradient move over time for animation (faster)
                                offset = int((time_val * 80) % block_rect.height)
                                
                                # Draw diagonal gradient with cycling colors
                                for i in range(block_rect.height * 2):
                                    # Position with diagonal movement
                                    pos = (i + offset) % (block_rect.height * 2)
                                    rel_pos = pos / (block_rect.height * 2)
                                    
                                    # Blend between three colors for rainbow effect
                                    if rel_pos < 0.33:
                                        blend_factor = rel_pos / 0.33
                                        r = int(color1[0] * (1 - blend_factor) + color2[0] * blend_factor)
                                        g = int(color1[1] * (1 - blend_factor) + color2[1] * blend_factor)
                                        b = int(color1[2] * (1 - blend_factor) + color2[2] * blend_factor)
                                    elif rel_pos < 0.66:
                                        blend_factor = (rel_pos - 0.33) / 0.33
                                        r = int(color2[0] * (1 - blend_factor) + color3[0] * blend_factor)
                                        g = int(color2[1] * (1 - blend_factor) + color3[1] * blend_factor)
                                        b = int(color2[2] * (1 - blend_factor) + color3[2] * blend_factor)
                                    else:
                                        blend_factor = (rel_pos - 0.66) / 0.34
                                        r = int(color3[0] * (1 - blend_factor) + color1[0] * blend_factor)
                                        g = int(color3[1] * (1 - blend_factor) + color1[1] * blend_factor)
                                        b = int(color3[2] * (1 - blend_factor) + color1[2] * blend_factor)
                                    
                                    gradient_color = (r, g, b)
                                    
                                    # Draw diagonal line
                                    start_x = max(0, i - block_rect.height)
                                    end_x = min(block_rect.width, i)
                                    start_y = max(0, block_rect.height - i)
                                    end_y = min(block_rect.height, 2 * block_rect.height - i)
                                    
                                    if start_x < end_x and start_y < end_y:
                                        pygame.draw.line(gradient_rect, gradient_color, 
                                                        (start_x, start_y), (end_x, end_y), 2)
                                
                                screen.blit(gradient_rect, block_rect)
                                
                                # Add animated scanline effect with color cycling
                                scanline_offset = int((time_val * 50) % 8)
                                for i in range(scanline_offset, block_rect.height, 4):
                                    scanline_color = tuple(int(c * 0.7) for c in hsv_to_rgb((base_hue + i/block_rect.height) % 1.0, 1.0, 1.0))
                                    scanline = pygame.Rect(block_rect.left, block_rect.top + i, block_rect.width, 2)
                                    pygame.draw.rect(screen, scanline_color + (150,), scanline)
                                    
                                # Add flashing border with color cycling
                                border_hue = (base_hue + math.sin(time_val * 8) * 0.2) % 1.0
                                border_color = tuple(int(c * 255) for c in hsv_to_rgb(border_hue, 1.0, 1.0))
                                border_width = 1 + int(math.sin(time_val * 10) * 1.5)
                                pygame.draw.rect(screen, border_color, block_rect, border_width, border_radius=3)
                                
                                # Add corner highlights that pulse
                                corner_size = 3 + int(math.sin(time_val * 15) * 2)
                                corner_hue = (tertiary_hue + 0.5) % 1.0
                                corner_color = tuple(int(c * 255) for c in hsv_to_rgb(corner_hue, 1.0, 1.0))
                                pygame.draw.circle(screen, corner_color, (block_rect.left + 2, block_rect.top + 2), corner_size)
                                pygame.draw.circle(screen, corner_color, (block_rect.right - 2, block_rect.bottom - 2), corner_size)
                                
                            elif effect == "sparkle":
                                # Get time value for animations
                                time_val = time.time()
                                
                                # Create a color-cycling base for the block
                                base_hue = (time_val * 0.3) % 1.0
                                
                                # Convert HSV to RGB for colors
                                def hsv_to_rgb(h, s, v):
                                    h_i = int(h * 6)
                                    f = h * 6 - h_i
                                    p = v * (1 - s)
                                    q = v * (1 - f * s)
                                    t = v * (1 - (1 - f) * s)
                                    
                                    if h_i == 0: return (v, t, p)
                                    if h_i == 1: return (q, v, p)
                                    if h_i == 2: return (p, v, t)
                                    if h_i == 3: return (p, q, v)
                                    if h_i == 4: return (t, p, v)
                                    return (v, p, q)
                                
                                # Cycle through colors for the base
                                base_color = tuple(int(c * 255) for c in hsv_to_rgb(base_hue, 0.7, 0.8))
                                pygame.draw.rect(screen, base_color, block_rect, border_radius=3)
                                
                                # Add animated electric circuit pattern
                                circuit_time = time_val * 3
                                
                                # Draw horizontal electric lines that pulse and change color
                                for i in range(0, block_rect.height, 4):
                                    # Offset based on time and position
                                    offset = int(math.sin(circuit_time + i * 0.2) * 5)
                                    line_width = int(1.5 + math.sin(circuit_time * 2 + i * 0.3) * 1.5)
                                    
                                    # Color cycling for each line
                                    line_hue = (base_hue + 0.5 + i / (block_rect.height * 3)) % 1.0
                                    line_color = tuple(int(c * 255) for c in hsv_to_rgb(line_hue, 1.0, 1.0))
                                    
                                    # Draw the pulsing line with offset
                                    start_x = block_rect.left + max(0, offset)
                                    end_x = block_rect.right - max(0, -offset)
                                    if start_x < end_x:
                                        line_rect = pygame.Rect(start_x, block_rect.top + i, end_x - start_x, line_width)
                                        pygame.draw.rect(screen, line_color, line_rect)
                                
                                # Draw vertical electric lines
                                for i in range(0, block_rect.width, 4):
                                    offset = int(math.cos(circuit_time + i * 0.2) * 5)
                                    line_width = int(1.5 + math.cos(circuit_time * 2 + i * 0.3) * 1.5)
                                    
                                    line_hue = (base_hue + 0.25 + i / (block_rect.width * 3)) % 1.0
                                    line_color = tuple(int(c * 255) for c in hsv_to_rgb(line_hue, 1.0, 1.0))
                                    
                                    start_y = block_rect.top + max(0, offset)
                                    end_y = block_rect.bottom - max(0, -offset)
                                    if start_y < end_y:
                                        line_rect = pygame.Rect(block_rect.left + i, start_y, line_width, end_y - start_y)
                                        pygame.draw.rect(screen, line_color, line_rect)
                                
                                # Add super intense sparkle effect
                                sparkle_chance = 0.7 + 0.3 * math.sin(time_val * 5)  # Higher chance for sparkles
                                if random.random() < sparkle_chance:
                                    # More sparkles
                                    for _ in range(random.randint(4, 8)):
                                        # Random position within block
                                        sparkle_pos = (
                                            random.randint(block_rect.left, block_rect.right),
                                            random.randint(block_rect.top, block_rect.bottom)
                                        )
                                        
                                        # Larger, more varied sparkle sizes
                                        sparkle_size = random.randint(2, 6)
                                        
                                        # Colorful sparkles instead of just white
                                        sparkle_hue = random.random()  # Random color
                                        sparkle_sat = random.uniform(0.5, 1.0)  # Random saturation
                                        sparkle_val = random.uniform(0.8, 1.0)  # High value for brightness
                                        sparkle_color = tuple(int(c * 255) for c in hsv_to_rgb(sparkle_hue, sparkle_sat, sparkle_val))
                                        
                                        # Draw the colorful sparkle
                                        pygame.draw.circle(screen, sparkle_color, sparkle_pos, sparkle_size)
                                        
                                        # Add a glow around the sparkle
                                        glow_size = sparkle_size + random.randint(1, 3)
                                        glow_color = tuple(list(sparkle_color) + [100])  # Semi-transparent
                                        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                                        pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                                        screen.blit(glow_surf, (sparkle_pos[0] - glow_size, sparkle_pos[1] - glow_size))
                                        
                                        # Add multiple particles from each sparkle
                                        for _ in range(random.randint(2, 5)):
                                            particle_speed = 1.0 + random.random() * 2.5  # Faster particles
                                            angle = random.uniform(0, 2 * math.pi)
                                            
                                            # Particles inherit sparkle color with slight variation
                                            particle_hue = (sparkle_hue + random.uniform(-0.1, 0.1)) % 1.0
                                            particle_color = tuple(int(c * 255) for c in hsv_to_rgb(particle_hue, sparkle_sat, sparkle_val))
                                            
                                            self.particles.append({
                                                'x': sparkle_pos[0],
                                                'y': sparkle_pos[1],
                                                'dx': math.cos(angle) * particle_speed,
                                                'dy': math.sin(angle) * particle_speed,
                                                'size': random.uniform(1.5, 4.0),  # Larger particles
                                                'color': particle_color,
                                                'life': random.uniform(0.6, 1.5)  # Longer life
                                            })
                            else:  # Cyberpunk wireframe effect
                                # Base color with pulsing intensity
                                pulse_factor = 0.7 + 0.3 * math.sin(time.time() * 3)
                                pulsed_color = tuple(int(c * pulse_factor) for c in color)
                                pygame.draw.rect(screen, pulsed_color, block_rect, border_radius=3)
                                
                                # Draw animated wireframe lines
                                wire_color = self.lighten_color(color, 100 + int(50 * math.sin(time.time() * 4)))
                                pygame.draw.rect(screen, wire_color, block_rect, 1, border_radius=3)
                                
                                # Add animated diagonal lines
                                line_offset = int((time.time() * 3) % 8) - 4
                                for i in range(-4, block_rect.width + 4, 8):
                                    pos = (i + line_offset) % (block_rect.width + 8) - 4
                                    pygame.draw.line(screen, wire_color, 
                                                   (block_rect.left + pos, block_rect.top),
                                                   (block_rect.left + pos + 8, block_rect.bottom), 1)
                                
                                # Add glowing dots at corners that pulse
                                dot_size = 2 + int(math.sin(time.time() * 5) * 1.5)
                                pygame.draw.circle(screen, wire_color, (block_rect.left + 2, block_rect.top + 2), dot_size)
                                pygame.draw.circle(screen, wire_color, (block_rect.right - 2, block_rect.top + 2), dot_size)
                                pygame.draw.circle(screen, wire_color, (block_rect.left + 2, block_rect.bottom - 2), dot_size)
                                pygame.draw.circle(screen, wire_color, (block_rect.right - 2, block_rect.bottom - 2), dot_size)
                        else:
                            # Enhanced standard block drawing
                            pygame.draw.rect(screen, color, block_rect, border_radius=3)
                            
                            # Add pulsing inner glow
                            inner_rect = pygame.Rect(
                                block_rect.left + 3,
                                block_rect.top + 3,
                                block_rect.width - 6,
                                block_rect.height - 6
                            )
                            inner_color = self.lighten_color(color, 30 + int(20 * self.grid_glow))
                            pygame.draw.rect(screen, inner_color, inner_rect, border_radius=2)
                        
                        # Draw enhanced highlight (top-left edges)
                        highlight_points = [
                            (block_rect.left, block_rect.bottom - 3),
                            (block_rect.left, block_rect.top),
                            (block_rect.right - 3, block_rect.top)
                        ]
                        pygame.draw.polygon(screen, self.lighten_color(color, 80), highlight_points)
                        
                        # Draw enhanced shadow (bottom-right edges)
                        shadow_points = [
                            (block_rect.left + 3, block_rect.bottom),
                            (block_rect.right, block_rect.bottom),
                            (block_rect.right, block_rect.top + 3)
                        ]
                        pygame.draw.polygon(screen, self.darken_color(color, 80), shadow_points)
                        
                        # Occasionally emit particles from the active piece
                        if random.random() < 0.05:  # 5% chance per block per frame
                            edge = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
                            if edge == 0:  # Top
                                particle_x = random.randint(block_rect.left, block_rect.right)
                                particle_y = block_rect.top
                                particle_dy = random.uniform(-2, -0.5)
                                particle_dx = random.uniform(-1, 1)
                            elif edge == 1:  # Right
                                particle_x = block_rect.right
                                particle_y = random.randint(block_rect.top, block_rect.bottom)
                                particle_dx = random.uniform(0.5, 2)
                                particle_dy = random.uniform(-1, 1)
                            elif edge == 2:  # Bottom
                                particle_x = random.randint(block_rect.left, block_rect.right)
                                particle_y = block_rect.bottom
                                particle_dy = random.uniform(0.5, 2)
                                particle_dx = random.uniform(-1, 1)
                            else:  # Left
                                particle_x = block_rect.left
                                particle_y = random.randint(block_rect.top, block_rect.bottom)
                                particle_dx = random.uniform(-2, -0.5)
                                particle_dy = random.uniform(-1, 1)
                                
                            # Add the particle
                            self.particles.append({
                                'x': particle_x,
                                'y': particle_y,
                                'dx': particle_dx,
                                'dy': particle_dy,
                                'size': random.uniform(1, 3),
                                'color': self.lighten_color(color, 100),
                                'life': random.uniform(0.5, 1.0)
                            })
                        
                        # Draw ghost piece (preview of where piece will land)
                        ghost_y = self.current_piece.y
                        while self.valid_position(self.current_piece, y_offset=ghost_y - self.current_piece.y + 1):
                            ghost_y += 1
                        
                        if ghost_y > self.current_piece.y:
                            ghost_rect = pygame.Rect(
                                self.x_offset + (self.current_piece.x + x) * GRID_SIZE + 3,
                                self.y_offset + (ghost_y + y) * GRID_SIZE + 3,
                                GRID_SIZE - 6, GRID_SIZE - 6
                            )
                            ghost_color = tuple(max(0, c - 100) for c in color)  # Darker version
                            pygame.draw.rect(screen, ghost_color, ghost_rect, 1, border_radius=1)
        
        # Draw next piece preview with y_offset
        preview_offset_x = self.x_offset + GRID_WIDTH * GRID_SIZE + 20
        preview_offset_y = self.y_offset + 50
        
        # Draw preview box
        pygame.draw.rect(
            screen,
            WHITE,
            (preview_offset_x, preview_offset_y, PREVIEW_SIZE * GRID_SIZE, PREVIEW_SIZE * GRID_SIZE),
            1
        )
        
        # Draw next piece in preview
        next_shape = self.next_piece.shape
        shape_height = len(next_shape)
        shape_width = len(next_shape[0])
        
        for y, row in enumerate(next_shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen,
                        self.next_piece.color,
                        (preview_offset_x + (x + (PREVIEW_SIZE - shape_width) // 2) * GRID_SIZE + 1,
                         preview_offset_y + (y + (PREVIEW_SIZE - shape_height) // 2) * GRID_SIZE + 1,
                         GRID_SIZE - 2, GRID_SIZE - 2)
                    )
        
        # Draw score, level, and lines in bottom right corner
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        lines_text = font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        
        # Calculate positions for bottom right corner
        bottom_right_x = self.x_offset + GRID_WIDTH * GRID_SIZE - max(score_text.get_width(), level_text.get_width(), lines_text.get_width())
        bottom_right_y = self.y_offset + GRID_HEIGHT * GRID_SIZE + 10
        
        # Draw text in bottom right corner
        screen.blit(score_text, (bottom_right_x, bottom_right_y))
        screen.blit(level_text, (bottom_right_x, bottom_right_y + 30))
        screen.blit(lines_text, (bottom_right_x, bottom_right_y + 60))
        
        # Draw game over text
        if self.game_over:
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (self.x_offset + GRID_WIDTH * GRID_SIZE // 2 - game_over_text.get_width() // 2, 
                                         self.y_offset + GRID_HEIGHT * GRID_SIZE // 2 - game_over_text.get_height() // 2))
            
            # Draw a small "Back to Menu" button below the game over text
            menu_btn_text = font.render("Back to Menu", True, (200, 200, 255))
            menu_btn_rect = pygame.Rect(
                self.x_offset + GRID_WIDTH * GRID_SIZE // 2 - 75,
                self.y_offset + GRID_HEIGHT * GRID_SIZE // 2 + 50,
                150, 40
            )
            # Check if mouse is hovering over the button
            mouse_pos = pygame.mouse.get_pos()
            if menu_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (100, 100, 180), menu_btn_rect, border_radius=5)
            else:
                pygame.draw.rect(screen, (60, 60, 120), menu_btn_rect, border_radius=5)
                
            screen.blit(menu_btn_text, (menu_btn_rect.centerx - menu_btn_text.get_width() // 2,
                                       menu_btn_rect.centery - menu_btn_text.get_height() // 2))
            
            # Store the button rect for click detection
            self.menu_button_rect = menu_btn_rect

    def handle_input(self, event):
        if self.game_over:
            # Check for menu button click if game is over
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                # Get the absolute mouse position
                mouse_pos = pygame.mouse.get_pos()
                print(f"Mouse clicked at {mouse_pos}, button rect: {self.menu_button_rect}")
                if self.menu_button_rect and self.menu_button_rect.collidepoint(mouse_pos):
                    print("Menu button clicked!")
                    return "menu"  # Signal to return to menu
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == self.controls["left"]:
                self.move(-1, 0)
            elif event.key == self.controls["right"]:
                self.move(1, 0)
            elif event.key == self.controls["down"]:
                self.move(0, 1)
            elif event.key == self.controls["rotate"]:
                self.rotate_piece()
            elif event.key == self.controls["hard_drop"]:
                self.hard_drop()

class StoreButton(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, font):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        
        # Store button colors
        self.normal_color = (255, 215, 0)  # Gold color for store
        self.hover_color = (255, 255, 0)  # Brighter yellow on hover
        self.text_color = (0, 0, 0)  # Black text for contrast
        self.hover_text_color = (0, 0, 0)  # Black
        self.bg_color = (50, 50, 70)  # Dark background
        self.roof_color = (200, 60, 60)  # Red roof
        self.wall_color = (240, 230, 180)  # Beige walls
        
        # Spark animation properties
        self.sparks = []
        self.spark_timer = 0
        self.spark_interval = 0.1  # Time between spark generation (faster)
        self.spark_colors = [(255, 255, 0), (255, 215, 0), (255, 165, 0)]  # Yellow to orange colors
        
        # Text rendering
        self.rendered_text = self.font.render(text, True, self.text_color)
        self.hover_rendered_text = self.font.render(text, True, self.hover_text_color)
        self.text_rect = self.rendered_text.get_rect()
        self.text_rect.centerx = self.rect.centerx
        self.text_rect.bottom = self.rect.bottom - 5
        
        # Animation properties
        self.shadow_offset = 4
        self.animation_progress = 0
        self.animation_speed = 0.2
        self.pulse_animation = 0
        self.pulse_direction = 1
        self.pulse_speed = 0.02
        self.glow_size = 0
        
        # Load chip count
        self.line_chips = get_line_chips()
    
    def update(self, dt=1/60):
        # Update pulse animation
        self.pulse_animation += self.pulse_speed * self.pulse_direction
        if self.pulse_animation > 1:
            self.pulse_animation = 1
            self.pulse_direction = -1
        elif self.pulse_animation < 0:
            self.pulse_animation = 0
            self.pulse_direction = 1
        
        # Update spark animation
        self.spark_timer += dt
        if self.spark_timer >= self.spark_interval:
            self.spark_timer = 0
            # Add new spark
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            size = random.randint(2, 4)
            color = random.choice(self.spark_colors)
            lifetime = random.uniform(0.5, 1.5)
            self.sparks.append({
                'x': self.rect.centerx + random.randint(-self.rect.width//3, self.rect.width//3),
                'y': self.rect.centery + random.randint(-self.rect.height//3, self.rect.height//3),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': size,
                'color': color,
                'lifetime': lifetime,
                'time': 0
            })
        
        # Update existing sparks
        for spark in self.sparks.copy():
            spark['time'] += dt
            spark['x'] += spark['vx']
            spark['y'] += spark['vy']
            
            # Remove sparks that have exceeded their lifetime
            if spark['time'] >= spark['lifetime']:
                self.sparks.remove(spark)
        
        # Update line chip count
        self.line_chips = get_line_chips()
    
    def draw(self, screen):
        # Draw sparks behind the button (electric effect)
        for spark in self.sparks:
            alpha = 255 * (1 - spark['time'] / spark['lifetime'])  # Fade out over time
            size = int(spark['size'] * (1 - spark['time'] / spark['lifetime'] * 0.5))  # Shrink slightly
            
            # Create a surface for the spark with alpha
            spark_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(spark_surface, (*spark['color'], alpha), (size, size), size)
            screen.blit(spark_surface, (spark['x'] - size, spark['y'] - size))
        
        # Draw button shadow
        shadow_rect = pygame.Rect(self.rect.x + self.shadow_offset, 
                                self.rect.y + self.shadow_offset,
                                self.rect.width, self.rect.height)
        pygame.draw.rect(screen, (30, 30, 50), shadow_rect, border_radius=0)
        
        # Draw base button (background)
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=0)
        
        # Calculate house dimensions
        house_width = self.rect.width - 20
        house_height = self.rect.height - 40
        house_x = self.rect.x + 10
        house_y = self.rect.y + 15
        
        # Draw house walls
        wall_rect = pygame.Rect(house_x, house_y + house_height//3, house_width, house_height*2//3)
        pygame.draw.rect(screen, self.wall_color, wall_rect)
        
        # Draw house roof (triangle)
        roof_points = [
            (house_x, house_y + house_height//3),
            (house_x + house_width//2, house_y),
            (house_x + house_width, house_y + house_height//3)
        ]
        pygame.draw.polygon(screen, self.roof_color, roof_points)
        
        # Draw door
        door_width = house_width // 4
        door_height = house_height // 3
        door_x = house_x + (house_width - door_width) // 2
        door_y = house_y + house_height - door_height
        pygame.draw.rect(screen, (120, 80, 40), (door_x, door_y, door_width, door_height))
        
        # Draw door knob
        knob_x = door_x + door_width - 5
        knob_y = door_y + door_height // 2
        pygame.draw.circle(screen, (255, 215, 0), (knob_x, knob_y), 3)
        
        # Draw windows
        window_size = house_width // 6
        window_y = house_y + house_height//3 + window_size
        # Left window
        pygame.draw.rect(screen, (200, 230, 255), (house_x + window_size, window_y, window_size, window_size))
        # Right window
        pygame.draw.rect(screen, (200, 230, 255), (house_x + house_width - window_size*2, window_y, window_size, window_size))
        
        # Draw window frames
        pygame.draw.line(screen, (100, 100, 100), (house_x + window_size, window_y + window_size//2), 
                        (house_x + window_size*2, window_y + window_size//2), 1)
        pygame.draw.line(screen, (100, 100, 100), (house_x + window_size + window_size//2, window_y), 
                        (house_x + window_size + window_size//2, window_y + window_size), 1)
        pygame.draw.line(screen, (100, 100, 100), (house_x + house_width - window_size*2, window_y + window_size//2), 
                        (house_x + house_width - window_size, window_y + window_size//2), 1)
        pygame.draw.line(screen, (100, 100, 100), (house_x + house_width - window_size*2 + window_size//2, window_y), 
                        (house_x + house_width - window_size*2 + window_size//2, window_y + window_size), 1)
        
        # Draw shop sign
        sign_width = house_width * 3 // 4
        sign_height = 20
        sign_x = house_x + (house_width - sign_width) // 2
        sign_y = house_y + house_height//3 - sign_height - 5
        pygame.draw.rect(screen, (50, 50, 150), (sign_x, sign_y, sign_width, sign_height))
        
        # Draw sign text
        sign_font = pygame.font.Font(None, 18)
        sign_text = sign_font.render("SHOP", True, (255, 255, 255))
        sign_text_rect = sign_text.get_rect(center=(sign_x + sign_width//2, sign_y + sign_height//2))
        screen.blit(sign_text, sign_text_rect)
        
        # Draw electric glow around the button when hovered
        if self.is_hovered:
            glow_size = 4 + int(2 * math.sin(self.pulse_animation * math.pi * 2))
            for i in range(glow_size):
                glow_rect = pygame.Rect(
                    self.rect.x - i, 
                    self.rect.y - i,
                    self.rect.width + i*2, 
                    self.rect.height + i*2
                )
                alpha = 150 - i * 20
                if alpha > 0:
                    glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surface, (255, 255, 0, alpha), 
                                    (0, 0, glow_rect.width, glow_rect.height), 1)
                    screen.blit(glow_surface, (glow_rect.x, glow_rect.y))
        
        # Draw text below house
        text_color = self.hover_text_color if self.is_hovered else self.text_color
        text_to_render = self.font.render(self.text, True, text_color)
        text_rect = text_to_render.get_rect(center=(self.rect.centerx, self.rect.bottom - 15))
        screen.blit(text_to_render, text_rect)
        
        # Draw LineChips count
        chips_text = pygame.font.Font(None, 20).render(f"Chips: {self.line_chips}", True, (255, 255, 255))
        chips_rect = chips_text.get_rect(center=(self.rect.centerx, self.rect.bottom + 10))
        screen.blit(chips_text, chips_rect)
        
        # Draw border with pixelated 8-bit style
        border_width = 4 if self.is_hovered else 3
        border_color = (255, 255, 0) if self.is_hovered else self.normal_color
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=0)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            # Use polygon collision detection instead of rectangle
            mouse_pos = event.pos
            if self.shape_type == "circle":
                # For circle, use distance calculation
                center_x = self.rect.x + self.rect.width // 2
                center_y = self.rect.y + self.rect.height // 2
                radius = min(self.rect.width, self.rect.height) // 2
                distance = math.sqrt((mouse_pos[0] - center_x)**2 + (mouse_pos[1] - center_y)**2)
                self.is_hovered = distance <= radius
            else:
                # For other shapes, use polygon point-in-polygon test
                self.is_hovered = self.point_in_polygon(mouse_pos, self.shape_points)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False
        
    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

class Button:
    def __init__(self, x, y, width, height, text, font, image_name=None, image_subfolder=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        self.animation_progress = 0.0  # Animation progress for hover effects
        self.animation_speed = 0.1     # Speed of the hover animation
        
        # Pulse animation attributes
        self.pulse_animation = 0.0
        self.pulse_speed = 0.05
        self.pulse_direction = 1
        self.pulse_min = 0.2
        self.pulse_max = 1.0
        
        # Glitch effect attributes
        self.glitch_active = False
        self.glitch_timer = 0
        self.glitch_duration = 0.1
        self.glitch_interval = random.uniform(2.0, 5.0)
        
        # Glow effect attributes
        self.glow_size = 20  # Increased glow size for more dramatic effect
        self.shadow_offset = 5  # Larger shadow for more depth
        
        # Scanline effect attributes
        self.scanline_offset = 0
        self.scanline_speed = 30
        self.scanline_height = 2
        self.scanline_alpha = 40
        
        # Image attributes
        self.image_name = image_name
        self.image_subfolder = image_subfolder
        self.image = None
        
        # Determine appropriate subfolder based on button type if not specified
        if not self.image_subfolder and self.image_name:
            if "Standard" in text and "Duel" not in text:
                self.image_subfolder = "buttons/standard"
            elif "Duel" in text:
                self.image_subfolder = "buttons/duel"
            elif "Gesture" in text:
                self.image_subfolder = "buttons/gesture"
            elif "Controls" in text:
                self.image_subfolder = "buttons/controls"
        
        # Load the image if specified
        if image_name:
            print(f"Loading image: {image_name} from subfolder: {self.image_subfolder}")
            try:
                full_path = os.path.join(IMAGES_DIR, self.image_subfolder, image_name)
                print(f"Full image path: {full_path}")
                print(f"File exists: {os.path.exists(full_path)}")
                
                if os.path.exists(full_path):
                    self.image = pygame.image.load(full_path).convert_alpha()
                    print(f"Successfully loaded image: {image_name}")
                    # Scale image to fit button
                    self.image = pygame.transform.scale(self.image, (width, height))
                else:
                    print(f"File not found: {full_path}")
            except Exception as e:
                print(f"Error loading image: {e}")
        
        # Create a custom shape based on button type
        if "Standard" in text and "Duel" not in text:
            # Standard mode - hexagon shape
            self.shape_type = "hexagon"
            self.shape_points = self.create_hexagon_points(x, y, width, height)
            self.normal_color = CYAN
            self.hover_color = BRIGHT_CYAN
            self.glow_color = BRIGHT_CYAN
        elif "The GeTrix Gauntlet" in text:
            # The GeTrix Gauntlet mode - jagged star shape
            self.shape_type = "hellstar"
            self.shape_points = self.create_hellstar_points(x, y, width, height)
            self.normal_color = RED
            self.hover_color = (255, 100, 100)  # Bright red
            self.glow_color = (255, 50, 50)  # Even brighter red
        elif "Duel" in text:
            # Duel mode - diamond shape
            self.shape_type = "diamond"
            self.shape_points = self.create_diamond_points(x, y, width, height)
            self.normal_color = MAGENTA
            self.hover_color = BRIGHT_MAGENTA
            self.glow_color = BRIGHT_MAGENTA
        elif "Controls" in text or "Gesture" in text:
            # Controller shape for controls
            self.shape_type = "controller"
            self.shape_points = self.create_controller_points(x, y, width, height)
            self.normal_color = YELLOW
            self.hover_color = BRIGHT_YELLOW
            self.glow_color = BRIGHT_YELLOW
        else:
            # Default to circular shape
            self.shape_type = "circle"
            self.shape_points = self.create_circle_points(x, y, width, height)
            self.normal_color = GREEN
            self.hover_color = BRIGHT_GREEN
            self.glow_color = BRIGHT_GREEN
            
        # Set text colors
        self.text_color = WHITE
        self.hover_text_color = BRIGHT_WHITE
        
        # Set background color
        self.bg_color = DARK_GRAY
            
        # Create collision polygon for mouse detection
        self.collision_poly = self.shape_points.copy()
        
        # Create circuit pattern for cyberpunk effect
        self.circuit_pattern = []
        
    def create_hexagon_points(self, x, y, width, height):
        # Create a hexagon shape
        points = []
        center_x = x + width // 2
        center_y = y + height // 2
        radius = min(width, height) // 2
        
        for i in range(6):
            angle = math.pi / 3 * i
            px = center_x + int(radius * math.cos(angle))
            py = center_y + int(radius * math.sin(angle))
            points.append((px, py))
        return points
    
    def create_diamond_points(self, x, y, width, height):
        # Create a diamond shape
        center_x = x + width // 2
        center_y = y + height // 2
        radius_x = width // 2
        radius_y = height // 2
        
        points = [
            (center_x, center_y - radius_y),  # Top
            (center_x + radius_x, center_y),  # Right
            (center_x, center_y + radius_y),  # Bottom
            (center_x - radius_x, center_y)   # Left
        ]
        return points
    
    def create_hellstar_points(self, x, y, width, height):
        # Create a jagged star shape for The GeTrix Gauntlet mode
        points = []
        center_x = x + width // 2
        center_y = y + height // 2
        outer_radius = min(width, height) // 2
        inner_radius = outer_radius * 0.5
        spikes = 8  # Number of spikes
        
        for i in range(spikes * 2):
            angle = math.pi * i / spikes
            radius = outer_radius if i % 2 == 0 else inner_radius
            px = center_x + int(radius * math.cos(angle))
            py = center_y + int(radius * math.sin(angle))
            points.append((px, py))
        return points
    
    def create_controller_points(self, x, y, width, height):
        # Create a game controller shape
        center_x = x + width // 2
        center_y = y + height // 2
        w = width // 2
        h = height // 2
        
        # Controller with rounded sides
        points = [
            (center_x - w, center_y - h//2),      # Top left
            (center_x - w//2, center_y - h),      # Left top curve
            (center_x + w//2, center_y - h),      # Right top curve
            (center_x + w, center_y - h//2),      # Top right
            (center_x + w, center_y + h//2),      # Bottom right
            (center_x + w//2, center_y + h),      # Right bottom curve
            (center_x - w//2, center_y + h),      # Left bottom curve
            (center_x - w, center_y + h//2)       # Bottom left
        ]
        return points
    
    def create_circle_points(self, x, y, width, height):
        # Approximate a circle with polygon points
        points = []
        center_x = x + width // 2
        center_y = y + height // 2
        radius = min(width, height) // 2
        
        # Use 12 points to approximate a circle
        for i in range(12):
            angle = 2 * math.pi * i / 12
            px = center_x + int(radius * math.cos(angle))
            py = center_y + int(radius * math.sin(angle))
            points.append((px, py))
        return points
        
        # Define cyberpunk neon colors based on button type
        if "Standard" in text and "Duel" not in text:
            # Standard mode - cyan neon
            self.shape_type = "square"
            self.normal_color = (0, 210, 255)  # Cyan neon
            self.glow_color = (50, 230, 255)  # Brighter cyan for glow
        elif "Duel" in text:
            # Duel mode - magenta neon
            self.shape_type = "diamond"
            self.normal_color = (255, 0, 150)  # Magenta neon
            self.glow_color = (255, 50, 180)  # Brighter magenta for glow
        else:  # Gesture Mode
            # Gesture mode - green neon
            self.shape_type = "hexagon"
            self.normal_color = (0, 255, 130)  # Green neon
            self.glow_color = (50, 255, 150)  # Brighter green for glow
        
        # High contrast colors with cyberpunk feel
        self.hover_color = tuple(min(255, c + 70) for c in self.normal_color)
        self.text_color = (255, 255, 255)  # White text for better contrast
        self.hover_text_color = (255, 255, 255)  # White
        self.bg_color = (10, 10, 25)  # Dark background for better neon contrast
        
        # Text rendering with glow effect
        self.rendered_text = self.font.render(text, True, self.text_color)
        self.hover_rendered_text = self.font.render(text, True, self.hover_text_color)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)
        
        # Animation properties
        self.shadow_offset = 4
        self.animation_progress = 0
        self.animation_speed = 0.2
        self.pulse_animation = 0
        self.pulse_direction = 1
        self.pulse_speed = 0.02
        self.glow_size = 0
        
        # Cyberpunk-specific properties
        self.scanline_offset = 0
        self.scanline_speed = 30  # Pixels per second
        self.glitch_timer = 0
        self.glitch_interval = random.uniform(1.5, 3.0)  # Random interval between glitches
        self.glitch_duration = 0
        self.glitch_active = False
        self.circuit_pattern = []
        
        # Generate circuit pattern lines (decorative elements)
        num_lines = random.randint(3, 6)
        for _ in range(num_lines):
            start_x = random.randint(0, width)
            start_y = random.randint(0, height)
            length = random.randint(10, 30)
            direction = random.choice([(1, 0), (0, 1), (1, 1), (-1, 1)])
            self.circuit_pattern.append({
                "start": (start_x, start_y),
                "length": length,
                "direction": direction,
                "width": random.randint(1, 2),
                "color": self.normal_color
            })
        
    def update(self, dt=1/60):
        # Smooth hover animation
        target = 1 if self.is_hovered else 0
        self.animation_progress += (target - self.animation_progress) * self.animation_speed
        
        # Pulse animation for all buttons
        self.pulse_animation += self.pulse_speed * self.pulse_direction
        if self.pulse_animation > 1:
            self.pulse_animation = 1
            self.pulse_direction = -1
        elif self.pulse_animation < 0:
            self.pulse_animation = 0
            self.pulse_direction = 1
            
        # Calculate glow size based on hover and pulse
        self.glow_size = 4 + (6 * self.animation_progress) + (self.pulse_animation * 3)
        
        # Update scanline animation
        self.scanline_offset = (self.scanline_offset + self.scanline_speed * dt) % (self.rect.height * 2)
        
        # Update glitch effect
        self.glitch_timer += dt
        if not self.glitch_active and self.glitch_timer > self.glitch_interval:
            # Start a new glitch
            self.glitch_active = True
            self.glitch_duration = random.uniform(0.05, 0.2)  # Short glitch duration
            self.glitch_timer = 0
        elif self.glitch_active:
            # Update active glitch
            if self.glitch_timer > self.glitch_duration:
                self.glitch_active = False
                self.glitch_timer = 0
                self.glitch_interval = random.uniform(1.5, 3.0)  # Reset interval

    def draw(self, screen):
        # Calculate the bounding box for our shape to determine surface size
        min_x = min(p[0] for p in self.shape_points)
        max_x = max(p[0] for p in self.shape_points)
        min_y = min(p[1] for p in self.shape_points)
        max_y = max(p[1] for p in self.shape_points)
        
        # Add padding for glow effects
        padding = int(self.glow_size * 2)
        surface_width = max_x - min_x + padding * 2
        surface_height = max_y - min_y + padding * 2
        
        # Create a surface for the button with alpha for glow effects
        button_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        
        # Adjust shape points for the surface coordinates
        adjusted_points = [(p[0] - min_x + padding, p[1] - min_y + padding) for p in self.shape_points]
        
        # Draw neon glow effect with enhanced intensity
        glow_intensity = 0.7 + 0.7 * self.pulse_animation  # Increased base intensity
        if self.is_hovered:
            glow_intensity += 0.5  # More dramatic hover effect
        
        # Draw multiple layers of glow with decreasing alpha
        for offset in range(int(self.glow_size), 0, -1):
            alpha = int(150 * (offset / self.glow_size) * glow_intensity)
            
            # Ensure glow_color is properly formatted
            if hasattr(self, 'glow_color') and self.glow_color is not None:
                # Convert to list to make it mutable
                glow_color = list(self.glow_color)
                
                # Make sure it's a valid RGB or RGBA color
                if len(glow_color) == 3:
                    glow_color.append(alpha)  # Add alpha to RGB
                elif len(glow_color) == 4:
                    glow_color[3] = alpha  # Update existing alpha
                else:
                    # Fallback to a default color if invalid
                    glow_color = (100, 200, 255, alpha)  # Cyan-blue with alpha
            else:
                # Fallback if glow_color is not defined
                glow_color = (100, 200, 255, alpha)  # Cyan-blue with alpha
            
            # Create expanded points for glow effect
            center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
            center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
            glow_points = []
            
            for px, py in adjusted_points:
                # Calculate vector from center to point
                dx = px - center_x
                dy = py - center_y
                # Normalize and scale by offset
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:  # Avoid division by zero
                    dx = dx / length * offset
                    dy = dy / length * offset
                # Add offset to original point
                glow_points.append((px + dx, py + dy))
            
            # Draw glow polygon with proper color format
            try:
                # Ensure glow_color is a valid RGB or RGBA tuple
                if isinstance(glow_color, (list, tuple)) and 3 <= len(glow_color) <= 4:
                    # Convert to tuple with proper values
                    glow_color_tuple = tuple(max(0, min(255, int(c))) for c in glow_color[:3])
                    if len(glow_color) == 4:
                        # Add clamped alpha value
                        alpha_value = max(0, min(255, int(glow_color[3])))
                        glow_color_tuple = glow_color_tuple + (alpha_value,)
                    
                    # Create a separate surface for the glow with alpha support
                    glow_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
                    pygame.draw.polygon(glow_surface, glow_color_tuple, glow_points)
                    button_surface.blit(glow_surface, (0, 0))
                else:
                    # Fallback to a safe color if invalid
                    fallback_color = (100, 200, 255, alpha)
                    glow_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
                    pygame.draw.polygon(glow_surface, fallback_color, glow_points)
                    button_surface.blit(glow_surface, (0, 0))
            except Exception as e:
                print(f"Glow drawing error: {e}")
                # Continue without drawing the glow if there's an error
        
        # Draw button shadow
        shadow_points = [(p[0] + self.shadow_offset, p[1] + self.shadow_offset) for p in adjusted_points]
        # Create shadow with proper color format
        shadow_color = (5, 5, 15, 150)  # Dark with alpha
        # Use surface with per-pixel alpha for shadow
        shadow_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        pygame.draw.polygon(shadow_surface, shadow_color, shadow_points)
        button_surface.blit(shadow_surface, (0, 0))
        
        # Draw base button shape
        if self.image:
            # If we have an image, use it instead of drawing a polygon
            print(f"Drawing button with image: {self.text}")
            # Calculate position to center the image
            img_x = surface_width // 2 - self.image.get_width() // 2
            img_y = surface_height // 2 - self.image.get_height() // 2
            button_surface.blit(self.image, (img_x, img_y))
        else:
            # Otherwise draw the polygon shape
            print(f"Drawing button with polygon shape: {self.text}")
            pygame.draw.polygon(button_surface, self.bg_color, adjusted_points)
        
        # Draw circuit pattern on button - adjusted for custom shape
        center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
        center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
        
        # Create more visible circuit patterns that follow the shape
        num_lines = len(adjusted_points)
        
        # Draw enhanced radial lines from center to vertices with dynamic effects
        for i in range(num_lines):
            # Connect center to each vertex with pulsing lines
            start_pos = (center_x, center_y)
            end_pos = adjusted_points[i]
            
            # Create a time-based pulse effect unique to each line
            time_offset = i / num_lines * math.pi
            pulse_effect = 0.7 + 0.5 * math.sin(time.time() * 4 + time_offset)
            
            # Create a color that shifts based on the pulse and position
            r, g, b = self.normal_color
            r = min(255, int(r * (0.8 + 0.4 * pulse_effect)))
            g = min(255, int(g * (0.8 + 0.4 * (1-pulse_effect))))
            b = min(255, int(b * (0.8 + 0.4 * pulse_effect)))
            
            # Add alpha based on pulse
            alpha = 150 + int(105 * self.pulse_animation)
            line_color = (r, g, b, alpha)
            
            # Calculate dynamic line width based on pulse
            line_width = max(2, int(3 * pulse_effect))
            
            # Draw main line with dynamic width
            pygame.draw.line(button_surface, line_color, start_pos, end_pos, line_width)
            
            # Draw subtle glow around the line
            glow_alpha = int(50 * pulse_effect)
            glow_color = (r, g, b, glow_alpha)
            pygame.draw.line(button_surface, glow_color, start_pos, end_pos, line_width + 2)
        
        # Add enhanced concentric shapes with dynamic effects
        if len(adjusted_points) > 2:  # Only for shapes with enough points
            # Use more scales for a more detailed pattern
            scales = [0.85, 0.7, 0.55, 0.4, 0.25]
            
            for idx, scale in enumerate(scales):
                # Create a time-based pulse effect unique to each shape
                time_offset = idx / len(scales) * math.pi
                shape_pulse = 0.7 + 0.3 * math.sin(time.time() * 3 + time_offset)
                
                # Add slight random variation to points for a more organic look
                inner_points = []
                for px, py in adjusted_points:
                    # Scale points toward center with slight variation
                    dx = px - center_x
                    dy = py - center_y
                    
                    # Add subtle variation based on time
                    variation = 0.03 * math.sin(time.time() * 2 + idx)
                    adjusted_scale = scale * (1 + variation)
                    
                    inner_px = center_x + dx * adjusted_scale
                    inner_py = center_y + dy * adjusted_scale
                    inner_points.append((inner_px, inner_py))
                
                # Create a color that shifts based on scale and time
                r, g, b = self.normal_color
                r = min(255, int(r * (0.7 + 0.3 * shape_pulse)))
                g = min(255, int(g * (0.7 + 0.3 * (1-shape_pulse))))
                b = min(255, int(b * (0.7 + 0.3 * shape_pulse)))
                
                # Add alpha based on pulse and scale
                alpha = int(80 + 120 * (1-scale) * self.pulse_animation * shape_pulse)
                inner_color = (r, g, b, alpha)
                
                # Calculate line width based on scale (thicker for outer shapes)
                line_width = max(1, int(2 * (1 - scale/2) * shape_pulse))
                
                # Draw inner shape with dynamic width
                pygame.draw.polygon(button_surface, inner_color, inner_points, line_width)
        
        # Add enhanced circuit dots at vertices with glow effects
        for i, point in enumerate(adjusted_points):
            # Create a time-based pulse effect unique to each dot
            time_offset = i / len(adjusted_points) * math.pi * 2
            dot_pulse = 0.7 + 0.5 * math.sin(time.time() * 5 + time_offset)
            
            # Calculate dynamic dot size based on pulse
            dot_radius = max(3, int(5 * dot_pulse))
            
            # Create a color that shifts based on pulse
            r, g, b = 220, 220, 255  # Bright bluish-white base
            r = min(255, int(r * dot_pulse))
            g = min(255, int(g * (0.8 + 0.2 * dot_pulse)))
            b = min(255, int(b * dot_pulse))
            dot_color = (r, g, b)
            
            # Draw outer glow for dots
            for radius in range(dot_radius + 4, dot_radius, -1):
                alpha = int(150 * (radius/(dot_radius + 4)) * dot_pulse)
                glow_color = (r, g, b, alpha)
                pygame.draw.circle(button_surface, glow_color, point, radius)
            
            # Draw main dot
            pygame.draw.circle(button_surface, dot_color, point, dot_radius)
            
            # Draw small inner highlight
            highlight_radius = max(1, int(dot_radius * 0.4))
            highlight_offset = int(dot_radius * 0.3)
            highlight_pos = (int(point[0] - highlight_offset), int(point[1] - highlight_offset))
            pygame.draw.circle(button_surface, (255, 255, 255, 200), highlight_pos, highlight_radius)
        
        # Get dynamic color based on hover state for button elements
        color = tuple(int(self.normal_color[i] + (self.hover_color[i] - self.normal_color[i]) * self.animation_progress) for i in range(3))
        
        # Draw different geometric shapes based on button type
        if self.shape_type == "square":
            # Cyberpunk Square: Draw layered squares with neon outlines and inner circuit break
            outer_size = min(self.rect.width, self.rect.height) // 3
            inner_size = outer_size * 0.7
            square_points = [
                (self.glow_size + self.rect.width // 2 - outer_size, self.glow_size + self.rect.height // 2 - outer_size),
                (self.glow_size + self.rect.width // 2 + outer_size, self.glow_size + self.rect.height // 2 - outer_size),
                (self.glow_size + self.rect.width // 2 + outer_size, self.glow_size + self.rect.height // 2 + outer_size),
                (self.glow_size + self.rect.width // 2 - outer_size, self.glow_size + self.rect.height // 2 + outer_size)
            ]
            pygame.draw.polygon(button_surface, color, square_points)
            notch = int(inner_size * 0.2)
            inner_points = [
                (self.glow_size + self.rect.width // 2 - inner_size + notch, self.glow_size + self.rect.height // 2 - inner_size),
                (self.glow_size + self.rect.width // 2 + inner_size - notch, self.glow_size + self.rect.height // 2 - inner_size),
                (self.glow_size + self.rect.width // 2 + inner_size, self.glow_size + self.rect.height // 2 - inner_size + notch),
                (self.glow_size + self.rect.width // 2 + inner_size, self.glow_size + self.rect.height // 2 + inner_size - notch),
                (self.glow_size + self.rect.width // 2 + inner_size - notch, self.glow_size + self.rect.height // 2 + inner_size),
                (self.glow_size + self.rect.width // 2 - inner_size + notch, self.glow_size + self.rect.height // 2 + inner_size),
                (self.glow_size + self.rect.width // 2 - inner_size, self.glow_size + self.rect.height // 2 + inner_size - notch),
                (self.glow_size + self.rect.width // 2 - inner_size, self.glow_size + self.rect.height // 2 - inner_size + notch)
            ]
            pygame.draw.polygon(button_surface, self.bg_color, inner_points)
        elif self.shape_type == "diamond":
            # Cyberpunk Diamond: Draw a rotated square with layered neon and glitch effects
            outer_size = min(self.rect.width, self.rect.height) // 3
            inner_size = outer_size * 0.6
            diamond_points = [
                (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 - outer_size),
                (self.glow_size + self.rect.width // 2 + outer_size, self.glow_size + self.rect.height // 2),
                (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 + outer_size),
                (self.glow_size + self.rect.width // 2 - outer_size, self.glow_size + self.rect.height // 2)
            ]
            pygame.draw.polygon(button_surface, color, diamond_points)
            inner_diamond = [
                (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 - inner_size),
                (self.glow_size + self.rect.width // 2 + inner_size, self.glow_size + self.rect.height // 2),
                (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 + inner_size),
                (self.glow_size + self.rect.width // 2 - inner_size, self.glow_size + self.rect.height // 2)
            ]
            pygame.draw.polygon(button_surface, self.bg_color, inner_diamond)
            pygame.draw.line(button_surface, color, (self.glow_size + self.rect.width // 2 - outer_size, self.glow_size + self.rect.height // 2), (self.glow_size + self.rect.width // 2 + outer_size, self.glow_size + self.rect.height // 2), 2)
            pygame.draw.line(button_surface, color, (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 - outer_size), (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2 + outer_size), 2)
        elif self.shape_type == "hexagon":
            # Cyberpunk Hexagon: Draw layered hexagon with a holographic inner hexagon
            outer_size = min(self.rect.width, self.rect.height) // 3
            hexagon_points = []
            for i in range(6):
                angle = math.pi / 3 * i + math.pi / 6
                x = self.glow_size + self.rect.width // 2 + outer_size * math.cos(angle)
                y = self.glow_size + self.rect.height // 2 + outer_size * math.sin(angle)
                hexagon_points.append((int(x), int(y)))
            pygame.draw.polygon(button_surface, color, hexagon_points)
            inner_points = []
            for i in range(6):
                angle = math.pi / 3 * i + math.pi / 6 + 0.2
                x = self.glow_size + self.rect.width // 2 + (outer_size * 0.7) * math.cos(angle)
                y = self.glow_size + self.rect.height // 2 + (outer_size * 0.7) * math.sin(angle)
                inner_points.append((int(x), int(y)))
            pygame.draw.polygon(button_surface, self.bg_color, inner_points)
        elif self.shape_type == "controller":
            # Cyberpunk Controller: Draw a futuristic game controller icon
            ctrl_size = min(self.rect.width, self.rect.height) // 3
            body_width = int(ctrl_size * 1.5)
            body_height = int(ctrl_size * 0.8)
            body_rect = pygame.Rect(
                self.glow_size + self.rect.width // 2 - body_width//2,
                self.glow_size + self.rect.height // 2 - body_height//2,
                body_width,
                body_height
            )
            pygame.draw.rect(button_surface, color, body_rect)
            pygame.draw.rect(button_surface, WHITE, body_rect, 2)
        else:
            # Fallback: Draw a circle with neon outline
            pygame.draw.circle(button_surface, color, (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2), min(self.rect.width, self.rect.height) // 3)
            pygame.draw.circle(button_surface, WHITE, (self.glow_size + self.rect.width // 2, self.glow_size + self.rect.height // 2), min(self.rect.width, self.rect.height) // 3, 3)
        
        # Add pixelated highlights for 8-bit effect
        lighter_color = tuple(min(255, c + 80) for c in color)  # Brighter highlight
        
        # Draw multiple square pixels for 8-bit highlight effect
        pixel_size = max(4, min(self.rect.width, self.rect.height) // 8)  # Larger, more visible pixels
        
        # Draw a pattern of square pixels
        for i in range(2):
            for j in range(2):
                if i == j:  # Only draw diagonal pixels for a more 8-bit look
                    pixel_x = self.glow_size + self.rect.width // 2 - min(self.rect.width, self.rect.height) // 3 + i * min(self.rect.width, self.rect.height) // 3
                    pixel_y = self.glow_size + self.rect.height // 2 - min(self.rect.width, self.rect.height) // 3 + j * min(self.rect.width, self.rect.height) // 3
                    pygame.draw.rect(button_surface, lighter_color, 
                                    pygame.Rect(pixel_x, pixel_y, pixel_size, pixel_size))
        
        # Draw border with pixelated 8-bit style for the custom shape
        border_width = 4 if self.is_hovered else 3  # Thicker border for 8-bit look
        border_color = WHITE if self.is_hovered else tuple(max(0, c - 30) for c in self.normal_color)
        
        # Draw the border on the screen directly using the original shape points
        pygame.draw.polygon(screen, border_color, self.shape_points, border_width)
        
        # Draw text with appropriate color and slight shadow for depth
        text_color = self.hover_text_color if self.is_hovered else self.text_color
        text_to_render = self.font.render(self.text, True, text_color)
        
        # Calculate center of the shape for text positioning
        shape_center_x = sum(p[0] for p in self.shape_points) / len(self.shape_points)
        shape_center_y = sum(p[1] for p in self.shape_points) / len(self.shape_points)
        
        # Center text within the shape, not below it
        text_rect = text_to_render.get_rect(center=(shape_center_x, shape_center_y))
        
        # Text shadow for better readability
        shadow_text_rect = text_rect.copy()
        shadow_text_rect.x += 2
        shadow_text_rect.y += 2
        shadow_text = self.font.render(self.text, True, DARK_GRAY)
        screen.blit(shadow_text, shadow_text_rect)
        
        # Main text
        screen.blit(text_to_render, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            # Use polygon collision detection instead of rectangle
            mouse_pos = event.pos
            if self.shape_type == "circle":
                # For circle, use distance calculation
                center_x = self.rect.x + self.rect.width // 2
                center_y = self.rect.y + self.rect.height // 2
                radius = min(self.rect.width, self.rect.height) // 2
                distance = math.sqrt((mouse_pos[0] - center_x)**2 + (mouse_pos[1] - center_y)**2)
                self.is_hovered = distance <= radius
            else:
                # For other shapes, use polygon point-in-polygon test
                self.is_hovered = self.point_in_polygon(mouse_pos, self.shape_points)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False
        
    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

def run_menu(screen, font, music_manager=None):
    # Start menu music if music manager is provided
    if music_manager:
        music_manager.play_music_for_mode('menu')
        
    # Create Settings button
    # Create fonts with appropriate sizes - larger for better readability
    title_font = pygame.font.Font(None, 120)
    subtitle_font = pygame.font.Font(None, 36)
    info_font = pygame.font.Font(None, 20)  # Larger font for instructions
    
    # Create buttons with Gesture Mode at top and other buttons to the left - larger size
    button_width, button_height = 280, 80
    
    # Create a button for Controls/Gestures in the top right (larger size)
    controls_btn_width, controls_btn_height = 240, 60
    controls_btn = Button(SCREEN_WIDTH - controls_btn_width - 20, 20, controls_btn_width, controls_btn_height, "Controls/Gestures", subtitle_font, 
                         image_name="image3-removebg-preview.png", image_subfolder="buttons/controls")
    controls_btn.shape_type = "controller"  # Special shape type for controller icon
    controls_btn.normal_color = (200, 200, 200)  # Light gray for info button
    
    # Create a Settings button below the Controls button
    settings_btn_width, settings_btn_height = 240, 60
    settings_btn = Button(SCREEN_WIDTH - settings_btn_width - 20, 90, settings_btn_width, settings_btn_height, "Settings", subtitle_font)
    settings_btn.normal_color = (0, 180, 180)  # Cyan color for settings
    
    # Create a Store button in the top left
    store_btn_width, store_btn_height = 120, 120
    store_btn = StoreButton(20, 20, store_btn_width, store_btn_height, "Store", subtitle_font)
    
    # Center all game mode buttons vertically, at an optimal position
    vertical_center = (SCREEN_HEIGHT * 2) // 3  # Moved down to ~67% of screen height
    button_spacing = button_height + 40  # Space between buttons
    
    # Standard mode button in the center
    single_player_btn = Button(SCREEN_WIDTH//2 - button_width//2, vertical_center, button_width, button_height, "Standard", font, 
                             image_name="image2-removebg-preview.png", image_subfolder="buttons/standard")
    
    # Gesture Mode button above Standard
    gesture_btn = Button(SCREEN_WIDTH//2 - button_width//2, vertical_center - button_spacing, button_width, button_height, "Gesture Mode", font, 
                       image_name="image-removebg-preview.png", image_subfolder="buttons/gesture")
    
    # The GeTrix Gauntlet button below Standard - normal size with star shape
    two_player_btn = Button(SCREEN_WIDTH//2 - button_width//2, vertical_center + button_spacing, button_width, button_height, "OverDrive", font, 
                          image_name="image1-removebg-preview.png", image_subfolder="buttons/duel")
    
    # Create enhanced title with multiple effects - properly centered
    title_text = "GeTrix"
    title_size = 130  # Larger size for more impact
    
    # Try to use Impact font for a bolder look
    try:
        title_font = pygame.font.SysFont('impact', title_size)
    except:
        title_font = pygame.font.Font(None, title_size)
    
    # Create shadow effect (darker blue)
    shadow_offset = 4
    shadow_color = (0, 100, 150)  # Dark blue shadow
    title_shadow = title_font.render(title_text, True, shadow_color)
    title_shadow_rect = title_shadow.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset, SCREEN_HEIGHT//5 + shadow_offset))
    
    # Create outline effect (multiple shadows in different directions)
    outline_color = (0, 150, 200)  # Slightly lighter blue for outline
    outline_offsets = [(2, 0), (-2, 0), (0, 2), (0, -2)]
    outline_rects = []
    for offset_x, offset_y in outline_offsets:
        outline = title_font.render(title_text, True, outline_color)
        outline_rect = outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, SCREEN_HEIGHT//5 + offset_y))
        outline_rects.append((outline, outline_rect))
    
    # Create glow effect
    glow_size = title_size + 6
    try:
        glow_font = pygame.font.SysFont('impact', glow_size)
    except:
        glow_font = pygame.font.Font(None, glow_size)
    
    glow_color = (100, 200, 255)  # Light blue glow
    glow = glow_font.render(title_text, True, glow_color)
    glow_rect = glow.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//5))
    
    # Main title (bright cyan)
    title_color = (0, 234, 255)  # Bright cyan
    title = title_font.render(title_text, True, title_color)
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//5))
    
    # Create subtitle - positioned lower below title
    subtitle = subtitle_font.render("Select Game Mode", True, UI_TEXT)
    subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//5 + 100))
    
    # Create right side decorative elements
    # 1. Create bouncing tetromino pieces that move around the screen
    tetromino_preview = []
    for i, shape in enumerate(SHAPES[:5]):  # Use first 5 shapes
        tetromino = {
            "shape": shape,
            "color": SHAPE_COLORS[i],
            "x": random.randint(50, SCREEN_WIDTH - 50),  # Random starting position
            "y": random.randint(50, SCREEN_HEIGHT - 50),  # Random starting position
            "dx": random.uniform(0.5, 2.0) * random.choice([-1, 1]),  # Random x velocity
            "dy": random.uniform(0.5, 2.0) * random.choice([-1, 1]),  # Random y velocity
            "rotation": 0,
            "rotation_speed": random.uniform(0.5, 2.0) * random.choice([-1, 1]),
            "scale": random.uniform(0.6, 0.9)  # Smaller scale
        }
        tetromino_preview.append(tetromino)
    
    # 2. Create info panel - centered for the controls screen
    info_panel = {
        "x": SCREEN_WIDTH // 2,  # Centered
        "y": SCREEN_HEIGHT // 2,  # Position maintained
        "width": 500,  # Even wider for text
        "height": 400,  # Even taller for text
        "alpha": 220  # More opaque for better contrast
    }
    
    # 3. Create info text with detailed gesture controls only - updated mode names
    info_texts = [
        "Game Modes:",
        "",
        "Standard - Classic Tetris",
        "HellF**K Mode - Fast-paced with special effects",
        "Gesture Mode - Hand controls",
        "",
        "Gesture Controls:",
        "• Index up: Move Left",
        "• Pinky up: Move Right",
        "• Middle up: Move Down",
        "• Thumb up: Rotate",
        "• All up: Hard Drop"
    ]
    
    # Create cyberpunk grid background
    grid_lines = []
    grid_spacing = 50
    for i in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
        grid_lines.append({"start": (i, 0), "end": (i, SCREEN_HEIGHT), "color": UI_GRID_LINE, "thickness": 1})
    for i in range(0, SCREEN_HEIGHT + grid_spacing, grid_spacing):
        grid_lines.append({"start": (0, i), "end": (SCREEN_WIDTH, i), "color": UI_GRID_LINE, "thickness": 1})
    
    # Create neon light effects
    neon_lights = []
    for _ in range(15):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        width = random.randint(100, 400)
        height = random.randint(5, 15) if random.random() < 0.7 else random.randint(5, 100)
        color = random.choice([RED, BLUE, CYAN, MAGENTA, YELLOW])
        pulse_speed = random.uniform(0.5, 2.0)
        alpha = random.randint(30, 80)
        neon_lights.append({
            "rect": pygame.Rect(x, y, width, height),
            "color": color,
            "pulse_speed": pulse_speed,
            "alpha": alpha,
            "pulse_offset": random.uniform(0, 2 * math.pi)
        })
    
    # Create flying particles
    particles = []
    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.uniform(1, 4)
        speed_x = random.uniform(-30, 30)
        speed_y = random.uniform(-30, 30)
        color = random.choice(PARTICLE_COLORS)
        life = random.uniform(1, 3)
        particles.append({
            "x": x, "y": y, 
            "size": size, 
            "speed_x": speed_x, "speed_y": speed_y, 
            "color": color, 
            "life": life,
            "max_life": life
        })
    
    # Create digital rain effect (Matrix-style)
    digital_rain = []
    for _ in range(30):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(-500, 0)
        speed = random.uniform(50, 200)
        length = random.randint(5, 20)
        chars = []
        for _ in range(length):
            chars.append({
                "char": random.choice("01ABCDEFabcdef+-*/!@#$%^&*()_=<>?"),
                "color": (0, random.randint(150, 255), random.randint(100, 200)),
                "alpha": random.randint(100, 255)
            })
        digital_rain.append({"x": x, "y": y, "speed": speed, "chars": chars})
    
    # Animation variables
    clock = pygame.time.Clock()
    animation_time = 0
    
    # Controls and store screen flags
    show_controls = False
    show_store = False
    
    # Create a Main Menu button for both controls and store pages
    menu_btn_width, menu_btn_height = 200, 50
    
    # Store variables
    store_data = load_store_data()
    selected_skin = store_data["active_skin"]
    store_message = ""
    message_timer = 0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Get delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            
            # Update button hover states
            single_player_btn.is_hovered = single_player_btn.rect.collidepoint(pygame.mouse.get_pos())
            two_player_btn.is_hovered = two_player_btn.rect.collidepoint(pygame.mouse.get_pos())
            gesture_btn.is_hovered = gesture_btn.rect.collidepoint(pygame.mouse.get_pos())
            controls_btn.is_hovered = controls_btn.rect.collidepoint(pygame.mouse.get_pos())
            store_btn.is_hovered = store_btn.rect.collidepoint(pygame.mouse.get_pos())
            settings_btn.is_hovered = settings_btn.rect.collidepoint(pygame.mouse.get_pos())
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Controls button always works
                if controls_btn.is_hovered:
                    show_controls = not show_controls
                    show_store = False  # Close store if open
                    continue
                
                # Settings button redirects to settings menu
                if settings_btn.is_hovered:
                    return "settings"
                
                # Check if Main Menu button is clicked in controls page
                if show_controls:
                    menu_btn_rect = pygame.Rect(SCREEN_WIDTH//2 - menu_btn_width//2, SCREEN_HEIGHT - 70, menu_btn_width, menu_btn_height)
                    if menu_btn_rect.collidepoint(event.pos):
                        show_controls = False  # Close the controls
                        continue
                    
                # Store button always works
                if store_btn.is_hovered:
                    show_store = not show_store
                    show_controls = False  # Close controls if open
                    continue
                
                # Check if Main Menu button is clicked in store
                if show_store:
                    menu_btn_width, menu_btn_height = 200, 50
                    menu_btn_rect = pygame.Rect(SCREEN_WIDTH//2 - menu_btn_width//2, SCREEN_HEIGHT - 70, menu_btn_width, menu_btn_height)
                    if menu_btn_rect.collidepoint(event.pos):
                        show_store = False  # Close the store
                        continue
                
                # Handle skin button clicks in store
                if show_store:
                    # Check basic skin buttons
                    basic_skins = [skin for skin_id, skin in store_data["available_skins"].items() 
                                  if skin["type"] == "basic" and skin_id != "default"]
                    
                    row_y = 220
                    col_width = 200
                    for i, skin in enumerate(basic_skins):
                        skin_id = next(k for k, v in store_data["available_skins"].items() if v == skin)
                        col = i % 3
                        row = i // 3
                        
                        x = SCREEN_WIDTH//2 - col_width + col * col_width
                        y = row_y + row * 80
                        
                        button_rect = pygame.Rect(x - 80, y - 20, 160, 60)
                        if button_rect.collidepoint(pygame.mouse.get_pos()):
                            if skin["owned"]:
                                # Set as active skin
                                set_active_skin(skin_id)
                                store_data = load_store_data()  # Refresh data
                                store_message = f"{skin['name']} selected!"
                                message_timer = 2.0  # Show for 2 seconds
                            else:
                                # Try to purchase
                                success, message = purchase_skin(skin_id)
                                if success:
                                    store_data = load_store_data()  # Refresh data
                                    store_message = f"Purchased {skin['name']}!"
                                    message_timer = 2.0
                                else:
                                    store_message = message
                                    message_timer = 2.0
                            break
                    
                    # Check special skin buttons
                    special_skins = [skin for skin_id, skin in store_data["available_skins"].items() 
                                    if skin["type"] == "special"]
                    
                    row_y = 440
                    for i, skin in enumerate(special_skins):
                        skin_id = next(k for k, v in store_data["available_skins"].items() if v == skin)
                        col = i % 3
                        row = i // 3
                        
                        x = SCREEN_WIDTH//2 - col_width + col * col_width
                        y = row_y + row * 80
                        
                        button_rect = pygame.Rect(x - 80, y - 20, 160, 60)
                        if button_rect.collidepoint(pygame.mouse.get_pos()):
                            if skin["owned"]:
                                # Set as active skin
                                set_active_skin(skin_id)
                                store_data = load_store_data()  # Refresh data
                                store_message = f"{skin['name']} selected!"
                                message_timer = 2.0  # Show for 2 seconds
                            else:
                                # Try to purchase
                                success, message = purchase_skin(skin_id)
                                if success:
                                    store_data = load_store_data()  # Refresh data
                                    store_message = f"Purchased {skin['name']}!"
                                    message_timer = 2.0
                                else:
                                    store_message = message
                                    message_timer = 2.0
                            break
                    
                    continue
                    
                # Game mode buttons only work when not in controls or store screen
                if not show_controls and not show_store:
                    if single_player_btn.is_hovered:
                        return "single"
                    if two_player_btn.is_hovered:
                        return "overdrive_menu"  # Go to OverDrive menu instead of directly to crazy mode
                    if gesture_btn.is_hovered:
                        return "gesture"
        
        # Update animations
        single_player_btn.update(dt)
        two_player_btn.update(dt)
        gesture_btn.update(dt)
        controls_btn.update(dt)
        store_btn.update(dt)
        
        # Update message timer
        if message_timer > 0:
            message_timer -= dt
            if message_timer <= 0:
                store_message = ""
        
        # Update animation time
        animation_time += dt
        
        # Draw background - cyberpunk gradient
        gradient_rect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            # Create a gradient from dark blue to black
            factor = y / SCREEN_HEIGHT
            r = int(0 + (20 * (1-factor)))
            g = int(0 + (10 * (1-factor)))
            b = int(20 + (40 * (1-factor)))
            pygame.draw.line(gradient_rect, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        screen.blit(gradient_rect, (0, 0))
        
        # Draw grid lines with pulsing effect
        for line in grid_lines:
            # Calculate pulsing alpha based on time
            pulse = (math.sin(animation_time * 0.5) + 1) / 2  # Value between 0 and 1
            alpha = int(20 + pulse * 20)  # Alpha between 20 and 40
            
            # Create a color with alpha
            color = list(line["color"])
            if len(color) == 3:  # RGB
                color.append(alpha)  # Add alpha
            else:  # RGBA
                color[3] = alpha  # Set alpha
            
            # Draw the line
            pygame.draw.line(screen, color, line["start"], line["end"], line["thickness"])
        
        # Draw neon light rectangles
        for light in neon_lights:
            # Calculate pulsing intensity
            pulse = (math.sin(animation_time * light["pulse_speed"] + light["pulse_offset"]) + 1) / 2
            alpha = int(light["alpha"] * (0.7 + 0.3 * pulse))
            
            # Create a surface with alpha
            light_surface = pygame.Surface((light["rect"].width, light["rect"].height), pygame.SRCALPHA)
            
            # Create color with alpha
            color = list(light["color"])
            if len(color) == 3:  # RGB
                color.append(alpha)  # Add alpha
            else:  # RGBA
                color[3] = alpha  # Set alpha
            
            # Draw the light
            pygame.draw.rect(light_surface, color, (0, 0, light["rect"].width, light["rect"].height), border_radius=3)
            
            # Add glow effect
            glow_surface = pygame.Surface((light["rect"].width + 10, light["rect"].height + 10), pygame.SRCALPHA)
            glow_color = list(light["color"])
            if len(glow_color) == 3:  # RGB
                glow_color.append(int(alpha * 0.5))  # Add alpha at half intensity
            else:  # RGBA
                glow_color[3] = int(alpha * 0.5)  # Set alpha at half intensity
            
            pygame.draw.rect(glow_surface, glow_color, (0, 0, light["rect"].width + 10, light["rect"].height + 10), border_radius=5)
            screen.blit(glow_surface, (light["rect"].x - 5, light["rect"].y - 5))
            screen.blit(light_surface, light["rect"])
        
        # Update and draw particles
        particles_to_remove = []
        for i, particle in enumerate(particles):
            # Update position
            particle["x"] += particle["speed_x"] * dt
            particle["y"] += particle["speed_y"] * dt
            
            # Update life
            particle["life"] -= dt
            if particle["life"] <= 0:
                particles_to_remove.append(i)
                continue
            
            # Wrap around screen
            if particle["x"] < 0:
                particle["x"] = SCREEN_WIDTH
            elif particle["x"] > SCREEN_WIDTH:
                particle["x"] = 0
            if particle["y"] < 0:
                particle["y"] = SCREEN_HEIGHT
            elif particle["y"] > SCREEN_HEIGHT:
                particle["y"] = 0
            
            # Calculate alpha based on life
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            
            # Create color with alpha
            color = list(particle["color"])
            if len(color) == 3:  # RGB
                color.append(alpha)  # Add alpha
            else:  # RGBA
                color[3] = alpha  # Set alpha
            
            # Draw the particle
            pygame.draw.circle(screen, color, (int(particle["x"]), int(particle["y"])), particle["size"] * (particle["life"] / particle["max_life"]))
        
        # Remove dead particles
        for i in sorted(particles_to_remove, reverse=True):
            if i < len(particles):
                particles.pop(i)
        
        # Update and draw digital rain
        rain_to_remove = []
        for i, rain in enumerate(digital_rain):
            # Update position
            rain["y"] += rain["speed"] * dt
            
            # Remove if off screen
            if rain["y"] > SCREEN_HEIGHT + len(rain["chars"]) * 20:
                rain_to_remove.append(i)
                continue
            
            # Draw characters
            for j, char_data in enumerate(rain["chars"]):
                char_y = rain["y"] + j * 20
                
                # Only draw if on screen
                if 0 <= char_y <= SCREEN_HEIGHT:
                    # Create font for character
                    char_font = pygame.font.Font(None, 24)
                    
                    # Calculate alpha (fade out at the tail)
                    fade_factor = 1.0 - (j / len(rain["chars"]))
                    alpha = int(char_data["alpha"] * fade_factor)
                    
                    # Create color with alpha
                    color = list(char_data["color"])
                    if len(color) == 3:  # RGB
                        color.append(alpha)  # Add alpha
                    else:  # RGBA
                        color[3] = alpha  # Set alpha
                    
                    # Render and draw character
                    char_surface = char_font.render(char_data["char"], True, color)
                    screen.blit(char_surface, (rain["x"], char_y))
                    
                    # Randomly change character (10% chance)
                    if random.random() < 0.1:
                        char_data["char"] = random.choice("01ABCDEFabcdef+-*/!@#$%^&*()_=<>?")
        
        # Remove rain that's off screen
        for i in sorted(rain_to_remove, reverse=True):
            if i < len(digital_rain):
                digital_rain.pop(i)
                
        # Add new rain occasionally
        if random.random() < 0.05:  # 5% chance per frame
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(-500, 0)
            speed = random.uniform(50, 200)
            length = random.randint(5, 20)
            chars = []
            for _ in range(length):
                chars.append({
                    "char": random.choice("01ABCDEFabcdef+-*/!@#$%^&*()_=<>?"),
                    "color": (0, random.randint(150, 255), random.randint(100, 200)),
                    "alpha": random.randint(100, 255)
                })
            digital_rain.append({"x": x, "y": y, "speed": speed, "chars": chars})
            
        if show_controls or show_store:
            # Draw semi-transparent overlay for controls/store screen
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((10, 10, 20))
            screen.blit(overlay, (0, 0))
            
            if show_controls:
                # Draw controls screen title
                controls_title = title_font.render("CONTROLS", True, UI_ACCENT)
                controls_title_rect = controls_title.get_rect(center=(SCREEN_WIDTH//2, 100))
                screen.blit(controls_title, controls_title_rect)
                
                # Draw back instruction
                back_text = subtitle_font.render("Click Controls/Gestures again to return", True, WHITE)
                back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
                screen.blit(back_text, back_rect)
            
            # Draw controls as a separate page like the store
            if show_controls:
                # Fill the screen with a dark background
                screen.fill((0, 10, 30))  # Dark blue background
                
                # Draw title
                controls_title = title_font.render("Controls", True, UI_ACCENT)
                controls_title_rect = controls_title.get_rect(center=(SCREEN_WIDTH//2, 80))
                screen.blit(controls_title, controls_title_rect)
                
                # Draw Main Menu button
                menu_btn_rect = pygame.Rect(SCREEN_WIDTH//2 - menu_btn_width//2, SCREEN_HEIGHT - 70, menu_btn_width, menu_btn_height)
                menu_btn_color = (80, 80, 150)  # Default color
                
                # Check if mouse is hovering over the button
                if menu_btn_rect.collidepoint(pygame.mouse.get_pos()):
                    menu_btn_color = (120, 120, 200)  # Highlight color
                    if pygame.mouse.get_pressed()[0]:  # If mouse is clicked
                        show_controls = False  # Close the controls
                
                # Draw the button
                pygame.draw.rect(screen, menu_btn_color, menu_btn_rect, border_radius=5)
                menu_btn_text = subtitle_font.render("Main Menu", True, WHITE)
                menu_btn_text_rect = menu_btn_text.get_rect(center=menu_btn_rect.center)
                screen.blit(menu_btn_text, menu_btn_text_rect)
                
                # Create comprehensive controls text
                controls_text = [
                    "STANDARD MODE CONTROLS:",
                    "",
                    "Left Window:",
                    "• A/D: Move Left/Right",
                    "• W: Rotate",
                    "• S: Move Down",
                    "• Q: Hard Drop",
                    "",
                    "GESTURE MODE CONTROLS:",
                    "",
                    "• Make a loose fist, and extend fingers to move pieces",
                    "",
                    "• Index finger: Move Left",
                    "• Pinky finger: Move Right",
                    "• Middle finger: Move Down",
                    "• Thumb clearly to the side: Rotate",
                    "• Open hand (most fingers up): Hard Drop",
                    "",
                    "Remember to face the palm of your RIGHT hand towards the camera",
                    "",
                    "GENERAL CONTROLS:",
                    "• ESC: Return to Menu",
                    "• R: Reset Game"
                ]
                
                # Create smaller font for instructions
                smaller_info_font = pygame.font.Font(None, 18)  # Smaller font for instructions
                
                # Draw controls text
                for i, text in enumerate(controls_text):
                    if "STANDARD MODE" in text or "GESTURE MODE" in text or "GENERAL CONTROLS" in text:
                        text_surface = subtitle_font.render(text, True, UI_ACCENT)
                        y_offset = 30  # More space before headers
                    elif "Left Window" in text or "Right Window" in text or "Remember" in text:
                        text_surface = info_font.render(text, True, UI_HIGHLIGHT)
                        y_offset = 25  # More space before subheaders
                    else:
                        text_surface = smaller_info_font.render(text, True, WHITE)
                        y_offset = 18  # Reduced spacing for smaller font
                        
                    # Position text centered on screen instead of in a panel
                    text_rect = text_surface.get_rect()
                    text_rect.centerx = SCREEN_WIDTH // 2  # Center horizontally
                    text_rect.y = 150 + sum([30 if "MODE" in controls_text[j] or "GENERAL" in controls_text[j] else 
                                             25 if "Window" in controls_text[j] or "Remember" in controls_text[j] else 18 
                                             for j in range(i)])
                    screen.blit(text_surface, text_rect)
        if show_store:
            # Draw store screen title
            store_title = title_font.render("STORE", True, (255, 215, 0))  # Gold color
            store_title_rect = store_title.get_rect(center=(SCREEN_WIDTH//2, 80))
            screen.blit(store_title, store_title_rect)
            
            # Draw Main Menu button
            menu_btn_width, menu_btn_height = 200, 50
            menu_btn_rect = pygame.Rect(SCREEN_WIDTH//2 - menu_btn_width//2, SCREEN_HEIGHT - 70, menu_btn_width, menu_btn_height)
            menu_btn_color = (80, 80, 150)  # Default color
            
            # Check if mouse is hovering over the button
            if menu_btn_rect.collidepoint(pygame.mouse.get_pos()):
                menu_btn_color = (120, 120, 200)  # Highlight color
                if pygame.mouse.get_pressed()[0]:  # If mouse is clicked
                    show_store = False  # Close the store
            
            # Draw the button
            pygame.draw.rect(screen, menu_btn_color, menu_btn_rect, border_radius=5)
            menu_btn_text = subtitle_font.render("Main Menu", True, WHITE)
            menu_btn_text_rect = menu_btn_text.get_rect(center=menu_btn_rect.center)
            screen.blit(menu_btn_text, menu_btn_text_rect)
            
            # Draw LineChips count
            chips_text = subtitle_font.render(f"LineChips: {get_line_chips()}", True, (255, 215, 0))
            chips_rect = chips_text.get_rect(center=(SCREEN_WIDTH//2, 130))
            screen.blit(chips_text, chips_rect)
            
            # Draw store message if any
            if store_message:
                msg_text = subtitle_font.render(store_message, True, (255, 255, 255))
                msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
                screen.blit(msg_text, msg_rect)
            
            # Draw skin categories
            basic_title = subtitle_font.render("Basic Skins (15 LineChips)", True, (220, 220, 220))
            basic_rect = basic_title.get_rect(center=(SCREEN_WIDTH//2, 180))
            screen.blit(basic_title, basic_rect)
            
            special_title = subtitle_font.render("Special Skins (30 LineChips)", True, (220, 220, 220))
            special_rect = special_title.get_rect(center=(SCREEN_WIDTH//2, 400))
            screen.blit(special_title, special_rect)
            
            # Draw basic skins
            basic_skins = [skin for skin_id, skin in store_data["available_skins"].items() 
                          if skin["type"] == "basic" and skin_id != "default"]
            
            # Create skin buttons for basic skins
            row_y = 220
            col_width = 200
            for i, skin in enumerate(basic_skins):
                skin_id = next(k for k, v in store_data["available_skins"].items() if v == skin)
                col = i % 3
                row = i // 3
                
                # Draw skin preview
                x = SCREEN_WIDTH//2 - col_width + col * col_width
                y = row_y + row * 80
                
                # Draw button background
                button_color = (100, 100, 100)
                if skin["owned"]:
                    button_color = (50, 150, 50)  # Green if owned
                if store_data["active_skin"] == skin_id:
                    button_color = (50, 50, 200)  # Blue if active
                
                pygame.draw.rect(screen, button_color, 
                                pygame.Rect(x - 80, y - 20, 160, 60), border_radius=0)
                
                # Draw skin name
                skin_text = info_font.render(skin["name"], True, WHITE)
                skin_rect = skin_text.get_rect(center=(x, y))
                screen.blit(skin_text, skin_rect)
                
                # Draw action text
                action_text = ""
                if skin["owned"]:
                    if store_data["active_skin"] == skin_id:
                        action_text = "Active"
                    else:
                        action_text = "Select"
                else:
                    action_text = f"Buy: {skin['price']}"
                
                action_surface = info_font.render(action_text, True, WHITE)
                action_rect = action_surface.get_rect(center=(x, y + 20))
                screen.blit(action_surface, action_rect)
            
            # Draw special skins
            special_skins = [skin for skin_id, skin in store_data["available_skins"].items() 
                            if skin["type"] == "special"]
            
            # Create skin buttons for special skins
            row_y = 440
            for i, skin in enumerate(special_skins):
                skin_id = next(k for k, v in store_data["available_skins"].items() if v == skin)
                col = i % 3
                row = i // 3
                
                # Draw skin preview
                x = SCREEN_WIDTH//2 - col_width + col * col_width
                y = row_y + row * 80
                
                # Draw button background
                button_color = (100, 100, 100)
                if skin["owned"]:
                    button_color = (50, 150, 50)  # Green if owned
                if store_data["active_skin"] == skin_id:
                    button_color = (50, 50, 200)  # Blue if active
                
                pygame.draw.rect(screen, button_color, 
                                pygame.Rect(x - 80, y - 20, 160, 60), border_radius=0)
                
                # Draw skin name
                skin_text = info_font.render(skin["name"], True, WHITE)
                skin_rect = skin_text.get_rect(center=(x, y))
                screen.blit(skin_text, skin_rect)
                
                # Draw action text
                action_text = ""
                if skin["owned"]:
                    if store_data["active_skin"] == skin_id:
                        action_text = "Active"
                    else:
                        action_text = "Select"
                else:
                    action_text = f"Buy: {skin['price']}"
                
                action_surface = info_font.render(action_text, True, WHITE)
                action_rect = action_surface.get_rect(center=(x, y + 20))
                screen.blit(action_surface, action_rect)
        elif not show_controls and not show_store:
            # Draw regular menu UI with enhanced title effects
            
            # Draw glow effect first (behind everything)
            screen.blit(glow, glow_rect)
            
            # Draw shadow effect
            screen.blit(title_shadow, title_shadow_rect)
            
            # Draw outline effects
            for outline, outline_rect in outline_rects:
                screen.blit(outline, outline_rect)
                
            # Draw main title on top
            screen.blit(title, title_rect)
            
            # Draw subtitle
            screen.blit(subtitle, subtitle_rect)
            
            # Draw game mode buttons
            single_player_btn.draw(screen)
            two_player_btn.draw(screen)
            gesture_btn.draw(screen)
            controls_btn.draw(screen)
            store_btn.draw(screen)
            settings_btn.draw(screen)
            
            # Draw right side decorative elements - only in main menu
            # Draw animated bouncing tetromino pieces in the background
            animation_time += dt
            for tetromino in tetromino_preview:
                # Update position with bouncing
                tetromino["x"] += tetromino["dx"] * dt * 60
                tetromino["y"] += tetromino["dy"] * dt * 60
                
                # Bounce off walls
                shape_width = len(tetromino["shape"][0]) * 20 * tetromino["scale"]
                shape_height = len(tetromino["shape"]) * 20 * tetromino["scale"]
                
                if tetromino["x"] < 0 or tetromino["x"] + shape_width > SCREEN_WIDTH:
                    tetromino["dx"] *= -1
                    # Ensure it stays within bounds
                    if tetromino["x"] < 0:
                        tetromino["x"] = 0
                    if tetromino["x"] + shape_width > SCREEN_WIDTH:
                        tetromino["x"] = SCREEN_WIDTH - shape_width
                
                if tetromino["y"] < 0 or tetromino["y"] + shape_height > SCREEN_HEIGHT:
                    tetromino["dy"] *= -1
                    # Ensure it stays within bounds
                    if tetromino["y"] < 0:
                        tetromino["y"] = 0
                    if tetromino["y"] + shape_height > SCREEN_HEIGHT:
                        tetromino["y"] = SCREEN_HEIGHT - shape_height
                
                # Update rotation
                tetromino["rotation"] += tetromino["rotation_speed"] * dt
                
                # Draw each block in the tetromino
                block_size = int(20 * tetromino["scale"])
                for y, row in enumerate(tetromino["shape"]):
                    for x, cell in enumerate(row):
                        if cell:
                            # Calculate position with rotation
                            angle = tetromino["rotation"]
                            center_x = tetromino["x"] + len(row) * block_size / 2
                            center_y = tetromino["y"] + len(tetromino["shape"]) * block_size / 2
                            offset_x = x * block_size - len(row) * block_size / 2
                            offset_y = y * block_size - len(tetromino["shape"]) * block_size / 2
                            
                            # Rotate around center
                            rotated_x = offset_x * math.cos(angle) - offset_y * math.sin(angle)
                            rotated_y = offset_x * math.sin(angle) + offset_y * math.cos(angle)
                            
                            # Final position
                            pos_x = int(center_x + rotated_x)
                            pos_y = int(center_y + rotated_y)
                            
                            # Draw block with 3D effect but with reduced alpha for background effect
                            block_color = list(tetromino["color"])
                            block_surface = pygame.Surface((block_size, block_size))
                            block_surface.fill(block_color)
                            block_surface.set_alpha(80)  # More transparent
                            screen.blit(block_surface, (pos_x, pos_y))
                            pygame.draw.rect(screen, tetromino["color"], 
                                            pygame.Rect(pos_x, pos_y, block_size, block_size), 
                                            1, border_radius=2)  # Just the outline
        
        # Always draw the Controls/Gestures button on top
        controls_btn.draw(screen)
        
        # Draw version info
        version_text = pygame.font.Font(None, 20).render("v1.0.0", True, GRAY)
        screen.blit(version_text, (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()

def run_single_player(screen, font, music_manager=None):
    # Start standard game music if music manager is provided
    if music_manager:
        music_manager.play_music_for_mode('standard')
    controls = {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "down": pygame.K_s,
        "rotate": pygame.K_w,
        "hard_drop": pygame.K_SPACE
    }
    
    # Move the game window down by adding a y_offset of 50 pixels
    y_offset = 50
    game = TetrisGame(SCREEN_WIDTH // 2 - (GRID_WIDTH * GRID_SIZE) // 2, controls, y_offset=y_offset)
    
    # Add music manager to the game instance
    game.music_manager = music_manager
    
    # Add more particles for visual effect
    particles = []
    for _ in range(100):  # Doubled the number of particles
        particles.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'size': random.uniform(2, 6),  # Larger particles
            'speed': random.uniform(1.0, 3.0),  # Faster movement
            'angle': random.uniform(0, 2 * math.pi),
            'color': (random.randint(100, 255), random.randint(100, 255), random.randint(150, 255)),  # Brighter colors
            'life': 1.0
        })
    
    # Background effect variables
    background_offset = 0
    background_speed = 1.2  # Faster background movement
    
    while True:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            # Check for direct menu button clicks when game is over
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                if game.game_over and game.menu_button_rect and game.menu_button_rect.collidepoint(mouse_pos):
                    print("Single game menu button clicked!")
                    return "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                elif event.key == pygame.K_r:
                    game.reset()
                else:
                    result = game.handle_input(event)
                    if result == "menu":
                        return "menu"
        
        game.update()
        
        # Draw illusory background
        screen.fill(BLACK)
        
        # Draw animated background pattern - brighter and more hectic
        background_offset += background_speed
        
        # Add flashing background pulses
        pulse_intensity = int(40 + 40 * math.sin(current_time * 3))
        pulse_color = (pulse_intensity, pulse_intensity, pulse_intensity + 20)
        screen.fill(pulse_color)  # Add a subtle pulsing base color
        
        # Draw grid with more vibrant colors
        for y in range(0, SCREEN_HEIGHT, 15):  # Closer spacing
            for x in range(0, SCREEN_WIDTH, 15):
                wave_effect = 15 * math.sin((x + y) / 40 + background_offset / 8)  # More pronounced wave
                r = int(120 + 120 * math.sin(current_time * 1.5 + (x) / 80))
                g = int(120 + 120 * math.sin(current_time * 2.0 + (y) / 80 + 2))
                b = int(150 + 100 * math.sin(current_time * 2.5 + (x + y) / 100 + 4))
                color = (r, g, b)  # Rainbow effect
                
                # Larger, pulsing circles
                size = 4 + 3 * math.sin(current_time * 3 + (x + y) / 40)
                
                # More movement
                x_offset = int(8 * math.sin(current_time * 2 + y / 15))
                y_offset = int(8 * math.cos(current_time * 2.5 + x / 15))
                
                pygame.draw.circle(screen, color, 
                                  (x + x_offset, y + y_offset), 
                                  int(size))
        
        # Update and draw particles
        particles_to_remove = []
        for i, particle in enumerate(particles):
            # Move particle
            particle['x'] += particle['speed'] * math.cos(particle['angle'])
            particle['y'] += particle['speed'] * math.sin(particle['angle'])
            particle['life'] -= 0.005
            
            # Remove dead particles or those that left the screen
            if particle['life'] <= 0 or \
               particle['x'] < -20 or particle['x'] > SCREEN_WIDTH + 20 or \
               particle['y'] < -20 or particle['y'] > SCREEN_HEIGHT + 20:
                particles_to_remove.append(i)
                continue
            
            # Draw particle
            alpha = int(255 * particle['life'])
            color = particle['color']
            s = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (particle['size'], particle['size']), particle['size'])
            screen.blit(s, (int(particle['x'] - particle['size']), int(particle['y'] - particle['size'])))
        
        # Remove dead particles
        for i in sorted(particles_to_remove, reverse=True):
            particles.pop(i)
        
        # Add new particles more frequently with brighter colors
        if random.random() < 0.25:  # Increased probability
            # Randomly choose particle type
            particle_type = random.randint(0, 2)
            
            if particle_type == 0:  # Standard particle
                particles.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(0, SCREEN_HEIGHT),
                    'size': random.uniform(2, 6),
                    'speed': random.uniform(1.0, 3.5),
                    'angle': random.uniform(0, 2 * math.pi),
                    'color': (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255)),
                    'life': 1.0
                })
            elif particle_type == 1:  # Streak particle
                particles.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(0, SCREEN_HEIGHT),
                    'size': random.uniform(1, 3),
                    'speed': random.uniform(5.0, 8.0),  # Very fast
                    'angle': random.uniform(0, 2 * math.pi),
                    'color': (255, random.randint(150, 255), random.randint(100, 200)),  # Reddish
                    'life': 0.7
                })
            else:  # Burst particle
                base_x = random.randint(0, SCREEN_WIDTH)
                base_y = random.randint(0, SCREEN_HEIGHT)
                base_color = (random.randint(200, 255), random.randint(200, 255), random.randint(100, 255))
                
                # Create a burst of 5-10 particles from the same point
                for _ in range(random.randint(5, 10)):
                    particles.append({
                        'x': base_x,
                        'y': base_y,
                        'size': random.uniform(1, 4),
                        'speed': random.uniform(2.0, 5.0),
                        'angle': random.uniform(0, 2 * math.pi),
                        'color': base_color,
                        'life': random.uniform(0.5, 0.9)
                    })
        
        # Draw the game on top of the background
        game.draw(screen, font)
        
        instructions = [
            "Controls:",
            "A/D: Move left/right",
            "S: Move down",
            "W: Rotate",
            "Space: Hard drop",
            "",
            "R: Reset game",
            "ESC: Menu"
        ]
        
        for i, line in enumerate(instructions):
            text = pygame.font.Font(None, 24).render(line, True, WHITE)
            screen.blit(text, (20, GRID_HEIGHT * GRID_SIZE + 10 + i * 20))
        
        pygame.display.flip()

def run_two_player(screen, font, crazy_mode=False, music_manager=None):
    # Start appropriate music based on mode
    if music_manager:
        if crazy_mode:
            music_manager.play_music_for_mode('crazy')
        else:
            music_manager.play_music_for_mode('standard')
    # Set up the title based on mode
    title = "HELLF**K MODE" if crazy_mode else "STANDARD DUEL"
    
    # Set up special effects for crazy mode
    last_control_swap_time = 0
    controls_swapped = False
    mirror_controls = False
    invert_controls = False
    last_effect_change_time = time.time()
    left_controls = {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "down": pygame.K_s,
        "rotate": pygame.K_w,
        "hard_drop": pygame.K_q
    }
    
    right_controls = {
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "down": pygame.K_DOWN,
        "rotate": pygame.K_UP,
        "hard_drop": pygame.K_SPACE
    }
    
    # In crazy mode, pieces fall faster and the game is more challenging
    speed_multiplier = 2.0 if crazy_mode else 1.0
    
    # Create the game instances
    left_game = TetrisGame(50, left_controls)
    right_game = TetrisGame(450, right_controls)
    
    # Add music manager to both game instances
    left_game.music_manager = music_manager
    right_game.music_manager = music_manager
    
    # Adjust game parameters for crazy mode
    if crazy_mode:
        # Faster falling speed
        left_game.fall_speed *= speed_multiplier
        right_game.fall_speed *= speed_multiplier
        
        # Activate ALL visual effects for maximum confusion
        left_game.illusion_active = True
        right_game.illusion_active = True
        
        # Increase grid pulse speed dramatically
        left_game.grid_pulse_speed = 5.0
        right_game.grid_pulse_speed = 5.0
        
        # Increase shake intensity for line clears
        left_game.shake_intensity = 10
        right_game.shake_intensity = 10
        
        # Set rotation for Brainfck mode - pieces will appear rotated
        left_game.target_rotation = 15
        right_game.target_rotation = -15
        
        # Make the grid lines move faster
        left_game.grid_line_speed = 3.0
        right_game.grid_line_speed = 3.0
        
        # Add more particles
        for _ in range(50):
            left_game.particles.append({
                'x': random.randint(0, GRID_WIDTH * GRID_SIZE),
                'y': random.randint(0, GRID_HEIGHT * GRID_SIZE),
                'size': random.uniform(1, 3),
                'speed': random.uniform(1, 3),
                'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                'direction': random.uniform(0, 2 * math.pi),
                'life': 1.0  # Add life property
            })
            right_game.particles.append({
                'x': random.randint(0, GRID_WIDTH * GRID_SIZE),
                'y': random.randint(0, GRID_HEIGHT * GRID_SIZE),
                'size': random.uniform(1, 3),
                'speed': random.uniform(1, 3),
                'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                'direction': random.uniform(0, 2 * math.pi),
                'life': 1.0  # Add life property
            })
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            # Check for direct menu button clicks when games are over
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                # Check if either game has a menu button that was clicked
                if left_game.game_over or right_game.game_over:
                    mouse_pos = pygame.mouse.get_pos()
                    if left_game.game_over and left_game.menu_button_rect and left_game.menu_button_rect.collidepoint(mouse_pos):
                        print("Left game menu button clicked!")
                        return "menu"
                    if right_game.game_over and right_game.menu_button_rect and right_game.menu_button_rect.collidepoint(mouse_pos):
                        print("Right game menu button clicked!")
                        return "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                elif event.key == pygame.K_r:
                    left_game.reset()
                    right_game.reset()
                else:
                    # In crazy mode, randomly mess with controls
                    if crazy_mode:
                        current_time = time.time()
                        
                        # Every 10 seconds, change the control effects
                        if current_time - last_effect_change_time > 10:
                            last_effect_change_time = current_time
                            effect_choice = random.randint(0, 3)
                            
                            # Reset all effects
                            controls_swapped = False
                            mirror_controls = False
                            invert_controls = False
                            
                            # Apply a random effect
                            if effect_choice == 1:
                                controls_swapped = True
                                flash_message = "CONTROLS SWAPPED!"
                            elif effect_choice == 2:
                                mirror_controls = True
                                flash_message = "MIRROR CONTROLS!"
                            elif effect_choice == 3:
                                invert_controls = True
                                flash_message = "INVERTED CONTROLS!"
                        
                        # Apply the control modifications
                        if controls_swapped:
                            # Swap left and right game controls
                            right_result = right_game.handle_input(event)
                            left_result = left_game.handle_input(event)
                            
                            # If either game signals to return to menu
                            if right_result == "menu" or left_result == "menu":
                                return "menu"
                        elif mirror_controls:
                            # Create mirrored event for left/right keys
                            mirrored_event = pygame.event.Event(event.type, {"key": event.key})
                            
                            # Mirror left/right keys
                            if event.key == pygame.K_LEFT:
                                mirrored_event.key = pygame.K_RIGHT
                            elif event.key == pygame.K_RIGHT:
                                mirrored_event.key = pygame.K_LEFT
                            elif event.key == pygame.K_a:
                                mirrored_event.key = pygame.K_d
                            elif event.key == pygame.K_d:
                                mirrored_event.key = pygame.K_a
                            
                            left_result = left_game.handle_input(mirrored_event)
                            right_result = right_game.handle_input(mirrored_event)
                            
                            # If either game signals to return to menu
                            if left_result == "menu" or right_result == "menu":
                                return "menu"
                        elif invert_controls:
                            # Invert up/down keys
                            inverted_event = pygame.event.Event(event.type, {"key": event.key})
                            
                            if event.key == pygame.K_UP:
                                inverted_event.key = pygame.K_DOWN
                            elif event.key == pygame.K_DOWN:
                                inverted_event.key = pygame.K_UP
                            elif event.key == pygame.K_w:
                                inverted_event.key = pygame.K_s
                            elif event.key == pygame.K_s:
                                inverted_event.key = pygame.K_w
                            
                            left_result = left_game.handle_input(inverted_event)
                            right_result = right_game.handle_input(inverted_event)
                            
                            # If either game signals to return to menu
                            if left_result == "menu" or right_result == "menu":
                                return "menu"
                        else:
                            # Normal controls
                            left_result = left_game.handle_input(event)
                            right_result = right_game.handle_input(event)
                            
                            # If either game signals to return to menu
                            if left_result == "menu" or right_result == "menu":
                                return "menu"
                    else:
                        # Normal mode - standard controls
                        # Check for menu button clicks if game is over
                        left_result = left_game.handle_input(event)
                        right_result = right_game.handle_input(event)
                        
                        # If either game signals to return to menu
                        if left_result == "menu" or right_result == "menu":
                            return "menu"
        
        left_game.update()
        right_game.update()
        
        # Create a wild background for crazy mode
        if crazy_mode:
            # Draw a trippy gradient background
            for y in range(0, SCREEN_HEIGHT, 4):
                color_shift = int(128 + 127 * math.sin(time.time() * 2 + y * 0.01))
                color = (color_shift, int(color_shift * 0.5), 255 - color_shift)
                pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y), 4)
                
            # Draw title with pulsing effect
            title_size = int(40 + 10 * math.sin(time.time() * 5))
            title_font = pygame.font.Font(None, title_size)
            title_color = (255, int(128 + 127 * math.sin(time.time() * 3)), int(128 + 127 * math.cos(time.time() * 3)))
            title_surface = title_font.render("CRAZY MODE", True, title_color)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 30))
            screen.blit(title_surface, title_rect)
            
            # Draw a wavy dividing line
            for y in range(0, SCREEN_HEIGHT, 2):
                x_offset = int(10 * math.sin(time.time() * 3 + y * 0.05))
                pygame.draw.line(screen, (200, 200, 200), 
                                (SCREEN_WIDTH // 2 + x_offset, y), 
                                (SCREEN_WIDTH // 2 + x_offset, y + 2), 2)
        else:
            # Regular background for standard mode
            screen.fill(BLACK)
            pygame.draw.line(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2)
            
        # Randomly swap the games' positions in crazy mode (5% chance per frame)
        if crazy_mode and random.random() < 0.05:
            # Save original offsets
            temp_x = left_game.x_offset
            left_game.x_offset = right_game.x_offset
            right_game.x_offset = temp_x
            
            # Draw games with swapped positions
            left_game.draw(screen, font)
            right_game.draw(screen, font)
            
            # Restore original offsets
            left_game.x_offset = temp_x
            right_game.x_offset = 450
        else:
            # Normal drawing
            left_game.draw(screen, font)
            right_game.draw(screen, font)
        
        instructions = [
            "Left: WASD + Q",
            "Right: Arrows + Space",
            "R: Reset both",
            "ESC: Menu"
        ]
        
        for i, line in enumerate(instructions):
            text = pygame.font.Font(None, 24).render(line, True, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - 80, GRID_HEIGHT * GRID_SIZE + 10 + i * 20))
        
        pygame.display.flip()

def run_overdrive_menu(screen, font, music_manager=None):
    """Menu to select control type for OverDrive mode"""
    # Start menu music if music manager is provided (keep same music)
    if music_manager:
        music_manager.play_music_for_mode('menu')
    
    # Create title font
    title_font = pygame.font.Font(None, 80)
    subtitle_font = pygame.font.Font(None, 40)
    
    # Create cyberpunk-style title and subtitle
    title_text = "OverDrive Mode"
    subtitle_text = "Select Control Method"
    
    # Render title with shadow effect
    shadow_offset = 3
    title_shadow = title_font.render(title_text, True, (180, 20, 20))  # Dark red shadow
    title_shadow_rect = title_shadow.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset, SCREEN_HEIGHT//4 + shadow_offset))
    
    title = title_font.render(title_text, True, (255, 80, 80))  # Bright red text
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    
    # Render subtitle
    subtitle = subtitle_font.render(subtitle_text, True, (220, 220, 220))
    subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 70))
    
    # Create large buttons for control types
    button_width, button_height = 320, 100
    vertical_center = SCREEN_HEIGHT // 2 + 50
    button_spacing = 40
    
    # Keyboard control button
    keyboard_btn = Button(
        SCREEN_WIDTH//2 - button_width - button_spacing//2, 
        vertical_center, 
        button_width, 
        button_height, 
        "Keyboard Controls", 
        subtitle_font
    )
    keyboard_btn.normal_color = (180, 50, 50)  # Red theme for overdrive
    keyboard_btn.hover_color = (255, 100, 100)
    keyboard_btn.shape_type = "controller"  # Controller shape
    
    # Gesture control button
    gesture_btn = Button(
        SCREEN_WIDTH//2 + button_spacing//2, 
        vertical_center, 
        button_width, 
        button_height, 
        "Gesture Controls", 
        subtitle_font,
        image_name="image-removebg-preview.png", 
        image_subfolder="buttons/gesture"
    )
    gesture_btn.normal_color = (180, 50, 50)  # Red theme for overdrive
    gesture_btn.hover_color = (255, 100, 100)
    
    # Back button
    back_btn = Button(50, 50, 150, 50, "Back", subtitle_font)
    back_btn.normal_color = (80, 80, 80)
    
    # Create digital rain effect (Matrix-style)
    digital_rain = []
    for _ in range(30):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(-500, 0)
        speed = random.uniform(50, 200)
        length = random.randint(5, 20)
        chars = []
        for _ in range(length):
            chars.append({
                "char": random.choice("01ABCDEFabcdef+-*/!@#$%^&*()_=<>?"),
                "color": (random.randint(150, 255), random.randint(20, 80), random.randint(20, 80)),  # Red theme
                "alpha": random.randint(100, 255)
            })
        digital_rain.append({"x": x, "y": y, "speed": speed, "chars": chars})
    
    # Create flying particles with red theme
    particles = []
    for _ in range(80):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.uniform(1, 4)
        speed_x = random.uniform(-30, 30)
        speed_y = random.uniform(-30, 30)
        # Red-themed particles
        color = (random.randint(200, 255), random.randint(0, 100), random.randint(0, 50))
        life = random.uniform(1, 3)
        particles.append({
            "x": x, "y": y, 
            "size": size, 
            "speed_x": speed_x, "speed_y": speed_y, 
            "color": color, 
            "life": life,
            "max_life": life
        })
    
    # Animation variables
    clock = pygame.time.Clock()
    animation_time = 0
    
    while True:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        animation_time += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
            
            # Handle button clicks
            if keyboard_btn.handle_event(event):
                return "crazy"  # Start crazy mode with keyboard controls
            elif gesture_btn.handle_event(event):
                return "crazy_gestures"  # Start crazy mode with gesture controls
            elif back_btn.handle_event(event):
                return "menu"  # Go back to main menu
        
        # Update digital rain
        for rain in digital_rain:
            rain["y"] += rain["speed"] * dt
            if rain["y"] > SCREEN_HEIGHT:
                rain["y"] = random.randint(-500, -100)
                rain["x"] = random.randint(0, SCREEN_WIDTH)
        
        # Update particles
        for p in particles[:]:
            p["x"] += p["speed_x"] * dt
            p["y"] += p["speed_y"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                particles.remove(p)
                # Add a new particle to replace it
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                size = random.uniform(1, 4)
                speed_x = random.uniform(-30, 30)
                speed_y = random.uniform(-30, 30)
                color = (random.randint(200, 255), random.randint(0, 100), random.randint(0, 50))
                life = random.uniform(1, 3)
                particles.append({
                    "x": x, "y": y, 
                    "size": size, 
                    "speed_x": speed_x, "speed_y": speed_y, 
                    "color": color, 
                    "life": life,
                    "max_life": life
                })
        
        # Update buttons
        keyboard_btn.update(dt)
        gesture_btn.update(dt)
        back_btn.update(dt)
        
        # Draw
        screen.fill((30, 0, 0))  # Dark red background
        
        # Draw digital rain
        for rain in digital_rain:
            for i, char_data in enumerate(rain["chars"]):
                char_y = rain["y"] + i * 20
                if 0 <= char_y < SCREEN_HEIGHT:
                    char_surface = subtitle_font.render(char_data["char"], True, char_data["color"])
                    char_surface.set_alpha(char_data["alpha"])
                    screen.blit(char_surface, (rain["x"], char_y))
        
        # Draw particles
        for p in particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            pygame.draw.circle(
                screen, 
                p["color"], 
                (int(p["x"]), int(p["y"])), 
                int(p["size"])
            )
        
        # Draw title and subtitle with glow effect
        screen.blit(title_shadow, title_shadow_rect)
        screen.blit(title, title_rect)
        screen.blit(subtitle, subtitle_rect)
        
        # Draw buttons
        keyboard_btn.draw(screen)
        gesture_btn.draw(screen)
        back_btn.draw(screen)
        
        pygame.display.flip()
    
    return "menu"

def run_crazy_mode(screen, font, music_manager=None, use_gestures=False):  # HellF**K Mode
    # Start crazy mode music if music manager is provided
    if music_manager:
        music_manager.play_music_for_mode('crazy')
    # Use a mix of keyboard controls for crazy mode
    controls = {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "down": pygame.K_s,
        "rotate": pygame.K_w,
        "hard_drop": pygame.K_SPACE
    }
    
    # Determine which controls to use based on the selection
    if use_gestures:
        # Initialize MediaPipe for hand tracking if using gestures
        import mediapipe as mp
        import cv2
        
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        
        # Initialize the webcam
        cap = cv2.VideoCapture(0)
        hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Create a window for hand tracking visualization
        cv2.namedWindow('Hand Tracking', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Hand Tracking', 400, 300)
        
        # Show a message that gesture controls are active
        print("OverDrive mode with Gesture Controls activated!")
    else:
        # Show a message that keyboard controls are active
        print("OverDrive mode with Keyboard Controls activated!")
    
    # Create a single game instance centered on screen but lowered a bit
    game = TetrisGame(SCREEN_WIDTH // 2 - (GRID_WIDTH * GRID_SIZE) // 2, controls)
    # Lower the game position
    game.y_offset += 50  # Move down by 50 pixels
    
    # Add music manager to the game instance
    game.music_manager = music_manager
    
    # Apply HELLF**K effects - much more intense
    game.fall_speed *= 0.4  # Make it MUCH faster
    game.illusion_active = True
    game.illusion_intensity = 0.3  # Increase illusion intensity (default is 0.1)
    game.grid_pulse_speed = 8.0  # Faster grid pulsing
    game.shake_intensity = 18  # More intense shaking
    game.target_rotation = 25  # More extreme rotation
    game.grid_line_speed = 5.0  # Faster grid lines
    
    # Set hellish color scheme (reddish-orange)
    game.bg_color = (40, 0, 0)  # Dark red background
    game.grid_color = (120, 40, 0)  # Reddish-orange grid
    game.grid_glow_color = (255, 80, 0)  # Bright orange glow
    
    # Add HELLFIRE particles - more of them with reddish-orange colors
    for _ in range(250):  # More particles
        game.particles.append({
            'x': random.randint(0, GRID_WIDTH * GRID_SIZE),
            'y': random.randint(0, GRID_HEIGHT * GRID_SIZE),
            'size': random.uniform(1.5, 4.5),  # Larger particles
            'speed': random.uniform(2, 5),  # Faster particles
            'color': (
                random.randint(200, 255),  # High red
                random.randint(20, 120),   # Medium green (for orange tint)
                random.randint(0, 40)      # Low blue (for reddish effect)
            ),
            'direction': random.uniform(0, 2 * math.pi),
            'life': random.uniform(0.7, 1.3)  # Variable lifespans
        })
    
    # Setup for game modifications
    last_effect_change_time = time.time()
    current_effect = "normal"
    flash_message = ""
    message_timer = 0
    
    # Variables for gesture control if enabled
    if use_gestures:
        last_gesture = None
        gesture_cooldown = 0
        gesture_cooldown_time = 0.2  # seconds between gesture recognition
        finger_states = {
            "thumb": False,
            "index": False,
            "middle": False,
            "ring": False,
            "pinky": False
        }
    
    # New crazy mode effect variables
    screen_rotation = 0  # Current screen rotation in degrees
    target_rotation = 0  # Target rotation to animate towards
    rotation_speed = 0.5  # Speed of rotation change
    zoom_level = 1.0  # Zoom level (1.0 = normal)
    target_zoom = 1.0  # Target zoom to animate towards
    screen_shake_intensity = 0  # Screen shake intensity
    screen_shake_duration = 0  # How long the shake lasts
    
    # New wild mechanics
    invert_colors = False  # Invert all colors on screen
    time_warp = False  # Randomly speed up and slow down time
    time_warp_factor = 1.0  # Current time warp factor
    ghost_pieces = False  # Show multiple ghost pieces
    pixelate_mode = False  # Pixelate the screen
    pixelate_factor = 1  # Pixelation factor
    pixelate_duration = 0  # How long pixelation lasts
    
    while True:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            # Check for direct menu button clicks when game is over
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                if game.game_over and game.menu_button_rect and game.menu_button_rect.collidepoint(mouse_pos):
                    print("Crazy mode menu button clicked!")
                    return "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                elif event.key == pygame.K_r:
                    game.reset()
                    # Reset crazy effects
                    screen_rotation = 0
                    target_rotation = 0
                    zoom_level = 1.0
                    target_zoom = 1.0
                    screen_shake_intensity = 0
                    screen_shake_duration = 0
                    invert_colors = False
                    time_warp = False
                    time_warp_factor = 1.0
                    ghost_pieces = False
                    pixelate_mode = False
                    pixelate_factor = 1
                    pixelate_duration = 0
                else:
                    # Handle keyboard input only if not using gestures
                    if not use_gestures:
                        result = game.handle_input(event)
                        if result == "menu":
                            return "menu"
        
        # Every 5-8 seconds, change the game effect
        if current_time - last_effect_change_time > random.uniform(5, 8):
            last_effect_change_time = current_time
            effect_choice = random.randint(0, 7)
            
            # Apply a random effect
            if effect_choice == 0:
                # Normal mode - but still hellish
                current_effect = "normal"
                target_rotation = random.randint(-10, 10)  # Slight rotation even in normal mode
                reverse_gravity = False
                target_zoom = random.uniform(0.95, 1.05)  # Slight zoom variation
                screen_shake_intensity = 3  # Slight shake always present
                flash_message = "HELLISH NORMAL"
            elif effect_choice == 1:
                # Rotate the screen - more extreme
                current_effect = "rotate"
                target_rotation = random.choice([45, 90, 135, 180, 225, 270, 315])  # More rotation angles
                flash_message = "INFERNAL ROTATION"
            elif effect_choice == 2:
                # Pixelate mode - much more extreme pixelation
                current_effect = "pixelate"
                pixelate_mode = True
                pixelate_factor = random.randint(8, 20)  # Much more pixelated
                pixelate_duration = random.uniform(7.0, 12.0)  # Longer duration
                flash_message = "DIGITAL HELL"
            elif effect_choice == 3:
                # Extreme zoom in/out
                current_effect = "zoom"
                target_zoom = random.uniform(0.5, 1.8)  # More extreme zoom levels
                flash_message = "DIMENSIONAL SHIFT"
            elif effect_choice == 4:
                # Violent screen shake
                current_effect = "shake"
                screen_shake_intensity = random.randint(15, 30)  # Much more intense shaking
                screen_shake_duration = random.uniform(8.0, 15.0)  # Even longer duration
                flash_message = "HELLQUAKE"
            elif effect_choice == 5:
                # Demonic color inversion
                current_effect = "invert"
                invert_colors = not invert_colors
                if invert_colors:
                    # Apply a red filter when inverting
                    game.color_filter = (255, 50, 50)  # Reddish filter
                    flash_message = "DEMONIC VISION"
                else:
                    game.color_filter = None
                    flash_message = "VISION RESTORED"
            elif effect_choice == 6:
                # Extreme time distortion
                current_effect = "time_warp"
                time_warp = not time_warp
                if time_warp:
                    # More extreme time warping
                    time_warp_factor = random.choice([0.3, 0.5, 2.0, 3.0])  # More extreme speeds
                    flash_message = "INFERNAL TIME DISTORTION!"
                else:
                    time_warp_factor = 1.0
                    flash_message = "TIME STABILIZED!"
            elif effect_choice == 7:
                # Demonic ghost pieces - show many ghost pieces
                current_effect = "ghost"
                ghost_pieces = not ghost_pieces
                if ghost_pieces:
                    # Add more ghost effects
                    game.ghost_count = random.randint(5, 10)  # Show multiple ghost pieces
                    game.ghost_alpha = 120  # More visible ghosts
                    flash_message = "DEMONIC APPARITIONS!"
                else:
                    game.ghost_count = 1
                    game.ghost_alpha = 80  # Default ghost alpha
                    flash_message = "DEMONS BANISHED!"
                    
            message_timer = 2.0  # Show message for 2 seconds
        
        # Update message timer
        if message_timer > 0:
            message_timer -= 0.016  # Assuming ~60fps
        
        # Apply crazy effects
        
        # Handle screen rotation animation
        if screen_rotation != target_rotation:
            # Find shortest path to target rotation
            diff = target_rotation - screen_rotation
            if abs(diff) > 180:
                diff = diff - 360 if diff > 0 else diff + 360
                
            # Gradually rotate towards target
            if abs(diff) <= rotation_speed:
                screen_rotation = target_rotation
            else:
                screen_rotation += rotation_speed if diff > 0 else -rotation_speed
            screen_rotation %= 360
        
        # Handle zoom animation
        if zoom_level != target_zoom:
            zoom_diff = target_zoom - zoom_level
            zoom_speed = 0.01
            if abs(zoom_diff) <= zoom_speed:
                zoom_level = target_zoom
            else:
                zoom_level += zoom_speed if zoom_diff > 0 else -zoom_speed
        
        # Handle screen shake
        shake_x = 0
        shake_y = 0
        if screen_shake_intensity > 0:
            # Convert to int for randint
            intensity_int = int(screen_shake_intensity)
            shake_x = random.randint(-intensity_int, intensity_int) if intensity_int > 0 else 0
            shake_y = random.randint(-intensity_int, intensity_int) if intensity_int > 0 else 0
            # Gradually reduce shake intensity
            screen_shake_intensity = max(0, screen_shake_intensity - 0.1)
        
        # Handle screen shake with longer duration
        shake_x = 0
        shake_y = 0
        if screen_shake_intensity > 0:
            # Convert to int for randint
            intensity_int = int(screen_shake_intensity)
            shake_x = random.randint(-intensity_int, intensity_int) if intensity_int > 0 else 0
            shake_y = random.randint(-intensity_int, intensity_int) if intensity_int > 0 else 0
            
            # Only reduce intensity if duration is up
            if screen_shake_duration <= 0:
                screen_shake_intensity = max(0, screen_shake_intensity - 0.1)
            else:
                screen_shake_duration -= 0.016  # Reduce duration counter
                
        # Handle pixelate mode duration
        if pixelate_mode and pixelate_duration > 0:
            pixelate_duration -= 0.016  # Reduce duration counter (assuming ~60 FPS)
            if pixelate_duration <= 0:
                pixelate_mode = False
                pixelate_factor = 1
                if random.random() < 0.3:  # 30% chance to show a message
                    flash_message = "HD RESTORED!"
                    message_timer = 1.0
        
        # Handle time warp effect
        if time_warp:
            # Randomly fluctuate the time warp factor
            if random.random() < 0.05:  # 5% chance each frame to change speed
                time_warp_factor = random.uniform(0.5, 2.0)  # Less extreme range
                
            # Apply time warp to game speed but not to player movement
            # Store original fall speed before update
            original_fall_speed = game.fall_speed
            # Apply time warp only to the automatic falling
            game.fall_speed = original_fall_speed / time_warp_factor
        
        # Process gesture input if enabled
        if use_gestures:
            gesture_cooldown -= 0.016  # Assuming ~60fps
            
            # Process hand gesture input
            success, img = cap.read()
            if success:
                # Flip horizontally for more intuitive interaction
                img = cv2.flip(img, 1)
                
                # Convert to RGB for MediaPipe
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Process hand landmarks
                results = hands.process(img_rgb)
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks on the image
                        mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        # Get fingertip y-coordinates
                        fingertips = [
                            hand_landmarks.landmark[4],   # Thumb
                            hand_landmarks.landmark[8],   # Index
                            hand_landmarks.landmark[12],  # Middle
                            hand_landmarks.landmark[16],  # Ring
                            hand_landmarks.landmark[20]   # Pinky
                        ]
                        
                        # Get base of palm y-coordinate
                        wrist = hand_landmarks.landmark[0]
                        
                        # Update finger states (finger is up if fingertip is higher than wrist)
                        finger_states = {
                            "thumb": fingertips[0].y < wrist.y,
                            "index": fingertips[1].y < wrist.y,
                            "middle": fingertips[2].y < wrist.y,
                            "ring": fingertips[3].y < wrist.y,
                            "pinky": fingertips[4].y < wrist.y
                        }
                        
                        # Process gestures if cooldown expired
                        if gesture_cooldown <= 0:
                            # All fingers up = Hard Drop
                            if all(finger_states.values()):
                                game.hard_drop()
                                gesture_cooldown = gesture_cooldown_time
                                # Add visual feedback
                                flash_message = "HARD DROP"
                                message_timer = 0.5
                            # Thumb up = Rotate
                            elif finger_states["thumb"] and not any([finger_states["index"], finger_states["middle"], finger_states["ring"], finger_states["pinky"]]):
                                game.rotate_piece()
                                gesture_cooldown = gesture_cooldown_time
                            # Index up = Move Left
                            elif finger_states["index"] and not any([finger_states["thumb"], finger_states["middle"], finger_states["ring"], finger_states["pinky"]]):
                                game.move(-1, 0)
                                gesture_cooldown = gesture_cooldown_time
                            # Middle up = Move Down
                            elif finger_states["middle"] and not any([finger_states["thumb"], finger_states["index"], finger_states["ring"], finger_states["pinky"]]):
                                game.move(0, 1)
                                gesture_cooldown = gesture_cooldown_time
                            # Pinky up = Move Right
                            elif finger_states["pinky"] and not any([finger_states["thumb"], finger_states["index"], finger_states["middle"], finger_states["ring"]]):
                                game.move(1, 0)
                                gesture_cooldown = gesture_cooldown_time
                
                # Display hand tracking window
                cv2.imshow('Hand Tracking', img)
                cv2.waitKey(1)
        
        # Update the game
        game.update()
        
        # Restore original fall speed after update if time warp is active
        if time_warp:
            game.fall_speed = original_fall_speed
        
        # Draw trippy background
        screen.fill(BLACK)
        
        # Draw wavy grid background
        for y in range(0, SCREEN_HEIGHT, 8):
            color_shift = int(128 + 127 * math.sin(current_time * 2 + y * 0.01))
            color = (color_shift, int(color_shift * 0.5), 255 - color_shift)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y), 4)
        
        # Create a surface for the game that we can rotate/transform
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        game_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw the game on the separate surface
        game.draw(game_surface, font, ghost_pieces=ghost_pieces)
        
        # Apply pixelate mode if active
        if pixelate_mode and pixelate_factor > 1:
            # Create a smaller surface and scale it back up to create pixelation effect
            w, h = game_surface.get_size()
            small_surface = pygame.transform.scale(game_surface, (w // pixelate_factor, h // pixelate_factor))
            game_surface = pygame.transform.scale(small_surface, (w, h))
        
        # Apply color inversion if active
        if invert_colors:
            # Create a negative version of the surface
            negative = pygame.Surface(game_surface.get_size(), pygame.SRCALPHA)
            negative.fill((255, 255, 255, 255))
            negative.blit(game_surface, (0, 0), special_flags=pygame.BLEND_SUB)
            game_surface = negative
        
        # Apply transformations to the game surface
        if screen_rotation != 0 or zoom_level != 1.0 or screen_shake_intensity > 0:
            # Get the center of the game area
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
            
            # Scale the surface if zooming
            if zoom_level != 1.0:
                scaled_width = int(game_surface.get_width() * zoom_level)
                scaled_height = int(game_surface.get_height() * zoom_level)
                game_surface = pygame.transform.smoothscale(game_surface, (scaled_width, scaled_height))
            
            # Rotate the surface
            if screen_rotation != 0:
                game_surface = pygame.transform.rotate(game_surface, screen_rotation)
            
            # Calculate position with shake offset
            pos_x = center_x - game_surface.get_width() // 2 + shake_x
            pos_y = center_y - game_surface.get_height() // 2 + shake_y
            
            # Draw the transformed surface
            screen.blit(game_surface, (pos_x, pos_y))
        else:
            # No transformations, just draw directly
            screen.blit(game_surface, (0, 0))
        
        # Draw title with pulsing effect
        title_size = int(40 + 10 * math.sin(current_time * 5))
        title_font = pygame.font.Font(None, title_size)
        title_color = (255, int(128 + 127 * math.sin(current_time * 3)), int(128 + 127 * math.cos(current_time * 3)))
        title_surface = title_font.render("CRAZY MODE", True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 30))
        screen.blit(title_surface, title_rect)
        
        # Draw flash message if active
        if message_timer > 0:
            # Make message pulse and fade
            msg_alpha = int(255 * min(1, message_timer))
            msg_size = int(50 + 20 * math.sin(current_time * 10))
            msg_font = pygame.font.Font(None, msg_size)
            msg_surface = msg_font.render(flash_message, True, (255, 50, 50))
            msg_surface.set_alpha(msg_alpha)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            screen.blit(msg_surface, msg_rect)
        
        # Draw instructions with smaller font
        instructions = [
            "Controls:",
            "A/D: Move left/right",
            "S: Move down",
            "W: Rotate",
            "SPACE: Hard drop",
            "R: Reset game",
            "ESC: Back to menu"
        ]
        
        small_font = pygame.font.Font(None, 24)  # Smaller font
        for i, text in enumerate(instructions):
            text_surface = small_font.render(text, True, WHITE)
            screen.blit(text_surface, (20, GRID_HEIGHT * GRID_SIZE + 60 + i * 20))  # Adjusted position and spacing
        
        pygame.display.flip()
    
    return "menu"

def run_gesture_mode(screen, font, music_manager=None):
    # Start standard game music if music manager is provided
    if music_manager:
        music_manager.play_music_for_mode('standard')
        
    # Background effect variables - brighter colors
    background_colors = []
    for i in range(15):  # More color variety
        # Create vibrant color palette
        if i % 3 == 0:  # Reds/pinks
            background_colors.append((random.randint(150, 255), random.randint(20, 100), random.randint(100, 200)))
        elif i % 3 == 1:  # Blues/purples
            background_colors.append((random.randint(50, 150), random.randint(50, 150), random.randint(150, 255)))
        else:  # Yellows/greens
            background_colors.append((random.randint(150, 255), random.randint(150, 255), random.randint(20, 100)))
    
    # Create more animated background elements with faster movement
    background_elements = []
    for _ in range(50):  # More elements
        size = random.randint(30, 150)  # Larger elements
        background_elements.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'size': size,
            'speed_x': random.uniform(-2.5, 2.5),  # Faster movement
            'speed_y': random.uniform(-2.5, 2.5),
            'rotation': random.uniform(0, 360),
            'rotation_speed': random.uniform(-5, 5),  # Faster rotation
            'color': random.choice(background_colors),
            'pulse_rate': random.uniform(1.0, 3.0),  # For size pulsing
            'pulse_amount': random.uniform(0.7, 1.3),  # For size pulsing
            'original_size': size  # Store original size for pulsing
        })
    print("Starting gesture mode...")
    gesture_controller = None
    camera_available = False
    
    try:
        # Import with error handling
        try:
            from gesture_control import GestureController, get_gesture_instructions
            print("Successfully imported gesture_control module")
        except ImportError as e:
            print(f"Error importing gesture_control: {e}")
            import traceback
            traceback.print_exc()
            return "menu"
        
        import traceback
        
        controls = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "down": pygame.K_DOWN,
            "rotate": pygame.K_UP,
            "hard_drop": pygame.K_SPACE
        }
        
        print("Setting up game position...")
        # Position the game box lower on the screen in gesture mode
        vertical_offset = 50  # Move down by 50 pixels
        game = TetrisGame(SCREEN_WIDTH // 2 - (GRID_WIDTH * GRID_SIZE) // 2, controls, y_offset=vertical_offset)
        print("Game object created successfully")
        
        # Add music manager to the game instance
        game.music_manager = music_manager
        
        # Initialize gesture controller with error handling
        print("Initializing gesture controller...")
        try:
            # Check if camera is enabled and if window should be shown based on settings
            if SETTINGS['camera_enabled']:
                show_camera = SETTINGS['show_camera_window']
                gesture_controller = GestureController(show_camera_window=show_camera)
                print("Gesture controller initialized")
                camera_available = gesture_controller.camera_available
                print(f"Camera available: {camera_available}")
            else:
                gesture_controller = None
                camera_available = False
                print("Camera disabled in settings")
        except Exception as e:
            print(f"Failed to initialize gesture controller: {e}")
            traceback.print_exc()
            camera_available = False
            gesture_controller = None
        
        # Display messages for game mode
        print("Setting up game messages...")
        message_font = pygame.font.Font(None, 36)
        camera_error_text = message_font.render("Camera not available. Using keyboard controls.", True, YELLOW)
        camera_error_rect = camera_error_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        fallback_mode = not camera_available
        fallback_text = message_font.render("KEYBOARD MODE ACTIVE", True, GREEN)
        fallback_rect = fallback_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        print("Game messages set up successfully")
        
        print("Starting main game loop...")
        clock = pygame.time.Clock()
        running = True
        frame_count = 0
        
        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds
            frame_count += 1
            
            if frame_count % 60 == 0:  # Log every 60 frames
                print(f"Game running: frame {frame_count}")
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Quit event received")
                    if gesture_controller:
                        print("Cleaning up gesture controller...")
                        gesture_controller.cleanup()
                    return None
                # Check for direct menu button clicks when game is over
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    if game.game_over and game.menu_button_rect and game.menu_button_rect.collidepoint(mouse_pos):
                        print("Gesture mode menu button clicked!")
                        if gesture_controller:
                            gesture_controller.cleanup()
                        return "menu"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("Escape key pressed, returning to menu")
                        if gesture_controller:
                            gesture_controller.cleanup()
                        return "menu"
                    elif event.key == pygame.K_r:
                        print("Reset key pressed")
                        game.reset()
                    # Allow keyboard controls even in gesture mode
                    result = game.handle_input(event)
                    if result == "menu":
                        if gesture_controller:
                            gesture_controller.cleanup()
                        return "menu"
            
            # Get gesture and convert to game input if camera is available
            if camera_available and gesture_controller:
                try:
                    print("Attempting to detect gesture...")
                    gesture = gesture_controller.detect_gesture()
                    if gesture == "escape":
                        print("Received escape signal from gesture controller")
                        if gesture_controller:
                            gesture_controller.cleanup()
                        return "menu"
                    elif gesture:
                        print(f"Detected gesture: {gesture}")
                        if gesture in controls:
                            print(f"Converting gesture to key: {controls[gesture]}")
                            # Create a synthetic keyboard event
                            event = pygame.event.Event(pygame.KEYDOWN, {"key": controls[gesture]})
                            result = game.handle_input(event)
                            if result == "menu":
                                if gesture_controller:
                                    gesture_controller.cleanup()
                                return "menu"
                except Exception as e:
                    print(f"Error detecting gesture: {e}")
                    traceback.print_exc()
                    # Don't crash on gesture detection errors
                    pass
            
            # Update and render game
            game.update()
            
            # Draw illusory background
            screen.fill(BLACK)
            
            # Update and draw background elements
            current_time = time.time()
            for element in background_elements:
                # Update position
                element['x'] += element['speed_x']
                element['y'] += element['speed_y']
                element['rotation'] += element['rotation_speed']
                
                # Wrap around screen edges
                if element['x'] < -element['size']:
                    element['x'] = SCREEN_WIDTH + element['size']
                elif element['x'] > SCREEN_WIDTH + element['size']:
                    element['x'] = -element['size']
                if element['y'] < -element['size']:
                    element['y'] = SCREEN_HEIGHT + element['size']
                elif element['y'] > SCREEN_HEIGHT + element['size']:
                    element['y'] = -element['size']
                
                # Draw element - use different shapes for variety
                shape_type = hash(str(element)) % 3
                
                # Adjust color based on time for more dramatic animation
                r, g, b = element['color']
                color_shift_r = int(50 * math.sin(current_time * 1.5 + element['x'] / 80))
                color_shift_g = int(50 * math.sin(current_time * 2.0 + element['y'] / 80 + 2))
                color_shift_b = int(50 * math.sin(current_time * 2.5 + (element['x'] + element['y']) / 100 + 4))
                
                color = (min(255, max(0, r + color_shift_r)), 
                         min(255, max(0, g + color_shift_g)), 
                         min(255, max(0, b + color_shift_b)))
                
                # Pulse the size based on time
                size_factor = 1.0 + 0.3 * math.sin(current_time * element['pulse_rate'])
                current_size = int(element['original_size'] * size_factor)
                
                if shape_type == 0:  # Rectangle
                    # Create a surface for rotation - brighter and more visible
                    s = pygame.Surface((current_size, current_size // 2), pygame.SRCALPHA)
                    s.fill((*color, 60))  # More opaque
                    
                    # Add a glowing outline
                    pygame.draw.rect(s, (*color, 120), 
                                    (0, 0, current_size, current_size // 2), 
                                    max(1, current_size // 20))
                    
                    # Rotate the surface
                    s = pygame.transform.rotate(s, element['rotation'])
                    
                    # Blit to screen
                    screen.blit(s, (element['x'] - s.get_width() // 2, 
                                    element['y'] - s.get_height() // 2))
                    
                elif shape_type == 1:  # Circle
                    s = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
                    
                    # Draw filled circle
                    pygame.draw.circle(s, (*color, 40), 
                                      (current_size // 2, current_size // 2), 
                                      current_size // 2)
                    
                    # Draw glowing outline
                    pygame.draw.circle(s, (*color, 100), 
                                      (current_size // 2, current_size // 2), 
                                      current_size // 2, 
                                      max(1, current_size // 15))
                    
                    # Add a pulsing inner circle
                    inner_size = int(current_size * 0.6 * (0.7 + 0.3 * math.sin(current_time * 3)))
                    pygame.draw.circle(s, (*color, 80), 
                                      (current_size // 2, current_size // 2), 
                                      inner_size)
                    
                    screen.blit(s, (element['x'] - current_size // 2, 
                                    element['y'] - current_size // 2))
                    
                else:  # Star shape instead of triangle
                    s = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
                    
                    # Draw a star
                    center_x, center_y = current_size // 2, current_size // 2
                    outer_radius = current_size // 2
                    inner_radius = current_size // 4
                    points = 5  # 5-pointed star
                    
                    star_points = []
                    for i in range(points * 2):
                        angle = math.pi * 2 * i / (points * 2)
                        radius = outer_radius if i % 2 == 0 else inner_radius
                        x = center_x + radius * math.sin(angle)
                        y = center_y + radius * math.cos(angle)
                        star_points.append((x, y))
                    
                    # Draw filled star
                    pygame.draw.polygon(s, (*color, 50), star_points)
                    
                    # Draw outline
                    pygame.draw.polygon(s, (*color, 120), star_points, max(1, current_size // 20))
                    
                    # Rotate the surface
                    s = pygame.transform.rotate(s, element['rotation'])
                    
                    # Blit to screen
                    screen.blit(s, (element['x'] - s.get_width() // 2, 
                                    element['y'] - s.get_height() // 2))
                    
                # Add occasional light beams from shapes
                if random.random() < 0.02:  # 2% chance per shape per frame
                    beam_length = random.randint(100, 300)
                    beam_width = random.randint(2, 8)
                    beam_angle = random.uniform(0, 2 * math.pi)
                    
                    end_x = element['x'] + beam_length * math.cos(beam_angle)
                    end_y = element['y'] + beam_length * math.sin(beam_angle)
                    
                    beam_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(beam_surface, (*color, 100), 
                                    (element['x'], element['y']), 
                                    (end_x, end_y), beam_width)
                    screen.blit(beam_surface, (0, 0))
            
            # Draw the game on top of the background
            game.draw(screen, font)
            
            # Draw camera status messages
            if not camera_available:
                # No camera available
                screen.blit(camera_error_text, camera_error_rect)
                screen.blit(fallback_text, fallback_rect)
                
                # Draw additional instructions for keyboard controls
                keyboard_instructions = [
                    "Use keyboard controls:",
                    "← → : Move left/right",
                    "↑ : Rotate",
                    "↓ : Move down",
                    "Space : Hard drop",
                    "R : Reset game"
                ]
                
                for i, line in enumerate(keyboard_instructions):
                    text = pygame.font.Font(None, 24).render(line, True, YELLOW)
                    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 150 + i * 30))
            else:
                # Camera is available - check if it's a mock camera
                if hasattr(gesture_controller, 'using_mock_camera') and gesture_controller.using_mock_camera:
                    mock_text = pygame.font.Font(None, 24).render("USING MOCK CAMERA - No real camera available", True, RED)
                    screen.blit(mock_text, (SCREEN_WIDTH // 2 - mock_text.get_width() // 2, 120))
                # Draw gesture instructions with smaller font
                try:
                    instructions = get_gesture_instructions().split('\n')
                    for i, line in enumerate(instructions):
                        if line.strip():  # Only render non-empty lines
                            text = pygame.font.Font(None, 18).render(line.strip(), True, WHITE)
                            screen.blit(text, (20, GRID_HEIGHT * GRID_SIZE + vertical_offset + 10 + i * 16))
                except Exception as e:
                    print(f"Error rendering gesture instructions: {e}")
                    traceback.print_exc()
            
            pygame.display.flip()
            
    except Exception as e:
        print(f"Error in gesture mode: {e}")
        traceback.print_exc()
    
    # Clean up resources
    if gesture_controller:
        try:
            print("Cleaning up gesture controller...")
            gesture_controller.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            traceback.print_exc()
    
    print("Exiting gesture mode")
    return "menu"

# Game settings
SETTINGS = {
    'show_camera_window': True,  # Whether to show the camera window in gesture mode
    'music_volume': 0.5,         # Music volume (0.0 to 1.0)
    'sound_volume': 1.0,         # Sound effects volume (0.0 to 1.0)
    'camera_enabled': True       # Whether the camera is enabled for gesture recognition
}

def save_settings():
    """Save settings to a file"""
    import json
    try:
        with open('settings.json', 'w') as f:
            json.dump(SETTINGS, f)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    """Load settings from a file"""
    import json
    try:
        with open('settings.json', 'r') as f:
            loaded_settings = json.load(f)
            # Update global settings
            for key, value in loaded_settings.items():
                SETTINGS[key] = value
    except FileNotFoundError:
        # If file doesn't exist, create it with default settings
        save_settings()
    except Exception as e:
        print(f"Error loading settings: {e}")

def run_settings_menu(screen, font, music_manager):
    """Settings menu screen"""
    # Create UI elements
    title_font = pygame.font.Font(None, 72)
    title_text = title_font.render("Settings", True, CYAN)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
    
    # Slider control variables
    dragging_slider = False
    dragging_sound_slider = False
    
    # Back button
    back_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 60, "Back to Menu", font)
    
    # Camera window toggle
    camera_toggle_text = font.render("Show Camera Window:", True, WHITE)
    camera_toggle_rect = camera_toggle_text.get_rect(topleft=(SCREEN_WIDTH // 2 - 250, 200))
    
    # Camera enabled toggle
    camera_enabled_text = font.render("Enable Camera for Gestures:", True, WHITE)
    camera_enabled_rect = camera_enabled_text.get_rect(topleft=(SCREEN_WIDTH // 2 - 250, 250))
    
    # Volume sliders
    volume_text = font.render("Music Volume:", True, WHITE)
    volume_rect = volume_text.get_rect(topleft=(SCREEN_WIDTH // 2 - 250, 300))
    
    sound_volume_text = font.render("Sound Effects Volume:", True, WHITE)
    sound_volume_rect = sound_volume_text.get_rect(topleft=(SCREEN_WIDTH // 2 - 250, 400))
    
    # Music slider properties
    slider_width = 300
    slider_height = 20
    slider_x = SCREEN_WIDTH // 2 - 250
    slider_y = 350
    slider_knob_radius = 15
    slider_knob_x = slider_x + int(SETTINGS['music_volume'] * slider_width)
    
    # Sound effects slider properties
    sound_slider_width = 300
    sound_slider_height = 20
    sound_slider_x = SCREEN_WIDTH // 2 - 250
    sound_slider_y = 450
    sound_slider_knob_radius = 15
    sound_slider_knob_x = sound_slider_x + int(SETTINGS['sound_volume'] * sound_slider_width)
    
    # Sound pack selection
    sound_pack_text = font.render("Sound Pack:", True, WHITE)
    sound_pack_rect = sound_pack_text.get_rect(topleft=(SCREEN_WIDTH // 2 - 250, 500))
    
    # Sound pack dropdown/selection
    if music_manager:
        sound_packs = music_manager.scan_custom_sound_packs()['packs']
        active_pack = music_manager.active_sound_pack
    else:
        sound_packs = {'default': {'name': 'Default Sounds'}}
        active_pack = 'default'
    
    # Sound pack buttons - we'll display them as a list
    sound_pack_buttons = []
    y_offset = 530
    for pack_id, pack_info in sound_packs.items():
        is_active = (pack_id == active_pack)
        button_color = CYAN if is_active else DARK_GRAY
        button = Button(SCREEN_WIDTH // 2, y_offset, 200, 40, pack_info['name'], font, button_color)
        sound_pack_buttons.append((pack_id, button))
        y_offset += 50
    
    # Toggle button properties for camera window
    toggle_width = 80
    toggle_height = 40
    toggle_x = SCREEN_WIDTH // 2 + 100
    toggle_y = 200
    toggle_radius = toggle_height // 2
    toggle_knob_x = toggle_x + (toggle_width - toggle_radius * 2) * (1 if SETTINGS['show_camera_window'] else 0) + toggle_radius
    
    # Toggle button properties for camera enabled
    toggle2_width = 80
    toggle2_height = 40
    toggle2_x = SCREEN_WIDTH // 2 + 100
    toggle2_y = 250
    toggle2_radius = toggle2_height // 2
    toggle2_knob_x = toggle2_x + (toggle2_width - toggle2_radius * 2) * (1 if SETTINGS['camera_enabled'] else 0) + toggle2_radius
    
    # Animation variables
    clock = pygame.time.Clock()
    current_time = 0
    
    # Main settings loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        current_time += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if back button clicked
                    if back_button.rect.collidepoint(mouse_pos):
                        # Save settings before returning to menu
                        save_settings()
                        return "menu"
                    

                    
                    # Check if any sound pack button is clicked
                    for pack_id, button in sound_pack_buttons:
                        if button.rect.collidepoint(mouse_pos):
                            if music_manager:
                                music_manager.set_active_sound_pack(pack_id)
                                # Update active pack and refresh buttons
                                active_pack = pack_id
                                # Refresh the button colors
                                sound_pack_buttons = []
                                y_offset = 530
                                for pid, pinfo in sound_packs.items():
                                    is_active = (pid == active_pack)
                                    button_color = CYAN if is_active else DARK_GRAY
                                    btn = Button(SCREEN_WIDTH // 2, y_offset, 200, 40, pinfo['name'], font, button_color)
                                    sound_pack_buttons.append((pid, btn))
                                    y_offset += 50
                    
                    # Check if camera window toggle button clicked
                    toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)
                    if toggle_rect.collidepoint(mouse_pos):
                        SETTINGS['show_camera_window'] = not SETTINGS['show_camera_window']
                    
                    # Check if camera enabled toggle button clicked
                    toggle2_rect = pygame.Rect(toggle2_x, toggle2_y, toggle2_width, toggle2_height)
                    if toggle2_rect.collidepoint(mouse_pos):
                        SETTINGS['camera_enabled'] = not SETTINGS['camera_enabled']
                        
                    # Update music manager with new volume
                    if music_manager:
                        music_manager.set_volume(SETTINGS['music_volume'])
                    
                    # Check if music slider clicked
                    slider_rect = pygame.Rect(slider_x, slider_y - slider_height // 2, slider_width, slider_height * 2)
                    if slider_rect.collidepoint(mouse_pos):
                        dragging_slider = True
                        # Update slider position and volume
                        slider_knob_x = max(slider_x, min(slider_x + slider_width, mouse_pos[0]))
                        SETTINGS['music_volume'] = (slider_knob_x - slider_x) / slider_width
                        # Update music manager with new volume
                        if music_manager:
                            music_manager.set_volume(SETTINGS['music_volume'])
                    
                    # Check if sound effects slider clicked
                    sound_slider_rect = pygame.Rect(sound_slider_x, sound_slider_y - sound_slider_height // 2, sound_slider_width, sound_slider_height * 2)
                    if sound_slider_rect.collidepoint(mouse_pos):
                        dragging_sound_slider = True
                        # Update slider position and volume
                        sound_slider_knob_x = max(sound_slider_x, min(sound_slider_x + sound_slider_width, mouse_pos[0]))
                        SETTINGS['sound_volume'] = (sound_slider_knob_x - sound_slider_x) / sound_slider_width
                        # Update music manager with new sound volume
                        if music_manager:
                            music_manager.set_sound_volume(SETTINGS['sound_volume'])
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    dragging_slider = False
                    dragging_sound_slider = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging_slider:
                    # Update slider position and volume
                    slider_knob_x = max(slider_x, min(slider_x + slider_width, event.pos[0]))
                    SETTINGS['music_volume'] = (slider_knob_x - slider_x) / slider_width
                    # Update music manager with new volume
                    if music_manager:
                        music_manager.set_volume(SETTINGS['music_volume'])
                        
                if dragging_sound_slider:
                    # Update sound slider position and volume
                    sound_slider_knob_x = max(sound_slider_x, min(sound_slider_x + sound_slider_width, event.pos[0]))
                    SETTINGS['sound_volume'] = (sound_slider_knob_x - sound_slider_x) / sound_slider_width
                    # Update music manager with new sound volume
                    if music_manager:
                        music_manager.set_sound_volume(SETTINGS['sound_volume'])
        
        # Update toggle knob positions with animation - faster animation to avoid disappearing
        target_toggle_x = toggle_x + (toggle_width - toggle_radius * 2) * (1 if SETTINGS['show_camera_window'] else 0) + toggle_radius
        toggle_knob_x = target_toggle_x  # Immediate position update instead of animation
        
        target_toggle2_x = toggle2_x + (toggle2_width - toggle2_radius * 2) * (1 if SETTINGS['camera_enabled'] else 0) + toggle2_radius
        toggle2_knob_x = target_toggle2_x  # Immediate position update instead of animation
        
        # Draw background with animated pattern
        screen.fill(BLACK)
        
        # Draw grid background
        grid_size = 30
        for x in range(0, SCREEN_WIDTH, grid_size):
            for y in range(0, SCREEN_HEIGHT, grid_size):
                # Create subtle animated grid
                brightness = 20 + 10 * math.sin(current_time * 2 + (x + y) / 100)
                color = (brightness, brightness, brightness + 10)
                pygame.draw.line(screen, color, (x, 0), (x, SCREEN_HEIGHT), 1)
                pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y), 1)
        
        # Draw title
        glow_size = 3 + 2 * math.sin(current_time * 3)
        for offset in range(int(glow_size), 0, -1):
            alpha = int(150 * (offset / glow_size))
            glow_surface = title_font.render("Settings", True, (*CYAN[:3], alpha))
            glow_rect = glow_surface.get_rect(center=(title_rect.centerx, title_rect.centery))
            screen.blit(glow_surface, (glow_rect.x - offset, glow_rect.y))
            screen.blit(glow_surface, (glow_rect.x + offset, glow_rect.y))
            screen.blit(glow_surface, (glow_rect.x, glow_rect.y - offset))
            screen.blit(glow_surface, (glow_rect.x, glow_rect.y + offset))
        screen.blit(title_text, title_rect)
        
        # Draw camera toggles
        screen.blit(camera_toggle_text, camera_toggle_rect)
        screen.blit(camera_enabled_text, camera_enabled_rect)
        
        # Draw camera window toggle button with improved visibility
        toggle_color = CYAN if SETTINGS['show_camera_window'] else DARK_GRAY
        # Draw background track
        pygame.draw.rect(screen, DARK_GRAY, (toggle_x, toggle_y, toggle_width, toggle_height), border_radius=toggle_height // 2)
        # Draw active portion of track when enabled
        if SETTINGS['show_camera_window']:
            filled_width = toggle_width // 2 + toggle_radius
            pygame.draw.rect(screen, CYAN, (toggle_x, toggle_y, filled_width, toggle_height), border_radius=toggle_height // 2)
        # Draw toggle knob
        pygame.draw.circle(screen, toggle_color, (int(toggle_knob_x), toggle_y + toggle_height // 2), toggle_radius - 2)
        # Add a white outline to make it more visible
        pygame.draw.circle(screen, WHITE, (int(toggle_knob_x), toggle_y + toggle_height // 2), toggle_radius - 2, 1)
        
        # Draw camera enabled toggle button with improved visibility
        toggle2_color = CYAN if SETTINGS['camera_enabled'] else DARK_GRAY
        # Draw background track
        pygame.draw.rect(screen, DARK_GRAY, (toggle2_x, toggle2_y, toggle2_width, toggle2_height), border_radius=toggle2_height // 2)
        # Draw active portion of track when enabled
        if SETTINGS['camera_enabled']:
            filled_width = toggle2_width // 2 + toggle2_radius
            pygame.draw.rect(screen, CYAN, (toggle2_x, toggle2_y, filled_width, toggle2_height), border_radius=toggle2_height // 2)
        # Draw toggle knob
        pygame.draw.circle(screen, toggle2_color, (int(toggle2_knob_x), toggle2_y + toggle2_height // 2), toggle2_radius - 2)
        # Add a white outline to make it more visible
        pygame.draw.circle(screen, WHITE, (int(toggle2_knob_x), toggle2_y + toggle2_height // 2), toggle2_radius - 2, 1)
        
        # Draw volume text
        screen.blit(volume_text, volume_rect)
        
        # Draw sound volume text
        screen.blit(sound_volume_text, sound_volume_rect)
        
        # Draw volume value
        volume_value_text = font.render(f"{int(SETTINGS['music_volume'] * 100)}%", True, WHITE)
        volume_value_rect = volume_value_text.get_rect(topleft=(slider_x + slider_width + 20, slider_y - 10))
        screen.blit(volume_value_text, volume_value_rect)
        
        # Draw sound volume value
        sound_volume_value_text = font.render(f"{int(SETTINGS['sound_volume'] * 100)}%", True, WHITE)
        sound_volume_value_rect = sound_volume_value_text.get_rect(topleft=(sound_slider_x + sound_slider_width + 20, sound_slider_y - 10))
        screen.blit(sound_volume_value_text, sound_volume_value_rect)
        
        # Draw slider track
        pygame.draw.rect(screen, DARK_GRAY, (slider_x, slider_y - slider_height // 2, slider_width, slider_height), border_radius=slider_height // 2)
        
        # Draw filled portion of slider
        filled_width = int((SETTINGS['music_volume']) * slider_width)
        if filled_width > 0:
            pygame.draw.rect(screen, CYAN, 
                            (slider_x, slider_y - slider_height // 2, filled_width, slider_height),
                            border_radius=slider_height // 2)
        
        # Draw slider knob with glow effect
        for offset in range(5, 0, -1):
            alpha = int(150 * (offset / 5))
            pygame.draw.circle(screen, (*CYAN[:3], alpha), 
                              (int(slider_knob_x), slider_y), 
                              slider_knob_radius + offset)
        pygame.draw.circle(screen, WHITE, (int(slider_knob_x), slider_y), slider_knob_radius - 2)
        
        # Draw sound slider track
        pygame.draw.rect(screen, DARK_GRAY, (sound_slider_x, sound_slider_y - sound_slider_height // 2, sound_slider_width, sound_slider_height), border_radius=sound_slider_height // 2)
        
        # Draw filled portion of sound slider
        sound_filled_width = int((SETTINGS['sound_volume']) * sound_slider_width)
        if sound_filled_width > 0:
            pygame.draw.rect(screen, CYAN, 
                            (sound_slider_x, sound_slider_y - sound_slider_height // 2, sound_filled_width, sound_slider_height),
                            border_radius=sound_slider_height // 2)
        
        # Draw sound slider knob with glow effect
        for offset in range(5, 0, -1):
            alpha = int(150 * (offset / 5))
            pygame.draw.circle(screen, (*CYAN[:3], alpha), 
                              (int(sound_slider_knob_x), sound_slider_y), 
                              sound_slider_knob_radius + offset)
        pygame.draw.circle(screen, WHITE, (int(sound_slider_knob_x), sound_slider_y), sound_slider_knob_radius - 2)
        
        # Draw sound pack text and buttons
        screen.blit(sound_pack_text, sound_pack_rect)
        
        # Draw sound pack buttons
        for pack_id, button in sound_pack_buttons:
            button.update(dt)
            button.draw(screen)
            
        # Draw back button
        back_button.update(dt)
        back_button.draw(screen)
        
        pygame.display.flip()
    
    return "menu"

def run_startup_animation(screen, font, music_manager=None):
    """Display a professional startup animation before the main menu"""
    # Create a gradient background
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        # Create a smooth gradient from deep blue to purple
        r = int(20 + (y / SCREEN_HEIGHT) * 40)  # 20-60
        g = int(20 + (y / SCREEN_HEIGHT) * 10)  # 20-30
        b = int(60 + (y / SCREEN_HEIGHT) * 40)  # 60-100
        pygame.draw.line(background, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # Play startup music if available, otherwise play a sound effect
    if music_manager:
        # Temporarily stop any playing music
        pygame.mixer.music.stop()
        
        # Try to play startup music first
        if not music_manager.play_startup_music():
            # If no startup music available, play a sound effect instead
            music_manager.play_sound('level_up')
    
    # Define colors for the tetromino pieces with enhanced glow effect
    tetromino_colors = [
        (0, 234, 255),    # Cyan - Brighter
        (255, 236, 39),   # Yellow - Brighter
        (255, 64, 255),   # Magenta - Brighter
        (41, 121, 255),   # Blue - Brighter
        (255, 121, 0),    # Orange - Brighter
        (0, 255, 170),    # Green - Brighter
        (255, 41, 117)    # Red/Pink - Brighter
    ]
    
    # Define tetromino shapes with rotations
    tetromino_shapes = [
        [SHAPES[0]],  # I - only one rotation for simplicity
        [SHAPES[1]],  # O - only one rotation for simplicity
        [SHAPES[2]],  # T - only one rotation for simplicity
        [SHAPES[3]],  # J - only one rotation for simplicity
        [SHAPES[4]],  # L - only one rotation for simplicity
        [SHAPES[5]],  # S - only one rotation for simplicity
        [SHAPES[6]]   # Z - only one rotation for simplicity
    ]
    
    # Create more Tetris pieces for a richer animation
    tetris_pieces = []
    for i in range(20):  # Doubled the number of pieces
        piece_type = random.randint(0, 6)  # 7 different Tetris pieces
        tetris_pieces.append({
            'type': piece_type,
            'color': tetromino_colors[piece_type],
            'x': random.randint(0, SCREEN_WIDTH - 50),
            'y': -100 - random.randint(0, 800),  # Start above the screen, more spread out
            'rotation': 0,  # Only using one rotation for simplicity
            'speed': random.uniform(1.5, 4),  # Slightly slower for better visual
            'scale': random.uniform(0.8, 1.2),  # Add some size variation
            'alpha': random.randint(180, 255)  # Add some transparency variation
        })
    
    # Create particle effects
    particles = []
    for i in range(100):
        particles.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'size': random.randint(1, 3),
            'color': random.choice([(0, 234, 255), (255, 64, 255), (0, 255, 170), (255, 236, 39)]),
            'speed': random.uniform(0.2, 1.0)
        })
    
    # Text to display with enhanced styling
    texts = [
        {'text': 'GeTrix', 'size': 140, 'color': (0, 234, 255), 'pos': (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100), 'alpha': 0, 'glow': True, 'pulse': False},
        {'text': 'Swipe, Stack, and Score!', 'size': 42, 'color': (255, 255, 255), 'pos': (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30), 'alpha': 0, 'glow': False, 'pulse': False},
        {'text': 'Developed by ToGGy', 'size': 36, 'color': (255, 255, 255), 'pos': (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90), 'alpha': 0, 'glow': False, 'pulse': False},
        {'text': '© 2025 All Rights Reserved', 'size': 24, 'color': (200, 200, 200), 'pos': (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 140), 'alpha': 0, 'glow': False, 'pulse': False},
        {'text': 'Press any key to continue', 'size': 28, 'color': (255, 255, 255), 'pos': (SCREEN_WIDTH//2, SCREEN_HEIGHT - 80), 'alpha': 0, 'glow': False, 'pulse': True}
    ]
    
    # Animation timing - initial fade-in only, then wait for player input
    start_time = pygame.time.get_ticks()
    fade_in_duration = 3000  # 3 seconds for text fade in
    min_display_time = 3000  # Minimum time to display before allowing skip
    
    # Create a clock for controlling frame rate
    clock = pygame.time.Clock()
    
    # Animation loop
    running = True
    clock_time = 0
    fade_complete = False
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        clock_time += dt
        
        current_time = pygame.time.get_ticks() - start_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Only allow skipping after minimum display time
            elif current_time > min_display_time:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
        
        # Draw background
        screen.blit(background, (0, 0))
        
        # Draw particles first (behind everything)
        for particle in particles:
            # Move particles upward slowly
            particle['y'] -= particle['speed']
            if particle['y'] < 0:
                particle['y'] = SCREEN_HEIGHT
                particle['x'] = random.randint(0, SCREEN_WIDTH)
            
            # Draw the particle
            pygame.draw.circle(screen, particle['color'], (int(particle['x']), int(particle['y'])), particle['size'])
        
        # Update and draw falling Tetris pieces
        for piece in tetris_pieces:
            piece['y'] += piece['speed']
            if piece['y'] > SCREEN_HEIGHT:
                # Reset piece to top when it falls off the bottom
                piece['y'] = -50
                piece['x'] = random.randint(0, SCREEN_WIDTH - 50)
            
            # Draw the Tetris piece with scaling and alpha
            shape = tetromino_shapes[piece['type']][piece['rotation']]
            block_size = int(20 * piece.get('scale', 1.0))
            
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        # Create a surface for this block with alpha
                        block_surface = pygame.Surface((block_size, block_size))
                        block_surface.set_alpha(piece.get('alpha', 255))
                        block_surface.fill(piece['color'])
                        
                        # Draw block with glow effect
                        rect = pygame.Rect(0, 0, block_size, block_size)
                        pygame.draw.rect(block_surface, piece['color'], rect)
                        pygame.draw.rect(block_surface, (255, 255, 255), rect, 1)  # White border
                        
                        # Position and draw the block
                        pos_x = int(piece['x'] + x * block_size)
                        pos_y = int(piece['y'] + y * block_size)
                        screen.blit(block_surface, (pos_x, pos_y))
        
        # Update and draw text with enhanced effects
        for i, text_info in enumerate(texts):
            # Calculate alpha based on progress
            text_progress = max(0, min(1.0, (current_time - (i * 500)) / fade_in_duration))
            text_info['alpha'] = int(255 * text_progress)
            
            # Create text surface with current alpha
            # Use a bold font for the title
            if text_info['text'] == 'GeTrix':
                # Use a more detailed font for the title if available
                try:
                    # Try to use a more stylized font if available
                    text_font = pygame.font.SysFont('impact', text_info['size'])
                except:
                    # Fall back to default font
                    text_font = pygame.font.Font(None, text_info['size'])
            else:
                text_font = pygame.font.Font(None, text_info['size'])
            
            # Apply pulse effect if enabled
            if text_info.get('pulse', False) and text_info['alpha'] > 0:
                pulse_factor = 0.2 * math.sin(clock_time * 5) + 1.0  # Pulsing between 0.8 and 1.2 times the original size
                pulse_size = int(text_info['size'] * pulse_factor)
                if text_info['text'] == 'GeTrix':
                    try:
                        text_font = pygame.font.SysFont('impact', pulse_size)
                    except:
                        text_font = pygame.font.Font(None, pulse_size)
                else:
                    text_font = pygame.font.Font(None, pulse_size)
            
            # Add shadow effect for the title
            if text_info['text'] == 'GeTrix':
                # Create shadow surface
                shadow_offset = 4  # Shadow offset in pixels
                shadow_color = (0, 100, 150)  # Dark blue shadow
                shadow_surface = text_font.render(text_info['text'], True, shadow_color)
                shadow_surface.set_alpha(text_info['alpha'])
                
                # Position shadow with offset
                shadow_rect = shadow_surface.get_rect(center=(text_info['pos'][0] + shadow_offset, text_info['pos'][1] + shadow_offset))
                screen.blit(shadow_surface, shadow_rect)
                
                # Create outline effect (multiple shadows in different directions)
                outline_color = (0, 150, 200)  # Slightly lighter blue for outline
                for offset_x, offset_y in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                    outline_surface = text_font.render(text_info['text'], True, outline_color)
                    outline_surface.set_alpha(int(text_info['alpha'] * 0.7))
                    outline_rect = outline_surface.get_rect(center=(text_info['pos'][0] + offset_x, text_info['pos'][1] + offset_y))
                    screen.blit(outline_surface, outline_rect)
            
            # Render the text
            text_surface = text_font.render(text_info['text'], True, text_info['color'])
            
            # Apply glow effect if enabled
            if text_info.get('glow', False) and text_info['alpha'] > 0:
                # Create a slightly larger glow surface for more intense glow
                glow_size = text_info['size'] + 8  # Increased glow size
                if text_info['text'] == 'GeTrix':
                    try:
                        glow_font = pygame.font.SysFont('impact', glow_size)
                    except:
                        glow_font = pygame.font.Font(None, glow_size)
                else:
                    glow_font = pygame.font.Font(None, glow_size)
                    
                # Create multiple glow layers for a more intense effect
                glow_colors = [(100, 200, 255), (50, 150, 255), (0, 100, 255)]
                for idx, glow_color in enumerate(glow_colors):
                    glow_surface = glow_font.render(text_info['text'], True, glow_color)
                    glow_surface.set_alpha(int(text_info['alpha'] * (0.7 - idx * 0.2)))
                    
                    # Position glow slightly offset
                    glow_rect = glow_surface.get_rect(center=text_info['pos'])
                    screen.blit(glow_surface, glow_rect)
            
            # Set alpha for main text surface
            text_surface.set_alpha(text_info['alpha'])
            
            # Position and draw the text
            text_rect = text_surface.get_rect(center=text_info['pos'])
            screen.blit(text_surface, text_rect)
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
        
        # Exit animation only when all text is fully visible
        if texts[-1]['alpha'] >= 250:
            # All text is fully visible, now just waiting for user input
            pass
    
    # Restart menu music
    if music_manager:
        music_manager.play_music_for_mode('menu')
    
    # Return to menu state
    return "menu"

def main():
    SCREEN_WIDTH = 800  # Reset to 800 for two-player support
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Load settings
    load_settings()
    
    # Initialize the music manager
    music_manager = MusicManager()
    
    # Apply volume settings
    music_manager.set_volume(SETTINGS['music_volume'])
    music_manager.set_sound_volume(SETTINGS['sound_volume'])
    
    # Load sound effects
    music_manager.load_sound_effects()
    
    # Start with menu music
    music_manager.play_music_for_mode('menu')
    pygame.display.set_caption("Tetris")
    
    # Set up the font
    font = pygame.font.Font(None, 36)
    
    # Game state machine
    clock = pygame.time.Clock()
    current_state = "startup"  # Start with the startup animation
    
    while current_state is not None:
        if current_state == "startup":
            current_state = run_startup_animation(screen, font, music_manager)
        elif current_state == "menu":
            current_state = run_menu(screen, font, music_manager)
        elif current_state == "single":
            current_state = run_single_player(screen, font, music_manager)
        elif current_state == "dual":
            current_state = run_two_player(screen, font, False, music_manager)
        elif current_state == "crazy":
            current_state = run_crazy_mode(screen, font, music_manager, False)
        elif current_state == "gesture":
            current_state = run_gesture_mode(screen, font, music_manager)
        elif current_state == "settings":
            current_state = run_settings_menu(screen, font, music_manager)
        elif current_state == "overdrive_menu":
            current_state = run_overdrive_menu(screen, font, music_manager)
        elif current_state == "crazy_gestures":
            current_state = run_crazy_mode(screen, font, music_manager, True)
        
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
