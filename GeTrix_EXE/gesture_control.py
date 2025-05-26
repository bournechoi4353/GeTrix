import cv2
import mediapipe as mp
import numpy as np
import time
import cv2
import os
import sys

# Import mock camera if available
try:
    from mock_camera import MockCamera
    MOCK_CAMERA_AVAILABLE = True
except ImportError:
    MOCK_CAMERA_AVAILABLE = False

class GestureController:
    def __init__(self, show_camera_window=True):
        self.show_camera_window = show_camera_window
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,  # Lowered for better detection
            min_tracking_confidence=0.5    # Lowered for better tracking
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Try to initialize camera with better error handling
        self.cap = None
        self.using_mock_camera = False
        
        try:
            print("Attempting to initialize camera...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open camera 0. Trying alternative method...")
                # Try alternative camera index
                self.cap = cv2.VideoCapture(1)
                if not self.cap.isOpened():
                    print("Error: Could not open any camera.")
                    
                    # Try to use mock camera if available
                    if MOCK_CAMERA_AVAILABLE:
                        print("Using mock camera instead...")
                        self.cap = MockCamera(width=640, height=480)
                        self.using_mock_camera = True
                    else:
                        self.cap = None
        except Exception as e:
            print(f"Camera initialization error: {e}")
            # Try to use mock camera if available
            if MOCK_CAMERA_AVAILABLE:
                print("Using mock camera instead...")
                self.cap = MockCamera(width=640, height=480)
                self.using_mock_camera = True
            else:
                self.cap = None
            
        # Set camera status flag
        self.camera_available = self.cap is not None and self.cap.isOpened()
        print(f"Camera available: {self.camera_available} (Mock: {self.using_mock_camera})")
            
        # Set camera properties for better performance
        if self.cap and self.cap.isOpened():
            # Get the actual camera resolution
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Camera resolution: {width}x{height}")
            
            # Set to 640x480 for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Verify the settings were applied
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            print(f"Camera settings applied: {actual_width}x{actual_height} @ {actual_fps}fps")
        
        # Finger indices in MediaPipe hand model
        self.THUMB_TIP = 4
        self.INDEX_TIP = 8
        self.MIDDLE_TIP = 12
        self.RING_TIP = 16
        self.PINKY_TIP = 20
        
        # Base of palm
        self.WRIST = 0
        
        # Gesture state tracking
        self.last_gesture_time = time.time()
        self.last_frame_time = time.time()
        self.gesture_cooldown = 0.2  # seconds - reduced for better responsiveness
        
        # Create a named window for the camera feed if show_camera_window is True
        if show_camera_window:
            cv2.namedWindow('Gesture Detection', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Gesture Detection', 640, 480)
        
        # Finger state tracking
        self.thumb_up_prev = False
        self.index_up_prev = False
        self.middle_up_prev = False
        self.ring_up_prev = False
        self.pinky_up_prev = False
        
        # Rotation state tracking (to ensure rotate only happens once per thumb gesture)
        self.thumb_rotate_used = False
        
        # Initialize display window if show_camera_window is True
        if show_camera_window:
            cv2.namedWindow('Gesture Detection', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Gesture Detection', 640, 480)

    def is_finger_up(self, hand_landmarks, finger_tip_idx, finger_pip_idx):
        """Check if a finger is extended upward"""
        tip = hand_landmarks.landmark[finger_tip_idx]
        pip = hand_landmarks.landmark[finger_pip_idx]  # Proximal interphalangeal joint (middle knuckle)
        
        # For most fingers, if tip is higher (lower y) than pip, finger is up
        return tip.y < pip.y
    
    def is_thumb_up(self, hand_landmarks):
        """Special case for thumb which moves differently"""
        thumb_tip = hand_landmarks.landmark[self.THUMB_TIP]
        thumb_mcp = hand_landmarks.landmark[2]  # Metacarpophalangeal joint
        wrist = hand_landmarks.landmark[self.WRIST]
        
        # Check if thumb is extended to the side with a tolerance margin
        # Adding a tolerance of 0.03 to make it less sensitive
        return thumb_tip.x < (thumb_mcp.x - 0.03)

    def detect_gesture(self):
        # Check if camera is available
        if not self.camera_available:
            # Don't print this every frame to avoid console spam
            return None
            
        try:
            success, image = self.cap.read()
            if not success:
                print("Failed to read frame from camera")
                return None
        except Exception as e:
            print(f"Error reading from camera: {e}")
            return None

        # Flip the image horizontally for a selfie-view display
        image = cv2.flip(image, 1)
        
        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect hands
        try:
            results = self.hands.process(image_rgb)
            print("MediaPipe hand detection processed successfully")
        except Exception as e:
            print(f"Error in MediaPipe hand detection: {e}")
            return None
        
        gesture = None
        current_time = time.time()
        
        # Calculate FPS
        fps = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
        self.last_frame_time = current_time
        
        # Get image dimensions
        h, w, _ = image.shape
        
        # Draw FPS counter
        cv2.putText(image, f"FPS: {fps:.1f}", (w - 150, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw cooldown indicator
        cooldown_remaining = max(0, self.gesture_cooldown - (current_time - self.last_gesture_time))
        cooldown_color = (0, 0, 255) if cooldown_remaining > 0 else (0, 255, 0)
        cv2.putText(image, f"Cooldown: {cooldown_remaining:.2f}s", (w - 220, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, cooldown_color, 2)
        
        # Check if we can process a new gesture (cooldown expired)
        can_process_gesture = current_time - self.last_gesture_time > self.gesture_cooldown
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]  # Get first hand
            
            # Draw hand landmarks
            self.mp_draw.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Check finger states
            thumb_up = self.is_thumb_up(hand_landmarks)
            index_up = self.is_finger_up(hand_landmarks, self.INDEX_TIP, 6)
            middle_up = self.is_finger_up(hand_landmarks, self.MIDDLE_TIP, 10)
            ring_up = self.is_finger_up(hand_landmarks, self.RING_TIP, 14)
            pinky_up = self.is_finger_up(hand_landmarks, self.PINKY_TIP, 18)
            
            # Add finger state labels to image with colors
            finger_states = [
                ("Thumb", thumb_up),
                ("Index", index_up),
                ("Middle", middle_up),
                ("Ring", ring_up),
                ("Pinky", pinky_up)
            ]
            
            for i, (finger, is_up) in enumerate(finger_states):
                state_text = f"{finger}: {'UP' if is_up else 'DOWN'}"
                color = (0, 255, 0) if is_up else (0, 0, 255)  # Green for UP, Red for DOWN
                cv2.putText(image, state_text, (10, 30 + i * 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # SIMPLIFIED GESTURE DETECTION
            if can_process_gesture:
                # Left: Index finger up only
                if index_up and not middle_up and not ring_up and not pinky_up:
                    gesture = "left"
                    cv2.putText(image, "LEFT", (w//2 - 50, h//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                    self.last_gesture_time = current_time
                
                # Right: Pinky finger up only
                elif pinky_up and not index_up and not middle_up and not ring_up:
                    gesture = "right"
                    cv2.putText(image, "RIGHT", (w//2 - 50, h//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                    self.last_gesture_time = current_time
                
                # Down: Middle finger up only
                elif middle_up and not index_up and not ring_up and not pinky_up:
                    gesture = "down"
                    cv2.putText(image, "DOWN", (w//2 - 50, h//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                    self.last_gesture_time = current_time
                
                # Rotate: Thumb up only
                elif thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
                    if not self.thumb_up_prev:  # Only trigger if thumb just went up
                        gesture = "rotate"
                        cv2.putText(image, "ROTATE", (w//2 - 70, h//2), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                        self.last_gesture_time = current_time
                
                # Hard drop: All fingers up
                elif thumb_up and index_up and middle_up and ring_up and pinky_up:
                    gesture = "hard_drop"
                    cv2.putText(image, "HARD DROP", (w//2 - 100, h//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                    self.last_gesture_time = current_time
            
            # Update previous states
            self.thumb_up_prev = thumb_up
            self.index_up_prev = index_up
            self.middle_up_prev = middle_up
            self.ring_up_prev = ring_up
            self.pinky_up_prev = pinky_up
        else:
            # No hand detected
            cv2.putText(image, "No Hand Detected", (w//2 - 120, h//2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        # Display the detected gesture at the bottom of the screen
        if gesture:
            cv2.putText(image, f"DETECTED: {gesture.upper()}", (10, h - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
            print(f"Gesture detected: {gesture}")
        
        # Display the image in a separate window if show_camera_window is True
        try:
            if self.show_camera_window:
                cv2.imshow('Gesture Detection', image)
                key = cv2.waitKey(1)  # Process window events
                if key == 27:  # ESC key
                    print("ESC key pressed in gesture window")
                    return "escape"  # Special signal to exit
        except Exception as e:
            print(f"Error displaying image: {e}")
            # Try to recreate the window if it failed and show_camera_window is True
            if self.show_camera_window:
                try:
                    cv2.destroyWindow('Gesture Detection')
                    cv2.namedWindow('Gesture Detection', cv2.WINDOW_NORMAL)
                    cv2.resizeWindow('Gesture Detection', 640, 480)
                    print("Recreated gesture window")
                except Exception as window_error:
                    print(f"Failed to recreate window: {window_error}")
        
        return gesture

    def cleanup(self):
        # Safely release camera resources
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
                print("Camera released successfully")
            
            # Close all OpenCV windows if show_camera_window was True
            if self.show_camera_window:
                cv2.destroyWindow('Gesture Detection')
                cv2.destroyAllWindows()
                print("All windows closed successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")

def get_gesture_instructions():
    return """
    Finger Controls:
    - Make a loose fist, and extend fingers to move pieces
    - Index finger: Move Left
    - Pinky finger: Move Right
    - Middle finger: Move Down
    - Thumb clearly to the side: Rotate
    - Open hand (most fingers up): Hard Drop
    - ESC: Return to menu
    
    Remember to face the palm of your RIGHT hand towards the camera
    """
