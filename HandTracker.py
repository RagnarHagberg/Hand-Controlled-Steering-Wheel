import asyncio
import json
import time

import mediapipe as mp
import math as math
import cv2
from math import dist

import websockets


class HandTracker:
    def __init__(self, mode=False, max_hands=2, detection_confidence=0.5, tracking_confidence=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )

        self.mp_draw = mp.solutions.drawing_utils

        # Landmark indices for fingertips
        self.tip_ids = [4, 8, 12, 16, 20]

        # Steering wheel tracking
        self.steering_wheel_angle = math.pi / 2  # Default upright position
        self.previous_hand_angle = None

        # For stabilization
        self.previous_hand_position = None
        self.tracked_hand_id = -1
        self.last_seen_hand_time = 0
        self.hand_timeout = 2.0

    #Change
    def process_frame(self, frame, draw=True):
        '''
        Detects hands and landmarks in a frame.
        '''

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)


        return frame

    def get_hand_position(self, frame, hand_no=0, draw=True):
        '''
        Finds the position of hand landmarks in the frame.
        '''

        if not self.results.multi_hand_landmarks:
            if time.time() - self.last_seen_hand_time > self.hand_timeout:
                self.tracked_hand_id = -1
                return
            else:
                return None, None, None

        min_movement = float('inf')

        # Check for most likely hand
        for i, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
            # Compute hand center (average of all landmark positions)
            hand_x = sum(lm.x for lm in hand_landmarks.landmark) / len(hand_landmarks.landmark)
            hand_y = sum(lm.y for lm in hand_landmarks.landmark) / len(hand_landmarks.landmark)
            current_hand_position = (hand_x, hand_y)

            # Compare movement against the last known hand position
            if self.previous_hand_position is not None:
                movement = math.dist(current_hand_position, self.previous_hand_position)  # Euclidean distance
            else:
                 # select zeroth hand
                movement = 0  # First frame, no previous position

            if movement < min_movement:
                min_movement = movement
                best_hand_index = i

        self.tracked_hand_id = best_hand_index
        self.last_seen_hand_time = time.time()
        my_hand = self.results.multi_hand_landmarks[self.tracked_hand_id]

        self.previous_hand_position = (
                sum(lm.x for lm in self.results.multi_hand_landmarks[best_hand_index].landmark) / len(
                    self.results.multi_hand_landmarks[best_hand_index].landmark),
                sum(lm.y for lm in self.results.multi_hand_landmarks[best_hand_index].landmark) / len(
                    self.results.multi_hand_landmarks[best_hand_index].landmark),
            )

        x_list, y_list, landmarks_list = [], [], []

        for idx, landmark in enumerate(my_hand.landmark):
            h, w, _ = frame.shape
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            x_list.append(cx)
            y_list.append(cy)
            landmarks_list.append((idx, cx, cy))

            if draw:
                cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        # Bounding box around hand
        xmin, xmax = min(x_list), max(x_list)
        ymin, ymax = min(y_list), max(y_list)
        bounding_box = (xmin, ymin, xmax, ymax)
        hand_center = ((xmin + xmax) // 2, (ymin + ymax) // 2)

        if draw:
            cv2.rectangle(frame, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)

        return landmarks_list, bounding_box, hand_center

    def draw_steering_wheel(self, frame, move_steering_wheel=True):
        distance_to_center = None

        # print(self.steering_wheel_angle)
        if self.results.multi_hand_landmarks and move_steering_wheel:
            angle_to_center, distance_to_center = self.get_hand_angle(frame)

            if self.previous_hand_angle is not None:
                # Ignore unreasonably big changes
                dif = min(0.5,self.previous_hand_angle - angle_to_center)
                dif = max(-0.5, dif)

                self.steering_wheel_angle -= dif

            self.previous_hand_angle = angle_to_center
        else:
            # Rotate back to default position
            self._reset_steering_wheel()

        circle_radius = distance_to_center if distance_to_center else 100

        # Draw steering wheel circle
        cv2.circle(frame, (320, 240), circle_radius, (20, 20, 40), 15)

        # Draw rotation handle
        pt1 = (int(320 + circle_radius * math.cos(self.steering_wheel_angle)),
               int(240 + circle_radius * (-math.sin(self.steering_wheel_angle))))
        pt2 = (int(pt1[0] + 15 * math.sin(self.steering_wheel_angle)),
               int(pt1[1] + 15 * math.cos(self.steering_wheel_angle)))

        cv2.line(frame, pt1, pt2, (255, 255, 255), 15)

    def get_hand_angle(self, frame):
        '''
        Calculates the angle of the hand relative to the screen center.
        '''

        _, _, hand_center = self.get_hand_position(frame, 0, draw=False)

        if hand_center is None:
            return None, None

        adjusted_x = hand_center[0] - 320  # Center X-coordinate (frame width / 2)
        adjusted_y = hand_center[1] - 240  # Center Y-coordinate (frame height / 2)

        distance_to_center = math.sqrt(adjusted_x ** 2 + adjusted_y ** 2)
        angle_to_center = math.acos(adjusted_x / distance_to_center) if distance_to_center else 0

        if adjusted_y > 0:
            angle_to_center = 2 * math.pi - angle_to_center

        return angle_to_center, int(distance_to_center)

    def _reset_steering_wheel(self):
        '''
        Gradually resets the steering wheel angle to the default upright position.
        '''
        step = 0.1
        target = math.pi / 2

        if self.steering_wheel_angle < target:
            self.steering_wheel_angle = min(self.steering_wheel_angle + step, target)
        else:
            self.steering_wheel_angle = max(self.steering_wheel_angle - step, target)

        self.previous_hand_angle = None

    def get_landmark_x_coordinate(self, landmark):  # landmark --> out of 21
        if len(self.results.multi_hand_landmarks) - 1 >= self.tracked_hand_id:
            return float(str(self.results.multi_hand_landmarks[self.tracked_hand_id].landmark[int(landmark)]).split('\n')[0].split(" ")[1])

    def get_landmark_y_coordinate(self,landmark):  # landmark --> out of 21
        if len(self.results.multi_hand_landmarks) - 1 >= self.tracked_hand_id:
            return float(str(self.results.multi_hand_landmarks[self.tracked_hand_id].landmark[int(landmark)]).split('\n')[1].split(" ")[1])


    def is_finger_closed(self, tip_landmark):
        '''
        The finger is closed if the tip of the finger is closer to the palm than the middle
        '''

        palm_x = self.get_landmark_x_coordinate(0)  # coordinates of landmark 0
        palm_y = self.get_landmark_y_coordinate(0)

        top_x = self.get_landmark_x_coordinate(tip_landmark)
        top_y = self.get_landmark_y_coordinate(tip_landmark)

        middle_x = self.get_landmark_x_coordinate(tip_landmark-1)
        middle_y = self.get_landmark_y_coordinate(tip_landmark-1)

        if not (palm_x and palm_y and top_x and top_y and middle_x and middle_y):
            return False

        distance_top_to_palm = dist([palm_x, palm_y], [top_x, top_y])
        distance_middle_to_palm = dist([palm_x, palm_y], [middle_x, middle_y])

        if distance_top_to_palm < distance_middle_to_palm:
            return True

    def get_closed_fingers(self):  # is z="finger, it retuens which finger is closed. If z="true coordinate", it returns the true coordinates
        if not self.results.multi_hand_landmarks:
            return []

        closed_fingers = []

        tip_ids_to_check_for = self.tip_ids[1:]
        for landmark_index in tip_ids_to_check_for:
            closed_fingers.append(self.is_finger_closed(landmark_index))

        return closed_fingers

