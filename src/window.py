# window.py
#
# Copyright 2021 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib
import threading
import os

from .CamPy import CamPy
from .Filter import Filter


@Gtk.Template(resource_path='/io/sighub/campy/window.ui')
#@Gtk.Template(filename='window.ui')
class CampyWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CampyWindow'

    # Webcam properties
    entry_webcam_width = Gtk.Template.Child()
    entry_webcam_height = Gtk.Template.Child()
    entry_webcam_framerate = Gtk.Template.Child()
    button_prova = Gtk.Template.Child()
    button_avvia = Gtk.Template.Child()

    # Filter properties
    switch_animated_background = Gtk.Template.Child()
    filechooser_background = Gtk.Template.Child()


    # Buttons
    combobox_input = Gtk.Template.Child()
    combobox_output = Gtk.Template.Child()

    # Data lists
    dispositivi = Gtk.Template.Child()

    filefilter_photo = Gtk.Template.Child()
    filefilter_video = Gtk.Template.Child()

    # Variables for logic
    is_webcam_daemon_running = False
    webcam_daemon = None


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind_signals()
        self.configure_devices_list()
        self.webcam_driver = CamPy(
            width = 640,
            height = 480,
            framerate = 60
        )
        self.webcam_driver.add_filter(Filter())

    def __del__(self):
        if self.running_task is not None:
            self.running_task.kill()

    def bind_signals(self):
        # Stuff for the filter
        self.switch_animated_background.connect('state-set', self.handle_switch_animated_background)

        # Connect the bottom buttons
        self.button_prova.connect('clicked', self.handle_button_test)
        self.button_avvia.connect('clicked', self.handle_button_avvia)

    def configure_devices_list(self):
        print("Devices list")
        video_cameras = [f for f in os.listdir('/dev/') if f.startswith("video")]
        for camera in video_cameras:
            self.dispositivi.append(("/dev/" + camera, ))

    def set_webcam_values(self):
        self.webcam_driver.filters[0].set_option("background", self.filechooser_background.get_filename())

        self.webcam_driver.set_camera_width(self.entry_webcam_width.get_text())
        self.webcam_driver.set_camera_height(self.entry_webcam_height.get_text())
        self.webcam_driver.set_camera_framerate(self.entry_webcam_framerate.get_text())

        self.webcam_driver.set_input_device(self.combobox_input.get_model()[self.combobox_input.get_active()][0])
        self.webcam_driver.set_output_device(self.combobox_output.get_model()[self.combobox_output.get_active()][0])

    # Avvia il servizio della webcam
    def avvia_servizio_webcam(self):
        self.set_webcam_values()
        while self.is_webcam_daemon_running:
            self.webcam_driver.start_iteration()

    #
    # Signal handlers
    #
    def handle_switch_animated_background(self, *args):
        self.webcam_driver.filters[0].set_option("animated", args[1])
        if args[1]:
            # Background should be animated
            self.filechooser_background.set_filter(self.filefilter_video)

        else:
            # Background should not be animated
            self.filechooser_background.set_filter(self.filefilter_photo)

    def handle_button_test(self, *args):
        self.set_webcam_values()

        success, current_frame = self.webcam_driver.input_device.read()
        self.webcam_driver.input_device.release()
        if not success:
            a = Gtk.MessageDialog(
                type = Gtk.MessageType.ERROR,
                title = "Errore",
                parent = None,
                buttons = Gtk.ButtonsType.CANCEL,
            )

            a.format_secondary_text(
                "Impossibile scattare foto dalla webcam."
            )

            # a.set_default_size(200, 150)
            GLib.Error("Non e' stato possibile leggere dalla webcam")
            a.run()
            a.destroy()
            return

        print(f"Testing frame size: {current_frame.size}")
        for fil in self.webcam_driver.filters:
            frame = fil.apply_static_filter(frame)

        self.webcam_driver.show_frame(frame)

    def handle_button_avvia(self, *args):
        self.is_webcam_daemon_running = not self.is_webcam_daemon_running
        if self.is_webcam_daemon_running:
            self.button_avvia.set_label("Termina")
            self.webcam_daemon = threading.Thread(target=self.avvia_servizio_webcam, daemon = True)
            self.webcam_daemon.start()

        else:
            self.button_avvia.set_label("Avvia")
            self.webcam_daemon.join()
            self.webcam_driver.input_device.release()
