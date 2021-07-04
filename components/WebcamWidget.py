#!/usr/bin/env python3

from PySide6 import QtWidgets
from PySide6.QtCore import pyqtSignal

class WebcamWidget(QtWidgets.QWidget):
    """
    WebcamWidget is a simple frame used to display the webcam.
    """


    def __init__(self):
        super().__init__()
