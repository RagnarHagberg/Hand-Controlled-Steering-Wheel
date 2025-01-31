import cv2
import mediapipe as mp
from mediapipe.tasks import python
import time
import GestureTracker
import HandTracker

GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult

MODEL_PATH = r"Models\gesture_recognizer.task"

closed_fist = False


# Gets result from the GestureRecognizer with live stream mode
def get_gesture_recognizer_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    global closed_fist
    # print('gesture recognition result: {}'.format(result))
    if result.gestures:
        if result.gestures[0][0].category_name == "Closed_Fist":
            closed_fist = True
        else:
            closed_fist = False
    else:
        closed_fist = False


def main():
    global closed_fist

    ptime = 0

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    detector = HandTracker.HandTracker()

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    gesture_tracker = GestureTracker.GestureTracker(get_gesture_recognizer_result, MODEL_PATH)
    options = gesture_tracker.create_options()

    with GestureRecognizer.create_from_options(options) as recognizer:
        while True:
            ret, frame = cap.read()

            # Do gesture recognition first
            # Convert stream to image type for gesture recognizer
            timestamp_ms = int(time.time() * 1000)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

            recognizer.recognize_async(mp_image, timestamp_ms)

            # Find fingers for next operations
            frame = detector.process_frame(frame)
            detector.draw_steering_wheel(frame, closed_fist)

            # Display fps on screen
            ctime = time.time()
            fps = 1 / (ctime - ptime)
            ptime = ctime
            cv2.putText(frame, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imshow('frame', frame)
            cv2.waitKey(1)


if __name__ == "__main__":
    main()
