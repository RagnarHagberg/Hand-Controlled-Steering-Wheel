import mediapipe as mp
import math as math
import cv2

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
        x_list, y_list, landmarks_list = [], [], []
        bounding_box = []
        hand_center = (0, 0)

        if self.results.multi_hand_landmarks:
            if hand_no >= len(self.results.multi_hand_landmarks):
                return None, None, None  # Return None if requested hand is not found

            my_hand = self.results.multi_hand_landmarks[hand_no]

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

        if self.results.multi_hand_landmarks and move_steering_wheel:
            angle_to_center, distance_to_center = self.get_hand_angle(frame)

            if self.previous_hand_angle is not None:
                self.steering_wheel_angle -= self.previous_hand_angle - angle_to_center

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