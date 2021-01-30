#!/usr/bin/env python3


from gi.repository import Gio, GLib

import cv2
import numpy
import requests
import tensorflow
from tf_bodypix.api import load_model, download_model, BodyPixModelPaths

from os import path
from os.path import expanduser

class Filter:
    package_name = "io.sighub.tay_ai"

    def __init__(self):
        # TODO: salvare il modello al primo download.
        self.bodypix_model = load_model(
            download_model(
                BodyPixModelPaths.MOBILENET_FLOAT_75_STRIDE_16
            )
        )

        self.options = {
            "animated": True,
            "background": None,
            "hologram": False,
        }

        self.background_image = None
        self.background_video = None
        self.current_frame = 0

    def __del__(self):
        pass

    def set_option(self, option_name, option_value):
        self.options[option_name] = option_value

        if option_name == "background":
            if self.options["animated"] == False:
                self.background_image = cv2.imread(option_value)

            else:
                self.background_video = cv2.VideoCapture(option_value)
                self.current_frame = 0

    def get_people_mask(self, frame):
        risultato = self.bodypix_model.predict_single(frame)
        # mask e' un tensorflow.python.framework.ops.EagerTensor
        mask = risultato.get_mask(threshold = 0.7)

        # convertiamolo in un bell'array
        mask = tensorflow.keras.preprocessing.image.img_to_array(mask)
        mask = cv2.dilate(mask, numpy.ones((10,10), numpy.uint8) , iterations=1)

        #mask = cv2.erode(mask, numpy.ones((10,10), numpy.uint8) , iterations=1)
        mask = cv2.blur(mask.astype(float), (30,30))

        return mask

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


    def apply(self, frame):
        if self.options["animated"]:
            return self.apply_animated(frame)

        return self.apply_static(frame)

    def apply_static(self, frame):
        mask = self.get_people_mask(frame)

        width, height = frame.shape[1], frame.shape[0]
        background_frame = cv2.resize(self.background_image, (width, height))

        # cv2.imshow("Background image", background_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        if self.options["hologram"]: frame = self.apply_hologram_effect(frame)
        inv_mask = 1 - mask
        for c in range(frame.shape[2]):
            frame[:,:,c] = frame[:,:,c] * mask + background_frame[:,:,c] * inv_mask

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

    def apply_animated(self, frame):
        mask = self.get_people_mask(frame)
        if self.current_frame >= self.background_video.get(cv2.CAP_PROP_FRAME_COUNT):
            self.current_frame = 1
            self.background_video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        width, height = frame.shape[1], frame.shape[0]
        self.current_frame += 1
        status, background_frame = self.background_video.read()
        if status is False:
            GLib.Error("Frame del background ignorato")
            return None

        background_frame = cv2.resize(background_frame, (width, height))

        if self.options["hologram"]: frame = self.apply_hologram_effect(frame)
        inv_mask = 1 - mask
        for c in range(frame.shape[2]):
            frame[:,:,c] = frame[:,:,c] * mask + background_frame[:,:,c] * inv_mask

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
