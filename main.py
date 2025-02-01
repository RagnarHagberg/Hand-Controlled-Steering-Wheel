import asyncio

import cv2
import mediapipe as mp
from mediapipe.tasks import python
import time
import GestureTracker
import HandTracker
import WebSocket


GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult

MODEL_PATH = r"Models\gesture_recognizer.task"

closed_fist = False
time_when_fist_closed = 0
fist_release_delay = 0.5


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
async def hand_tracking(queue):
    global closed_fist, time_when_fist_closed

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

    use_gesture_recognizer = False
    frame_counter = 0
    gesture_recognition_interval = 3  # Run every 3 frames

    with GestureRecognizer.create_from_options(options) as recognizer:
        while True:
            ret, frame = cap.read()

            if not ret:
                continue

            frame_counter += 1

            # Do gesture recognition before other alterations of the frame
            # Run gesture recognition every 3 frames to reduce computation
            if use_gesture_recognizer and frame_counter % gesture_recognition_interval == 0:
                timestamp_ms = int(time.time() * 1000)
                # Convert stream to image type for gesture recognizer
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

                recognizer.recognize_async(mp_image, timestamp_ms)

            # Find fingers for next operations
            frame = detector.process_frame(frame, False)
            if not use_gesture_recognizer:
                true_fingers = [True for x in detector.get_closed_fingers() if x]
                detected_fist = len(true_fingers) > 2 # More than 2 fingers closed means a fist

                if detected_fist:
                    closed_fist = True
                    time_when_fist_closed = time.time() # Start tracking the time the fist was closed
                else:
                    if closed_fist and (time.time() - time_when_fist_closed >= fist_release_delay):
                        closed_fist = False

            detector.draw_steering_wheel(frame, closed_fist)

            #steering_data = {"rotation_angle": detector.steering_wheel_angle if closed_fist else 0.0}  # Example data, can be more complex
            steering_data = {"rotation_angle": detector.steering_wheel_angle}
            print(f"Hand tracking data: {steering_data} from tracker")  # Debug print for hand tracking data
            await queue.put(steering_data)

            # Flip Screen
            frame = cv2.flip(frame, 1)

            # Display fps on screen
            ctime = time.time()
            fps = 1 / (ctime - ptime)
            ptime = ctime
            cv2.putText(frame, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

            cv2.imshow('frame', frame)
            cv2.waitKey(1)

            await asyncio.sleep(0.1)  # Yield control to the asyncio loop


#change to multithread

async def main():
    queue = asyncio.Queue()

    # Start WebSocket server
    server_task = asyncio.create_task(WebSocket.start_server())

    # Start hand tracking (sends data to queue)
    hand_tracking_task = asyncio.create_task(hand_tracking(queue))

    # Start sending steering data to clients
    send_data_task = asyncio.create_task(WebSocket.send_steering_data(queue))

    # Run all tasks
    await asyncio.gather(server_task, hand_tracking_task, send_data_task)

if __name__ == "__main__":
    asyncio.run(main())
