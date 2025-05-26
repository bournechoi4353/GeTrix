# Dual Tetris Assets Directory

This directory contains assets for the Dual Tetris game.

## Structure

- `/images/` - Contains image files for the game
  - Button images (PNG format recommended)
  - Logo images
  - Background images
  - UI elements

## Image Guidelines

### Button Images
- Recommended size: 200x200 pixels
- Transparent background (PNG)
- Name format: `button_[type]_[state].png`
  - Example: `button_standard_normal.png`, `button_standard_hover.png`

### Logo Images
- Recommended size: 400x200 pixels
- Transparent background (PNG)
- Name format: `logo_[variant].png`
  - Example: `logo_main.png`, `logo_small.png`

## How to Use

1. Place your image files in the appropriate directory
2. The game will automatically load the images if they exist
3. If an image is not found, the game will fall back to the default drawn shapes

## Supported Image Formats

- PNG (recommended for transparency)
- JPG
- BMP
- GIF (static only)
