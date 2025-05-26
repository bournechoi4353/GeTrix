import cv2
import time

def check_cameras():
    print("Checking available cameras...")
    for i in range(3):  # Check first 3 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera {i} is available")
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"  Resolution: {width}x{height}")
            print(f"  FPS: {fps}")
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret:
                print(f"  Successfully read a frame of size {frame.shape}")
                # Show the frame briefly
                cv2.namedWindow(f"Camera {i}", cv2.WINDOW_NORMAL)
                cv2.imshow(f"Camera {i}", frame)
                cv2.waitKey(1000)  # Display for 1 second
                cv2.destroyWindow(f"Camera {i}")
            else:
                print("  Failed to read a frame")
        else:
            print(f"Camera {i} is not available")
        cap.release()
    
    cv2.destroyAllWindows()
    print("Camera check complete")

if __name__ == "__main__":
    print(f"OpenCV version: {cv2.__version__}")
    check_cameras()
