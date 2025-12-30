import cv2
from cvzone.FaceDetectionModule import FaceDetector
import pyfirmata
import numpy as np
import time

# Initialization
cap = cv2.VideoCapture(0)
ws, hs = 1280, 720
cap.set(3, ws)
cap.set(4, hs)

if not cap.isOpened():
    print("Camera couldn't Access!!!")
    exit()

port = "COM11"
board = pyfirmata.Arduino(port)
servo_pinX = board.get_pin('d:9:s')  # pin 9 Arduino
servo_pinY = board.get_pin('d:10:s')  # pin 10 Arduino

# Additional Servo Motor on pin 11
servo_pinZ = board.get_pin('d:11:s')  # pin 11 Arduino
servoZ_initial_pos = 0
servo_pinZ.write(servoZ_initial_pos)

detector = FaceDetector()
servoPos = [90, 90]  # initial servo position

start_time = time.time()  # Record the start time for the additional servo movement

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture image!")
        break

    # Flip the image horizontally
    img = cv2.flip(img, 1)

    img, bboxs = detector.findFaces(img, draw=False)

    if bboxs:
        # Get the face coordinates
        fx, fy = bboxs[0]["center"][0], bboxs[0]["center"][1]
        pos = [fx, fy]

        # Corrected servo degree conversion
        servoX = np.interp(fx, [0, ws], [0, 180])  # Normal horizontal servo
        servoY = np.interp(fy, [0, hs], [180, 0])  # Normal vertical servo (no change)

        # Clamp values to be between 0 and 180 degrees
        servoX = np.clip(servoX, 0, 180)
        servoY = np.clip(servoY, 0, 180)

        servoPos[0] = servoX
        servoPos[1] = servoY

        # Visual elements on screen
        cv2.circle(img, (fx, fy), 80, (0, 0, 255), 2)
        cv2.putText(img, str(pos), (fx + 15, fy - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.line(img, (0, fy), (ws, fy), (0, 0, 0), 2)  # x line
        cv2.line(img, (fx, hs), (fx, 0), (0, 0, 0), 2)  # y line
        cv2.circle(img, (fx, fy), 15, (0, 0, 255), cv2.FILLED)
        cv2.putText(img, "TARGET LOCKED", (850, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

    else:
        # No target scenario
        cv2.putText(img, "NO TARGET", (880, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
        cv2.circle(img, (640, 360), 80, (0, 0, 255), 2)
        cv2.circle(img, (640, 360), 15, (0, 0, 255), cv2.FILLED)
        cv2.line(img, (0, 360), (ws, 360), (0, 0, 0), 2)  # x line
        cv2.line(img, (640, hs), (640, 0), (0, 0, 0), 2)  # y line

    # Display servo positions
    cv2.putText(img, f'Servo X: {int(servoPos[0])} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.putText(img, f'Servo Y: {int(servoPos[1])} deg', (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    # Update the face-tracking servos
    servo_pinX.write(servoPos[0])
    servo_pinY.write(servoPos[1])

    # Handle the additional servo (Z axis) rotation logic
    elapsed_time = time.time() - start_time

    if elapsed_time <= 10:
        # Rotate from 0 to 90 degrees over 10 seconds
        angleZ = np.interp(elapsed_time, [0, 10], [0, 90])
        servo_pinZ.write(angleZ)
    elif elapsed_time > 10 and elapsed_time <= 11:
        # Hold for 1 second
        servo_pinZ.write(90)
    else:
        # Return to 0 degrees after 1 second
        servo_pinZ.write(servoZ_initial_pos)
        start_time = time.time()  # Reset the timer for the next cycle

    # Display the image
    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
board.exit()
