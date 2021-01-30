#!/usr/bin/env python3


from gi.repository import GLib

import cv2
import pyfakewebcam


class CamPy:
    def __init__(self, width, height, framerate):
        self.input_device = None
        self.output_device = None
        self.set_camera_width(width)
        self.set_camera_height(height)
        self.set_camera_framerate(framerate)
        self.filters = []

    def __del__(self):
        if self.input_device != None:
            del self.input_device

        if self.output_device != None:
            del self.output_device

    def set_input_device(self, input_device):
        print(f"Created camera with size {self.width}:{self.height}:{self.framerate}")
        self.input_device = cv2.VideoCapture(input_device)
        self.input_device.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.input_device.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.input_device.set(cv2.CAP_PROP_FPS, self.framerate)

    def set_output_device(self, output_device):
        self.output_device = pyfakewebcam.FakeWebcam(output_device, self.width, self.height)

    def set_camera_width(self, width):
        print(f"Setting width: {width}")
        self.width = int(width)
        if self.input_device is not None:
            self.input_device.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

    def set_camera_height(self, height):
        print(f"Setting height: {height}")
        self.height = int(height)
        if self.input_device is not None:
            self.input_device.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def set_camera_framerate(self, framerate):
        print(f"Setting framerate: {framerate}")
        self.framerate = int(framerate)
        if self.input_device is not None:
            self.input_device.set(cv2.CAP_PROP_FPS, self.framerate)

    def add_filter(self, fil):
        self.filters.append(fil)

    # Questo metodo scatta una foto dalla webcam, la processa e la manda alla webcam fake.
    def start_iteration(self):
        if self.input_device is None:
            GLib.Error("La webcam non e` stata creata")
            return

        status, current_frame = self.input_device.read()
        if status == False:
            GLib.Error("Impossibile leggere dalla webcam!")
            return

        frame = self.apply_all_filters(current_frame)

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.output_device.schedule_frame(frame)


    # Processa un frame con un filtro
    def apply_all_filters(self, frame):
        for fil in self.filters:
            returned_frame = fil.apply(frame)
            if returned_frame is None:
                GLib.Error(f"Filter failed: {fil.package_name}")
                continue

            frame = returned_frame

        return frame

    # Show a frame
    def show_frame(self, frame):
        cv2.imshow("Frame da mostrare", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
