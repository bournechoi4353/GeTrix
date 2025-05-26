# GeTrix - Gesture-Controlled Tetris

A Tetris game implementation in Python using Pygame, featuring both standard controls and innovative camera-based gesture controls. Play with keyboard or control the game with hand gestures!

## Features

- Menu system with multiple game mode selection
- Single-player classic Tetris
- Two-player simultaneous Tetris
- Gesture control support using webcam
- Score tracking and levels
- Difficulty increases over time
- Next piece preview
- Game over detection
- Custom sound packs and music manager

## Requirements

- Python 3.7+
- Pygame
- OpenCV (for camera input)
- MediaPipe (for hand tracking)
- NumPy

## Installation

```bash
# Install required packages
pip install -r requirements.txt

# Check if your camera is working
python check_camera.py
```

## How to Play

Run the game:

```bash
python dual_tetris.py
# Or for gesture controls:
python GeTrix.py
```

### Keyboard Controls

#### Single Player Mode
- Left/Right arrows: Move piece left/right
- Down arrow: Move piece down
- Up arrow: Rotate piece
- Space: Hard drop
- R: Reset game
- ESC: Return to menu

#### Two Player Mode
Left Player:
- A/D: Move piece left/right
- S: Move piece down
- W: Rotate piece
- Q: Hard drop

Right Player:
- Left/Right arrows: Move piece left/right
- Down arrow: Move piece down
- Up arrow: Rotate piece
- Space: Hard drop

Shared Controls:
- R: Reset both games
- ESC: Return to menu

### Gesture Controls

Requires a webcam to detect hand gestures:

- Thumb extended left: Rotate piece
- Index finger up: Move piece left
- Middle finger up: Move piece right
- Ring finger up: Move piece down
- All fingers closed: Hard drop

## Troubleshooting

If you encounter camera issues:
1. Run `python check_camera.py` to verify your camera works
2. Ensure proper lighting for better hand detection
3. Position your hand within frame of the camera

## Building Executables

For macOS:
```bash
python create_mac_package.py
```

For Windows:
```bash
python create_windows_package.py
```

