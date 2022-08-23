import time
import cv2

def self_land(self):
    """Use the drone's ground camera to search for the landing marker. Once found, center the drone over the marker and land."""

    print("Self-landing function initiated. Drone now searching for a landing marker...")

    circle = False
    rect = False
    stop = False

    while not stop:

        # Keypress commands
        key = self.drone.getKey()

        if key == 'q':
            print("Quit button pressed. Landing the drone...")
            self.stop = True

        # Process the frame and get parameters
        frame = self.drone.VideoImage 
        frame = cv2.resize(frame, (400, 400))
        (h, w) = frame.shape[:2]
        frame_center = (w//2, h//2)

        # Find the contours within the frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), cv2.BORDER_DEFAULT)
        ret, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY_INV)
        contours, heirarchies = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for i in contours:
            M = cv2.moments(i)
            approx = cv2.approxPolyDP(i, 0.01 * cv2.arcLength(i, True), True)

            # Find contour center-points
            if M['m00'] != 0:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])

                # Find a circle (assumed to be 12-sided shape or higher)
                if len(approx) >= 12:
                    cntConvex = cv2.isContourConvex(approx)
                    if cntConvex:
                        cv2.drawContours(frame, [i], -1, (0, 0, 255), 2)
                        cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)
                        cx_circle = cx
                        cy_circle = cy
                        circle = True

                # Find curved corner rectangles (assumed to be between 7 and 10 sides)
                if len(approx) >= 7 and len(approx) < 10:
                    cntConvex = cv2.isContourConvex(approx)
                    if cntConvex:
                        cv2.drawContours(frame, [i], -1, (255, 0, 0), 2)
                        cv2.circle(frame, (cx, cy), 7, (255, 0, 0), -1)
                        cx_rect = cx
                        cy_rect = cy

            # Check the rectangle is positioned inside the circle (is it the specified marker)
            try:
                if cx_rect <= cx_circle + 20 and cx_rect > cx_circle:
                    if cy_rect <= cy_circle + 20 and cy_rect > cy_circle:
                        rect = True

                    elif cy_rect >= cy_circle - 20 and cy_rect < cy_circle:
                        rect = True

                    else:
                        rect = False

                elif cx_rect >= cx_circle - 20 and cx_rect < cx_circle:
                    if cy_rect <= cy_circle + 20 and cy_rect > cy_circle:
                        rect = True

                    elif cy_rect >= cy_circle - 20 and cy_rect < cy_circle:
                        rect = True

                    else:
                        rect = False

            except:
                rect = False

            # When a marker is visible in the camera frame, align drone with the marker's center-point
            if circle == True and rect == True:
                x_correct = False
                y_correct = False

                if frame_center[0] > cx_circle + 50:
                    print("Moving left...")
                    self.drone.moveLeft()
                    time.sleep(1)
                    self.drone.stop()

                elif frame_center[0] < cx_circle - 50:
                    print("Moving right...")
                    self.drone.moveRight()
                    time.sleep(1)
                    self.drone.stop()

                else:
                    x_correct = True

                if frame_center[1] > cy_circle + 50:
                    print("Moving forward...")
                    self.drone.moveForward()
                    time.sleep(1)
                    self.drone.stop()

                elif frame_center[1] < cy_circle - 50:
                    print("Moving backward...")
                    self.drone.moveBackward()
                    time.sleep(1)
                    self.drone.stop()

                else:
                    y_correct = True

                # Land the drone once center-points are aligned
                if x_correct == True and y_correct == True:
                    print("Landing the drone on the marker.")
                    stop = True
        
        # Show the video feed
        cv2.imshow("Drone's ground camera", frame)
        cv2.waitKey(1)

    # Land the drone and quit
    self.drone.land()
    print("Drone landed. Exiting program.")
    cv2.destroyAllWindows()