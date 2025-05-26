import cv2
import numpy as np
import time

class MockCamera:
    """A mock camera class that can be used when a real camera is not available"""
    
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.is_open = True
        self.frame_count = 0
        self.start_time = time.time()
        
        # Create a black background
        self.background = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add some text to the background
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(self.background, "Mock Camera", (width//2 - 100, height//2), 
                    font, 1, (255, 255, 255), 2)
        cv2.putText(self.background, "No real camera available", (width//2 - 150, height//2 + 40), 
                    font, 0.7, (200, 200, 200), 2)
        
        # Create a moving circle for visual feedback
        self.circle_pos = [width//2, height//2]
        self.circle_dir = [5, 3]
        self.circle_radius = 20
        self.circle_color = (0, 255, 255)  # Yellow
    
    def isOpened(self):
        return self.is_open
    
    def read(self):
        if not self.is_open:
            return False, None
        
        # Create a copy of the background
        frame = self.background.copy()
        
        # Update circle position
        self.circle_pos[0] += self.circle_dir[0]
        self.circle_pos[1] += self.circle_dir[1]
        
        # Bounce off edges
        if self.circle_pos[0] <= self.circle_radius or self.circle_pos[0] >= self.width - self.circle_radius:
            self.circle_dir[0] *= -1
        if self.circle_pos[1] <= self.circle_radius or self.circle_pos[1] >= self.height - self.circle_radius:
            self.circle_dir[1] *= -1
        
        # Draw the circle
        cv2.circle(frame, (self.circle_pos[0], self.circle_pos[1]), 
                   self.circle_radius, self.circle_color, -1)
        
        # Add frame counter and FPS
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        cv2.putText(frame, f"Frame: {self.frame_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return True, frame
    
    def get(self, prop_id):
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return self.width
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.height
        elif prop_id == cv2.CAP_PROP_FPS:
            return 30
        return 0
    
    def set(self, prop_id, value):
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            self.width = value
            return True
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            self.height = value
            return True
        return False
    
    def release(self):
        self.is_open = False
