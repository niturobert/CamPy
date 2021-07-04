#!/usr/bin/env python3

import os
import sys

# GUI.
from PySide6 import QtWidgets, QtCore, QtGui
from __feature__ import snake_case, true_property


# Import modules from the current project.
from WebcamWorker import WebcamWorker

## Import custom widgets.
# from components import WebcamWidget


# My classes.
class CamPy(QtWidgets.QWidget):
    running = False
    filename = None

    def __init__(self):
        super().__init__()
        self.build_interface()

    def build_interface(self):
        # Main Window's properties
        self.window_title = "CamPy"
        self.maximum_width, self.maximum_height = 300, 100
        self.window_icon = QtGui.QIcon(os.path.join(os.getcwd(), "assets", "logo.png"))

        # Layouts
        layout_core = QtWidgets.QVBoxLayout(self)
        layout_camera = QtWidgets.QFormLayout()
        layout_buttons = QtWidgets.QVBoxLayout()

        # Children of the layout_camera layout
        lbl_width = QtWidgets.QLabel("Width")
        lbl_height = QtWidgets.QLabel("Height")
        lbl_framerate = QtWidgets.QLabel("Framerate")

        self.le_width = QtWidgets.QLineEdit()
        self.le_height = QtWidgets.QLineEdit()
        self.le_framerate = QtWidgets.QLineEdit()

        self.le_width.max_length = self.le_height.max_length= self.le_framerate.max_length= 4
        self.le_width.validator = self.le_height.validator = self.le_framerate.validator = QtGui.QIntValidator()
        self.le_width.text, self.le_height.text, self.le_framerate.text = "1280", "720", "20"

        layout_camera.add_row(lbl_width, self.le_width)
        layout_camera.add_row(lbl_height, self.le_height)
        layout_camera.add_row(lbl_framerate, self.le_framerate)

        # Children of the layout_buttons layout
        self.cb_model = QtWidgets.QComboBox()
        self.cb_model.add_item("[NOT IMPLEMENTED] Low Quality")
        self.cb_model.add_item("Medium Quality")
        self.cb_model.add_item("[NOT IMPLEMENTED] High Quality")
        self.cb_model.add_item("[NOT IMPLEMENTED] Max Quality")
        self.cb_model.current_text = "Medium Quality"

        self.chk_hologram = QtWidgets.QCheckBox("Hologram")
        self.chk_flip = QtWidgets.QCheckBox("Flip")
        self.btn_file = QtWidgets.QPushButton("Select Background Video")
        self.btn_done = QtWidgets.QPushButton("Start")

        self.btn_file.clicked.connect(self.pick_background_file)
        self.btn_done.clicked.connect(self.toggle_campy_running)

        # Set the layouts
        layout_core.add_layout(layout_camera)
        layout_core.add_layout(layout_buttons)

        layout_buttons.add_widget(self.chk_hologram)
        layout_buttons.add_widget(self.chk_flip)
        layout_buttons.add_widget(self.cb_model)
        layout_buttons.add_widget(self.btn_file)
        layout_buttons.add_widget(self.btn_done)

        self.layout = layout_core
        print(self.children())

    def pick_background_file(self):
        # options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.get_open_file_name(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            # "All Files (*);;Webp/Webm (*.webp *.webm);;Mp4 (*.mp4)",
            "Video File (*.webp *.webm *.mp4 *.mkv *.avi)",
            options=QtWidgets.QFileDialog.Options()
        )

        if filename:
            # File was chosen.
            self.filename = filename
            self.btn_file.text = filename.split("/")[-1]
            self.btn_file.text = self.btn_file.text[:12] + "..." if len(self.btn_file.text) >= 15 else self.btn_file.text

    def toggle_campy_running(self):
        self.running = not self.running
        if self.running:
            # Check if background was chosen.
            if self.filename is None:
                self.running = not self.running
                return self.show_message(
                    "Error",
                    "Please select a background video",
                    QtWidgets.QMessageBox.Critical,
                )

            # Update the button's text.
            self.loading_disable_stop()

            # Start the campy thread.
            self.worker_thread = WebcamWorker(
                video_path=self.filename,
                loaded=self.loaded_enable_stop,
                stopped=self.stopped_enable_all,
                resolution=(self.le_width.text, self.le_height.text, self.le_framerate.text),
                flip=self.chk_flip.checked,
                hologram=self.chk_hologram.checked,
            )
            # self.worker_thread.starting_event_loop.connect(self.update_btn_label)
            self.worker_thread.start()

        else:
            # Stop the campy thread.
            self.worker_thread.stop()
            self.worker_thread.join()

    def show_message(self, title="Alert", text="Alert", icon=QtWidgets.QMessageBox.Information):
        message = QtWidgets.QMessageBox()
        message.icon = icon
        message.text = text
        message.window_title = title

        return message.exec()

    # Methods used to toggle data.
    def loading_disable_stop(self):
        self.cb_model.enabled = False
        self.btn_file.enabled = self.btn_done.enabled = False
        self.chk_flip.enabled = self.chk_hologram.enabled = False
        self.le_width.enabled = self.le_height.enabled = self.le_framerate.enabled = False

        self.btn_done.text = "Starting..."

    def loaded_enable_stop(self):
        self.btn_done.text = "Stop"
        self.btn_done.enabled = True

    def stopped_enable_all(self):
        self.btn_done.text = "Start"
        self.cb_model.enabled = True
        self.btn_file.enabled = True
        self.chk_flip.enabled = self.chk_hologram.enabled = True
        self.le_width.enabled = self.le_height.enabled = self.le_framerate.enabled = True


if __name__ == '__main__':
    campy = QtWidgets.QApplication(sys.argv)
    widget = CamPy()
    widget.resize(300, 100)
    widget.show()

    sys.exit(campy.exec())