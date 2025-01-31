import mediapipe as mp
from mediapipe.tasks import python


class GestureTracker:
    def __init__(self, result_callback, model_file_path):
        self.BaseOptions = mp.tasks.BaseOptions
        self.GestureRecognizer = mp.tasks.vision.GestureRecognizer
        self.GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        self.GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
        self.VisionRunningMode = mp.tasks.vision.RunningMode
        self.result_callback = result_callback

        model_file = open(model_file_path, "rb")
        model_data = model_file.read()
        model_file.close()

        self.base_options = python.BaseOptions(model_asset_buffer=model_data)

    def create_options(self):
        options = self.GestureRecognizerOptions(
            base_options=self.base_options,
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            result_callback=self.result_callback)
        return options
