from PyQt6.QtCore import *
from typing import *
from typing_extensions import TypedDict
import numpy as np
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtMultimedia import *
from PyQt6.QtMultimediaWidgets import *
import os
openslide_path = os.path.abspath("../../openslide/bin")
os.add_dll_directory(openslide_path)
from openslide import OpenSlide


class ZoomDict(TypedDict):
    position: np.ndarray = None
    """ pixel location of the upper left of the data """
    data: np.ndarray = None
    """ image pixel array """


class SlideHandler(QObject):
    update_slides = pyqtSignal()

    def __init__(self, filepath: str = None, width: int = 800, height: int = 600):
        """
        Initialization of SlideLoader
        :param filepath: path of the _slide data. The data type is based on the OpenSlide library and can handle:
                         Aperio (.svs, .tif), Hamamatsu (.vms, .vmu, .ndpi), Leica (.scn), MIRAX (.mrxs),
                         Philips (.tiff), Sakura (.svslide), Trestle (.tif), Ventana (.bif, .tif),
                         Generic tiled TIFF (.tif) (see openslide.org)
        :type filepath: str

        """
        super(SlideHandler, self).__init__()

        self._slide: OpenSlide = None
        self.current_file = filepath
        if filepath is not None:
            self.set_slide(filepath, width, height)

        self._slide_loader_thread = QThread()

        self.moveToThread(self._slide_loader_thread)
        self._slide_loader_thread.start()

        self._num_lvl: int = 0                           # total number of level
        self._slide_size: List[np.ndarray] = []          # list of the size of each level
        self._zoom_stack: Dict[int, ZoomDict] = {}       # stack of the images along the level under the mouse position
        self._mouse_pos: np.ndarray = np.array([0, 0])   # current mouse position
        self._old_center: np.ndarray = np.array([0, 0])  # position on the lowest level on the last update
        self._new_file: bool = True                      # flag for new fie
        self._view_width: int = width                    # width of the GraphicsView
        self._view_height: int = height                  # height of the GraphicsView
        self._stack_mutex = QMutex()                     # locker to ensure now clash between
                                                         # reading and writing the _zoom_stack
        self._updating_slides: bool = True               # flag if update is running

        self.update_slides.connect(self.updating_zoom_stack, Qt.ConnectionType.QueuedConnection)
        self.blockSignals(True)

    def set_slide(self, filepath: str, width: int = None, height: int = None):
        """
        Loads a new _slide. Needs an update_size after loading a new image.
        :param filepath: path of the _slide data. The data type is based on the OpenSlide library and can handle:
                         Aperio (.svs, .tif), Hamamatsu (.vms, .vmu, .ndpi), Leica (.scn), MIRAX (.mrxs),
                         Philips (.tiff), Sakura (.svslide), Trestle (.tif), Ventana (.bif, .tif),
                         Generic tiled TIFF (.tif) (see https://openslide.org)
        :type filepath: str
        :param width: width of the GraphicsView
        :type width: int
        :param height: height of the GraphicView
        :type height: int
        :return: /
        """
        self.blockSignals(True)
        self._slide = OpenSlide(filepath)
        self.current_file = filepath
        if width and height:
            self.update_size(width, height)
        self.blockSignals(False)

    def update_size(self, width: int, height: int):
        """
        Calcuating the needed size of the different level based on the current window size. The resolution of the lower
        levels depend on the window size and not on the original one. Function has to be called after loading new data.
        :param width: width of the GraphicsView
        :type width: int
        :param height: height of the GraphicView
        :type height: int
        :return: /
        """
        self.blockSignals(True)
        self._view_width = width     # assigned if window size changes
        self._view_height = height   # assigned if window size changes

        self._slide_size = []
        self._num_lvl = 0
        size = max([self._view_width, self._view_height])
        # calculating the number of needed levels (cuts off the small slides)
        dim = 0 if self._view_width > self._view_height else 1
        for size_slide in np.array(self._slide.level_dimensions)[0:, dim]:
            if size > size_slide:
                break
            else:
                self._num_lvl += 1

        # calculate the required size for next _slide to ensure the image fills the view, factor "2" as panning buffer
        resize_fac = 2 * np.array(self._slide.level_dimensions)[self._num_lvl, dim] / size
        level_dimensions = np.asarray([self._view_width, self._view_height])

        # calculate the size of each level
        for n in range(self._num_lvl, 0, -1):
            self._slide_size.append((level_dimensions * resize_fac).astype(int))

        # append the upper _slide with no resize factor (to display the original size on the highest level)
        self._slide_size.append(np.asarray(self._slide.level_dimensions[self._num_lvl]).astype(int))
        self._new_file = True       # ensure a new stack will be load
        self.blockSignals(False)
        self.updating_zoom_stack()

    @pyqtSlot()
    def updating_zoom_stack(self):
        """
        The function calculates a stack of images of the respective level. Each image has an identical size , leading to
        display a smaller part of the _slide with a higher resultion. To ensure a movement to the mouse position while
        zooming in, the center of each image is located along a line. This line goes through the center of the highest
        level (largest image with smallest resolution) to the mouse position on the lowest level (smallest image with
        highest resolution). Hind: Image the stack as a flipped skew pyramid with the mouse position on the top. Moving
        the mouse equals moving the top of the pyramid with a fixed bottom.
        :return: /
        """
        new_stack: Dict[int, ZoomDict] = {}  # clear stack

        # set the centers for lowest and highest level
        center_high_lvl = (np.asarray(self._slide.level_dimensions[0]) / 2).astype(int)
        center_low_lvl = self._mouse_pos

        # check if an update is necessary
        diff = np.abs(self._old_center - center_low_lvl)
        reserve = np.asarray([self._view_width, self._view_height]) / 2

        if self._new_file or\
           diff[0] > reserve[0] or\
           diff[1] > reserve[1]:  # check if new position will fit into current slides; ensure stack loads for new files
            # calculate the centers along a line with a geometrical distribution.
            # Caution: The absolut distance must be distributed to cover the case to zoom into the right-hand side
            distance = np.abs(center_high_lvl - center_low_lvl)
            distance[0] = 1 if distance[0] == 0 else distance[0]  # geometrical space cannot work with "0"
            distance[1] = 1 if distance[1] == 0 else distance[1]  # geometrical space cannot work with "0"

            # calculating the centers depending on the positions
            if center_low_lvl[0] <= center_high_lvl[0]:
                centers_x = center_low_lvl[0] + np.around(np.geomspace(0.1, distance[0], num=self._num_lvl + 1),
                                                          decimals=1)
            else:
                centers_x = center_low_lvl[0] - np.around(np.geomspace(0.1, distance[0], num=self._num_lvl + 1),
                                                          decimals=1)
            if center_low_lvl[1] <= center_high_lvl[1]:
                centers_y = center_low_lvl[1] + np.around(np.geomspace(0.1, distance[1], num=self._num_lvl + 1),
                                                          decimals=1)
            else:
                centers_y = center_low_lvl[1] - np.around(np.geomspace(0.1, distance[1], num=self._num_lvl + 1),
                                                          decimals=1)
            slide_centers = np.stack([centers_x, centers_y], axis=1)

            # update the stack with the calculated centers
            try:
                for slide_lvl in range(self._num_lvl + 1):
                    slide_pos = (slide_centers[slide_lvl, :] - self._slide_size[slide_lvl] * 2 ** slide_lvl / 2).astype(int)
                    data = np.array(self._slide.read_region(slide_pos, slide_lvl, self._slide_size[slide_lvl]).convert('RGB'))
                    new_stack.update({slide_lvl: ZoomDict(position=slide_pos, data=data)})
            except IndexError as e:
                if self._updating_slides:
                    self.update_slides.emit()  # use a signal for constant updating
                return

            # override the zoom_stack with QMutexLocker to prevent parallel reading and writing
            with QMutexLocker(self._stack_mutex):
                self._zoom_stack = new_stack

            self._old_center = center_low_lvl

        self._new_file = False
        if self._updating_slides:
            self.update_slides.emit()  # use a signal for constant updating

    def get_zoom_stack(self):
        """
        Returns the current stack of slides
        :return: _zoom_stack
        """
        # use of QMutexLocker to prevent parallel reading and writing
        with QMutexLocker(self._stack_mutex):
            return self._zoom_stack

    def get_slide_size(self, lvl: int):
        """
        Returns the size of all wanted slide level
        :return: _slide_size
        """
        return self._slide_size[lvl]

    def get_num_lvl(self):
        """
        Returns the total number of slide levels
        :return: _num_lvl
        """
        return self._num_lvl

    def get_mouse_pos(self):
        """
        Returns the currently stored mouse position.
        :return: _mouse_pos
        """
        return self._mouse_pos

    def get_status_update(self):
        """
        Returns if the update of slides is currently running
        :return: Status updating_zoom_stack (True if active)
        """
        return self._updating_slides

    def start_updating(self):
        """
        Starts updating the slides under the mouse position
        :return: /
        """
        self._updating_slides = True
        self.updating_zoom_stack()  # call it again to restart

    def stop_updating(self):
        """
        Stops the current updating of the slides under the mouse position
        :return: /
        """
        self._updating_slides = False
