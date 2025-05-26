# Store Images

This directory is for storing store-related images for the Dual Tetris game.

## Recommended Image Specifications

- **Format**: PNG with transparency
- **Size**: 100x100 pixels for store items
- **Style**: Match the cyberpunk aesthetic of the game

## Naming Convention

- `item_[name].png` - Store items (e.g., `item_booster.png`)
- `skin_[name].png` - Tetromino skins (e.g., `skin_neon.png`)
- `icon_[name].png` - UI icons (e.g., `icon_coins.png`)

## Usage in Code

To use a store image in the game:

```python
# Load a store item image
item_image = load_image("item_booster.png", subfolder="store")

# Load a skin preview
skin_image = load_image("skin_neon.png", subfolder="store")

# Display the image
screen.blit(item_image, (x, y))
```

## Creating Custom Store Images

1. Create your image with a transparent background
2. Use the recommended size
3. Save in PNG format
4. Place in this directory
5. Use the naming convention for different types

The game will automatically load your custom store images if they exist.
