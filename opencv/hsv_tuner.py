import cv2
import numpy as np

def nothing(x):
    """Callback function for trackbars. Does nothing."""
    pass

def create_hsv_tuner():
    """
    Creates a window with trackbars to tune HSV values for color segmentation.
    Uses the webcam as video source.
    """
    # Open the default camera
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    # Create a window to display the trackbars
    cv2.namedWindow('Trackbars')
    cv2.resizeWindow('Trackbars', 640, 240)

    # Create trackbars for H, S, V ranges
    # Hue (0-179), Saturation (0-255), Value (0-255)
    cv2.createTrackbar('H_min', 'Trackbars', 0, 179, nothing)
    cv2.createTrackbar('H_max', 'Trackbars', 179, 179, nothing)
    cv2.createTrackbar('S_min', 'Trackbars', 0, 255, nothing)
    cv2.createTrackbar('S_max', 'Trackbars', 255, 255, nothing)
    cv2.createTrackbar('V_min', 'Trackbars', 0, 255, nothing)
    cv2.createTrackbar('V_max', 'Trackbars', 255, 255, nothing)

    print("\nHSV Tuner started.")
    print("Adjust the sliders to find the desired color range.")
    print("Press 's' to print the current threshold in a copy-paste format.")
    print("Press 'q' to quit.")

    while True:
        # Read a frame from the camera
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break

        # Convert the frame from BGR to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get current trackbar positions
        h_min = cv2.getTrackbarPos('H_min', 'Trackbars')
        h_max = cv2.getTrackbarPos('H_max', 'Trackbars')
        s_min = cv2.getTrackbarPos('S_min', 'Trackbars')
        s_max = cv2.getTrackbarPos('S_max', 'Trackbars')
        v_min = cv2.getTrackbarPos('V_min', 'Trackbars')
        v_max = cv2.getTrackbarPos('V_max', 'Trackbars')

        # Define the lower and upper bounds of the HSV threshold
        lower_bound = np.array([h_min, s_min, v_min])
        upper_bound = np.array([h_max, s_max, v_max])
        
        # Print the current threshold values
        print(f"lower: ({h_min}, {s_min}, {v_min}), upper: ({h_max}, {s_max}, {v_max})          ", end='\r')


        # Create a mask using the inRange function
        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)

        # Apply the mask to the original frame to see the result
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Display the original frame, the mask, and the result
        cv2.imshow('Original Frame', frame)
        cv2.imshow('Mask', mask)
        cv2.imshow('Result', result)

        # Exit the loop when 'q' is pressed
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("\n\n--- Copy-paste this line ---")
            print(f"hsv_threshold = ({h_min}, {s_min}, {v_min}, {h_max}, {s_max}, {v_max})")
            print("----------------------------\n")

    # Release the camera and destroy all windows
    cap.release()
    cv2.destroyAllWindows()
    print("\nHSV Tuner closed.")


if __name__ == "__main__":
    create_hsv_tuner() 