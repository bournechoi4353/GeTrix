# Logo Images

This directory is for storing logo images for the Dual Tetris game.

## Recommended Image Specifications

- **Format**: PNG with transparency
- **Size**: 400x200 pixels for main logo, 200x100 for smaller variants
- **Style**: Match the cyberpunk aesthetic of the game

## Naming Convention

- `logo_main.png` - Main game logo
- `logo_small.png` - Smaller version for UI elements
- `logo_title.png` - Title screen version

## Usage in Code

To use a logo in the game:

```python
# Load the main logo
logo_image = load_image("logo_main.png", subfolder="logo")

# Display the logo
screen.blit(logo_image, (x, y))
```

## Creating Custom Logo Images

1. Create your image with a transparent background
2. Use the recommended size
3. Save in PNG format
4. Place in this directory
5. Use the naming convention for different variants

The game will automatically load your custom logo if it exists.
