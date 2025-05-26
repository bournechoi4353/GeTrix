# Button Images

This directory contains button images for the Dual Tetris game, organized by button type.

## Subfolders

- `/standard/` - Standard mode button images
- `/duel/` - Duel mode button images
- `/gesture/` - Gesture mode button images
- `/controls/` - Controls button images

## Recommended Image Specifications

- **Format**: PNG with transparency
- **Size**: 200x200 pixels (will be scaled to fit the button)
- **States**: Normal, Hover, Pressed

## Naming Convention

- `button_normal.png` - Default state
- `button_hover.png` - Hover state
- `button_pressed.png` - Pressed state

## Button Shapes

Each button type has a specific shape:

- **Standard Mode**: Hexagon shape with cyan glow
- **Duel Mode**: Diamond shape with magenta glow
- **Gesture Mode**: Controller shape with yellow glow
- **Controls**: Controller shape with yellow glow

## Creating Custom Button Images

1. Create your image with a transparent background
2. Use the recommended size (200x200 pixels)
3. Save in PNG format
4. Place in the appropriate subfolder
5. Use the naming convention for different states

The game will automatically load your custom images if they exist, or fall back to the drawn shapes if they don't.
