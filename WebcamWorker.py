#!/usr/bin/env python3

import os
import sys
import threading

# External Libraries.
import cv2
import numpy
import pyvirtualcam
import tensorflow as tf
from tf_bodypix.api import load_model
from tf_bodypix.api import download_model, BodyPixModelPaths

# Gui stuff.
from PySide6 import QtWidgets
# from PySide6.QtCore import Signal


class WebcamWorker(threading.Thread):
    """
    WebcamWorker is a thread used to capture, process, and send the frames from the real webcam to the fake one.
    The fake webcam requires OBS webcam to be installed on the system.
    """

    # Constants
    cam_width, cam_height, cam_fps = 1280, 720, 20

    # Events
    # starting_event_loop = Signal()
    is_running = True

    # Other attributes
    current_frame = 1
    max_frames = 0
    background = None


    # Constructor
    def __init__(self, video_path="", loaded=None, stopped=None, resolution=(1280, 720, 20), hologram=False, flip=False):
        super().__init__()

        print(f"Hologram: {hologram}\r\nFlip: {flip}")
        self.background = cv2.VideoCapture(video_path)
        self.max_frames = self.background.get(cv2.CAP_PROP_FRAME_COUNT)
        self.cam_width, self.cam_height, self.cam_fps = int(resolution[0]), int(resolution[1]), int(resolution[2])

        # Configurations
        self.hologram = hologram
        self.flip = flip

        # Hooks
        self.loaded = loaded
        self.stopped = stopped

        # Load the model.
        # print("Path: %s" % os.path.join(os.path.abspath(os.getcwd()), "model.json"))
        # self.bodypix_model = load_model(os.path.join(os.path.abspath(os.getcwd()), "model.json"))
        print("Loading tensorflow model")
        self.bodypix_model = load_model(
            download_model(
                BodyPixModelPaths.MOBILENET_FLOAT_50_STRIDE_16,
            )
        )
    
    def configure_webcams(self):
        print("Opening real webcam...")
        # Configure and use the real camera.
        self.real_webcam = cv2.VideoCapture(0)
        
        print("Configuring real webcam...")
        self.real_webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
        self.real_webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)

        # Use the first available camera (usually OBS) for output.
        print("Opening fake webcam...")
        self.fake_webcam = pyvirtualcam.Camera(width=self.cam_width, height=self.cam_height, fps=self.cam_fps)
        print("Done")

    def capture_frame(self):
        return self.real_webcam.read()

    def process_frame(self, frame):
        # Step 1: get the background frame from the selected file.
        if self.current_frame >= self.max_frames:
            self.current_frame = 0
            self.background.set(cv2.CAP_PROP_POS_FRAMES, 1)

        self.current_frame += 1
        status, background_frame = self.background.read()
        if status is False: return frame

        background_frame = cv2.resize(background_frame, (self.cam_width, self.cam_height))

        # Step 2: flip the image if requested.
        if self.flip: frame = numpy.flip(frame, 1)


        # Step 3: detect people from the frame.
        _people_frame = self.bodypix_model.predict_single(frame)
        people_frame = _people_frame.get_mask(threshold = 0.7)
        people_frame = tf.keras.preprocessing.image.img_to_array(people_frame)
        people_frame = cv2.dilate(people_frame, numpy.ones((10,10), numpy.uint8) , iterations=1)
        people_frame = cv2.blur(people_frame.astype(float), (30,30))
        
        # Step 4: apply the custom effects (if enabled).
        if self.hologram: frame = self.apply_hologram_effect(frame)

        # Step 5: apply the background to the pixels not in the body.
        inverse_people_frame = 1 - people_frame
        for c in range(frame.shape[2]):
            frame[:,:,c] = frame[:,:,c] * people_frame + background_frame[:,:,c] * inverse_people_frame

        # Last step: convert the color palette from BGR to RGB and return the frame.
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def send_frame(self, frame):
        self.fake_webcam.send(frame)

    def show_message(self, title="Alert", text="Alert", icon=QtWidgets.QMessageBox.Information):
        message = QtWidgets.QMessageBox()
        message.icon = icon
        message.text = text
        message.window_title = title

        return message.exec()

    def apply_hologram_effect(self, frame):
        def shift_image(img, dx, dy):
            img = numpy.roll(img, dy, axis=0)
            img = numpy.roll(img, dx, axis=1)
            if dy>0:
                img[:dy, :] = 0
            elif dy<0:
                img[dy:, :] = 0
            if dx>0:
                img[:, :dx] = 0
            elif dx<0:
                img[:, dx:] = 0
            return img

        blue_pill = cv2.applyColorMap(frame, cv2.COLORMAP_WINTER)
        bandLength, bandGap = 2, 3
        for y in range(blue_pill.shape[0]):
            if y % (bandLength+bandGap) < bandLength:
                blue_pill[y,:,:] = blue_pill[y,:,:] * numpy.random.uniform(0.1, 0.3)

        blue_blur = cv2.addWeighted(blue_pill, 0.2, shift_image(blue_pill.copy(), 5, 5), 0.8, 0)
        blue_blur = cv2.addWeighted(blue_blur, 0.5, shift_image(blue_blur.copy(), -5, -5), 0.6, 0)
        return cv2.addWeighted(frame, 0.5, blue_blur, 0.6, 0)


    def run(self):
        self.configure_webcams()
        self.is_running = True

        # Main loop.
        print("Fake webcam initialized")
        self.loaded()
        while self.is_running:
            success, captured_frame = self.capture_frame()
            if not success:
                sys.stderr.write("Failed to read from webcam...\r\n")
                self.show_message(title="Warning", text="Failed to read from webcam. Please make sure that there is no other program running...")
                continue

            self.send_frame(self.process_frame(captured_frame))

        # Close the camera.
        print("Main loop ended, freeing webcam...")
        self.stopped()
        self.fake_webcam.close()
        self.real_webcam.release()

    def stop(self):
        self.is_running = False


