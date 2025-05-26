# Dual Tetris Images Directory

This directory contains image assets for the Dual Tetris game, organized into subfolders by type.

## Directory Structure

- `/buttons/` - Button images
  - `/buttons/standard/` - Standard mode button images
  - `/buttons/duel/` - Duel mode button images
  - `/buttons/gesture/` - Gesture mode button images
  - `/buttons/controls/` - Controls button images
- `/logo/` - Game logo images
- `/store/` - Store item images

## Naming Conventions

### Button Images
- `button_normal.png` - Default state
- `button_hover.png` - Hover state
- `button_pressed.png` - Pressed state

### Logo Images
- `logo_main.png` - Main game logo
- `logo_small.png` - Smaller version for UI elements

### Store Images
- `item_[name].png` - Store items
- `skin_[name].png` - Tetromino skins

## Image Specifications

- All images should use transparent backgrounds (PNG format)
- Recommended button size: 200x200 pixels
- Recommended logo size: 400x200 pixels
- Store items: 100x100 pixels

## Usage in Code

Images are automatically loaded from the appropriate subfolder based on the button type:

```python
# Example: Create a button with a custom image
button = Button(x, y, width, height, "Standard", font, image_name="button_normal.png")

# Explicitly specify a subfolder
button = Button(x, y, width, height, "Custom", font, 
                image_name="custom.png", image_subfolder="buttons/custom")
```
