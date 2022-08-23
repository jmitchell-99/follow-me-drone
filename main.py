import time
import cv2
import torch
import ps_drone3 as psd3
from landing import *

model = torch.hub.load('yolov5', 'custom', path='best.pt', source='local', _verbose=True)
print("Object detection model loaded.")

class FollowMeDrone:

    def __init__(self):
        """Connect to the drone."""

        self.drone = psd3.Drone()
        self.stop = False
        self.centered = False
        self.first_frame = True
        
    def setup_drone(self):
        """Configure the drone and start using the front camera."""

        self.drone.startup()
        self.drone.reset()
        self.drone.useDemoMode(True)
        self.drone.setConfigAllID() 
        self.drone.sdVideo()
        self.drone.frontCam()

        CDC = self.drone.ConfigDataCount
        while CDC == self.drone.ConfigDataCount:
            time.sleep(0.0001)

        self.drone.startVideo()
        self.IMC = self.drone.VideoImageCount

        # Get initial battery
        while (self.drone.getBattery()[0] == -1):
            time.sleep(0.1)
        print("Battery: " + str(self.drone.getBattery()[0]) + "%  " + str(self.drone.getBattery()[1]))

    def tracking(self):
        """Process the object detection model on the camera frames and make the drone follow detected targets."""

        while not self.stop:

            # Keypress commands
            key = self.drone.getKey()

            if key == 'q':
                print("Quit button pressed. Landing the drone...")
                self.stop = True

            if key == 't':
                print("Drone commencing takeoff...")
                self.drone.takeoff()
                self.drone.stop()

            elif key == 'l':
                cv2.destroyAllWindows()
                self.drone.groundCam()
                self_land(self)
                break

            elif key == 'b':
                # Give a battery update
                while (self.drone.getBattery()[0] == -1):
                    time.sleep(0.1)
                print("Battery: " + str(self.drone.getBattery()[0]) + "%  " + str(self.drone.getBattery()[1]))

            else:
                pass

            # Get video frame
            frame = self.drone.VideoImage 

            try: 
                # Process the frame and get parameters
                frame = cv2.resize(frame, (400, 400))
                (h, w) = frame.shape[:2]
                frame_size = h*w
                frame_center = (w//2, h//2)

                # Run YOLOv5 object detection model on the frame
                results = model(frame)
                df_results = results.pandas().xyxy[0]

                # Add crosshairs at the frame's centerpoint
                cv2.line(frame, (frame_center[0] - 5, frame_center[1]), (frame_center[0] + 5, frame_center[1]), (255, 255, 255), 2)
                cv2.line(frame, (frame_center[0], frame_center[1] - 5), (frame_center[0], frame_center[1] + 5), (255, 255, 255), 2)

                # Show initial video frame
                if self.first_frame == True:
                    cv2.imshow("Drone's front camera", frame)
                    cv2.waitKey(1)
                    self.first_frame = False

                # Find detection's bounding box
                start_point = (int(df_results['xmin'].iloc[0]), int(df_results['ymin'].iloc[0]))
                end_point = (int(df_results['xmax'].iloc[0]), int(df_results['ymax'].iloc[0]))
                xmin = start_point[0]
                xmax = end_point[0]
                ymin = start_point[1]
                ymax = end_point[1]

                # Find bbox's centerpoint, size and percentage size of total frame
                detc_center = (int((xmin + xmax)/2), int((ymin + ymax)/2))
                detc_size = int((xmax - xmin) * (ymax - ymin))
                detc_perc = (detc_size / frame_size) * 100

                # Draw bbox and it's centerpoint, and a line to the frame's centerpoint
                cv2.rectangle(frame, start_point, end_point, (0, 0, 255), 2)
                cv2.circle(frame, detc_center, 5, (255, 0, 0), -1)
                cv2.line(frame, detc_center, frame_center, (0, 255, 0), 2)

                # Show processed video
                cv2.imshow("Drone's front camera", frame)
                cv2.waitKey(1)

                # Align frame's centerpoint with target bbox's centerpoint
                if frame_center[0] > detc_center[0] + 25 or frame_center[0] < detc_center[0] - 25:
                    if frame_center[1] > detc_center[1] + 25 or frame_center[1] < detc_center - 25:
                        centered = False

                        if frame_center[0] > detc_center[0] + 25:
                            print("Turning left...")
                            self.drone.turnLeft()
                            time.sleep(2)
                            self.drone.stop()

                        elif frame_center[0] < detc_center[0] - 25:
                            print("Turning right...")
                            self.drone.turnRight()
                            time.sleep(2)
                            self.drone.stop()

                        if frame_center[1] > detc_center[1] + 25:
                            print("Increasing altitude...") 
                            self.drone.moveUp()
                            time.sleep(2)
                            self.drone.stop()

                        elif frame_center[1] < detc_center[1] - 25:
                            print("Lowering altitude...")
                            self.drone.moveDown()
                            time.sleep(2)
                            self.drone.stop()

                elif frame_center[0] <= detc_center[0] + 25 or frame_center[0] >= detc_center[0] - 25:
                    if frame_center[1] <= detc_center[1] + 25 or frame_center[1] >= detc_center - 25:
                        centered = True
                        print("Drone centered.")

                # Move towards/away from target
                if centered == True:

                    if detc_perc >= 24 and detc_perc <= 26:
                        print("Optimal distance. Drone stationary.")
                        self.drone.stop()
                        pass

                    elif detc_perc < 24:
                        print("Drone too far away. Moving forward...")
                        self.drone.moveForward()
                        time.sleep(2)
                        self.drone.stop()

                    elif detc_perc > 26:
                        print("Drone too close. Moving backward...")
                        self.drone.moveBackward()
                        time.sleep(2)
                        self.drone.stop()

            except:
                pass

        # Land the drone and quit
        self.drone.land()
        print("Drone landed. Exiting program...")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    instance = FollowMeDrone()
    instance.setup_drone()
    instance.tracking()