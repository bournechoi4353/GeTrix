import json
import os

# Default colors for Tetris blocks (I, J, L, O, S, T, Z)
DEFAULT_COLORS = [
    (0, 255, 255),  # Cyan (I)
    (0, 0, 255),    # Blue (J)
    (255, 165, 0),  # Orange (L)
    (255, 255, 0),  # Yellow (O)
    (0, 255, 0),    # Green (S)
    (128, 0, 128),  # Purple (T)
    (255, 0, 0)     # Red (Z)
]

# Default store data
DEFAULT_STORE_DATA = {
    "line_chips": 0,
    "owned_skins": ["default"],
    "active_skin": "default",
    "available_skins": {
        "default": {
            "name": "Default",
            "type": "basic",
            "price": 0,
            "description": "The classic Tetris blocks",
            "owned": True,
            "colors": DEFAULT_COLORS
        },
        "glossy": {
            "name": "Glossy",
            "type": "basic",
            "price": 15,
            "description": "Shiny, reflective blocks",
            "owned": False,
            "colors": [
                (100, 255, 255),  # Lighter Cyan
                (100, 100, 255),  # Lighter Blue
                (255, 200, 100),  # Lighter Orange
                (255, 255, 100),  # Lighter Yellow
                (100, 255, 100),  # Lighter Green
                (200, 100, 200),  # Lighter Purple
                (255, 100, 100)   # Lighter Red
            ]
        },
        "matte": {
            "name": "Matte",
            "type": "basic",
            "price": 15,
            "description": "Smooth, non-reflective blocks",
            "owned": False,
            "colors": [
                (0, 200, 200),    # Darker Cyan
                (0, 0, 200),      # Darker Blue
                (200, 120, 0),    # Darker Orange
                (200, 200, 0),    # Darker Yellow
                (0, 200, 0),      # Darker Green
                (100, 0, 100),    # Darker Purple
                (200, 0, 0)       # Darker Red
            ]
        },
        "neon": {
            "name": "Neon",
            "type": "basic",
            "price": 15,
            "description": "Bright, glowing blocks",
            "owned": False,
            "colors": [
                (0, 255, 255),    # Neon Cyan
                (80, 80, 255),    # Neon Blue
                (255, 180, 0),    # Neon Orange
                (255, 255, 0),    # Neon Yellow
                (0, 255, 80),     # Neon Green
                (255, 0, 255),    # Neon Purple
                (255, 0, 80)      # Neon Red
            ]
        },
        "retro": {
            "name": "Retro",
            "type": "basic",
            "price": 15,
            "description": "Old-school pixelated blocks",
            "owned": False,
            "colors": [
                (0, 170, 170),    # Retro Cyan
                (0, 0, 170),      # Retro Blue
                (170, 85, 0),     # Retro Orange
                (170, 170, 0),    # Retro Yellow
                (0, 170, 0),      # Retro Green
                (170, 0, 170),    # Retro Purple
                (170, 0, 0)       # Retro Red
            ]
        },
        "gradient": {
            "name": "Gradient",
            "type": "special",
            "price": 30,
            "description": "Blocks with smooth gradient effect",
            "owned": True,
            "effect": "gradient",
            "colors": [
                (0, 255, 255),    # Cyan base for gradient
                (0, 0, 255),      # Blue base for gradient
                (255, 165, 0),    # Orange base for gradient
                (255, 255, 0),    # Yellow base for gradient
                (0, 255, 0),      # Green base for gradient
                (128, 0, 128),    # Purple base for gradient
                (255, 0, 0)       # Red base for gradient
            ]
        },
        "sparkle": {
            "name": "Sparkle",
            "type": "special",
            "price": 30,
            "description": "Blocks with sparkling effect",
            "owned": False,
            "effect": "sparkle",
            "colors": [
                (0, 200, 200),    # Slightly darker for better sparkle contrast
                (0, 0, 200),      # Slightly darker for better sparkle contrast
                (200, 130, 0),    # Slightly darker for better sparkle contrast
                (200, 200, 0),    # Slightly darker for better sparkle contrast
                (0, 200, 0),      # Slightly darker for better sparkle contrast
                (100, 0, 100),    # Slightly darker for better sparkle contrast
                (200, 0, 0)       # Slightly darker for better sparkle contrast
            ]
        },
        "pastel": {
            "name": "Pastel",
            "type": "special",
            "price": 30,
            "description": "Soft pastel colored blocks",
            "owned": False,
            "effect": "gradient",
            "colors": [
                (173, 216, 230),  # Light Blue
                (173, 216, 255),  # Light Sky Blue
                (255, 218, 185),  # Peach
                (255, 255, 224),  # Light Yellow
                (144, 238, 144),  # Light Green
                (221, 160, 221),  # Plum
                (255, 182, 193)   # Light Pink
            ]
        },
        "metallic": {
            "name": "Metallic",
            "type": "special",
            "price": 30,
            "description": "Shiny metallic blocks",
            "owned": False,
            "effect": "gradient",
            "colors": [
                (176, 196, 222),  # Light Steel Blue
                (70, 130, 180),   # Steel Blue
                (184, 134, 11),   # Dark Goldenrod
                (218, 165, 32),   # Goldenrod
                (46, 139, 87),    # Sea Green
                (139, 0, 139),    # Dark Magenta
                (178, 34, 34)     # Firebrick
            ]
        }
    }
}

# File path for store data
STORE_DATA_FILE = "tetris_store_data.json"

def load_store_data():
    """Load store data from file or create default if it doesn't exist"""
    if os.path.exists(STORE_DATA_FILE):
        try:
            with open(STORE_DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, use default
            return DEFAULT_STORE_DATA.copy()
    else:
        # Create new file with default data
        save_store_data(DEFAULT_STORE_DATA)
        return DEFAULT_STORE_DATA.copy()

def save_store_data(data):
    """Save store data to file"""
    with open(STORE_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_line_chips(amount):
    """Add LineChips to the player's account"""
    data = load_store_data()
    data["line_chips"] += amount
    save_store_data(data)
    return data["line_chips"]

def purchase_skin(skin_id):
    """Attempt to purchase a skin"""
    data = load_store_data()
    
    # Check if skin exists
    if skin_id not in data["available_skins"]:
        return False, "Skin not found"
    
    skin = data["available_skins"][skin_id]
    
    # Check if already owned
    if skin["owned"]:
        return False, "Already owned"
    
    # Check if enough LineChips
    if data["line_chips"] < skin["price"]:
        return False, f"Not enough LineChips. Need {skin['price']}, have {data['line_chips']}"
    
    # Purchase the skin
    data["line_chips"] -= skin["price"]
    skin["owned"] = True
    data["owned_skins"].append(skin_id)
    save_store_data(data)
    
    return True, f"Successfully purchased {skin['name']}!"

def set_active_skin(skin_id):
    """Set the active skin"""
    data = load_store_data()
    
    # Check if skin exists
    if skin_id not in data["available_skins"]:
        return False, "Skin not found"
    
    # Check if owned
    if not data["available_skins"][skin_id]["owned"]:
        return False, "You don't own this skin"
    
    # Set as active
    data["active_skin"] = skin_id
    save_store_data(data)
    
    return True, f"Set {data['available_skins'][skin_id]['name']} as active skin"

def get_active_skin():
    """Get the currently active skin"""
    data = load_store_data()
    return data["active_skin"]

def get_line_chips():
    """Get the current number of LineChips"""
    data = load_store_data()
    return data["line_chips"]
