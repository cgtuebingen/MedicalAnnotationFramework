from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import *
from typing_extensions import TypedDict
import numpy as np
import os
openslide_path = os.path.abspath("../../openslide/bin")
os.add_dll_directory(openslide_path)
from openslide import OpenSlide
from openslide import OpenSlideCache

class slide_view(QGraphicsView):
    sendImage = pyqtSignal(QImage, float)

    def __init__(self, *args):
        super(slide_view, self).__init__(*args)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)

        self.slide: OpenSlide = None
        self.filepath = None
        self.width = self.scene().width()
        self.height = self.scene().height()
        self.max_dims = (0.0, 0.0)
        self.panning: bool = False
        self.pan_start: QPointF = QPointF()
        self.cur_zoom: float = 0.0
        self.zoom_perc_levels = {}
        self.cur_level = 0
        self.dim_count = 0
        self.mouse_pos: QPointF = QPointF()
        self.scene_to_slide_ratio = 0.0
        self.downsample_factors = {}
        self.dimensions = {}

    def fitInView(self, rect, aspectratioMode = Qt.AspectRatioMode.KeepAspectRatio):
        if not self.filepath:
            RuntimeError("There was no slide set!")

        super(slide_view, self).fitInView(rect, aspectratioMode)
        self.width = int(rect.width())
        self.height = int(rect.height())
        self.cur_zoom = max(self.width/self.max_dims[0], self.height/self.max_dims[1])
        self.scene_to_slide_ratio = self.cur_zoom
        self.check_for_update((0, 0))

    def load_slide(self, filepath: str, width: int = None, height: int = None):
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
        self.slide = OpenSlide(filepath)
        self.filepath = filepath
        self.mouse_pos = QPointF(self.slide.dimensions[0]/2, self.slide.dimensions[1]/2)
        if not width or not height:
            width = self.scene().views()[0].viewport().width()
            height = self.scene().views()[0].viewport().height()
        self.calculate_zoom_levels(width, height)

    def calculate_zoom_levels(self, width: int, height: int):
        """
        Calcuating the needed size of the different level based on the current window size. The resolution of the lower
        levels depend on the window size and not on the original one. Function has to be called after loading new data.
        :param width: width of the GraphicsView
        :type width: int
        :param height: height of the GraphicView
        :type height: int
        :return: /
        """
        self.width = width  # assigned if window size changes
        self.height = height  # assigned if window size changes

        self.dimensions = np.array(self.slide.level_dimensions)
        self.dim_count = self.slide.level_count
        self.max_dims = self.slide.dimensions
        self.downsample_factors = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        viewport_aspect_ratio = self.width / self.height
        slide_aspect_ratio = self.max_dims[0] / self.max_dims[1]
        desired_downsample = max(self.max_dims[0] / self.width, self.max_dims[1] / self.height)
        initial_level = min(range(self.slide.level_count),
                            key=lambda level: abs(self.downsample_factors[level] - desired_downsample))

        self.zoom_perc_levels = {}
        for i in range(len(self.dimensions) - 1, -1, -1):
            if i == len(self.dimensions) - 1:
                self.zoom_perc_levels[i] = 1.0  # Zoom percentage for lowest-resolution level
            else:
                downsampling_factor = self.dimensions[i][0] / self.dimensions[i + 1][0]
                self.zoom_perc_levels[i] = self.zoom_perc_levels[i + 1] / downsampling_factor

        view_up_left = self.scene().views()[0].mapToScene(int(0.02 * self.width),
                                                          int(0.02 * self.height))  # 2% buffer for frame
        view_low_right = self.scene().views()[0].mapToScene(int(0.98 * self.width),
                                                            int(0.98 * self.height))
        cur_dims = view_low_right - view_up_left

        self.cur_zoom = max(cur_dims.x()/self.max_dims[0], cur_dims.y()/self.max_dims[1])
        # for i in range(len(self.zoom_perc_levels)):
        #     if self.zoom_perc_levels[i] >= self.cur_zoom:
        #         self.cur_level = i
        #         break
        self.cur_level = initial_level

        self.set_image((0, 0), self.cur_level)

        # self.slide_size = []
        # self.num_lvl = 0
        # size = max([self.width, self.height])
        # # calculating the number of needed levels (cuts off the small slides)
        # dim = 0 if self.width > self.height else 1
        # for size_slide in np.array(self._slide.level_dimensions)[0:, dim]:
        #     if size > size_slide:
        #         break
        #     else:
        #         self.num_lvl += 1
        #
        # # calculate the required size for next _slide to ensure the image fills the view, factor "2" as panning buffer
        # resize_fac = 2 * np.array(self._slide.level_dimensions)[self.num_lvl, dim] / size
        # level_dimensions = np.asarray([self.width, self.height])
        #
        # # calculate the size of each level
        # for n in range(self.num_lvl, 0, -1):
        #     self.slide_size.append((level_dimensions * resize_fac).astype(int))
        #
        # # append the upper _slide with no resize factor (to display the original size on the highest level)
        # self.slide_size.append(np.asarray(self._slide.level_dimensions[self.num_lvl]).astype(int))
        # self._new_file = True  # ensure a new stack will be load
        # self.updating_zoom_stack()

    def check_for_update(self, mouse_pos):
        new_level = 0
        for i in range(len(self.zoom_perc_levels)):
            if self.zoom_perc_levels[i] >= self.cur_zoom:
                new_level = i
                break
        self.cur_level = new_level
        self.set_image(mouse_pos, self.cur_level)

    # def calculate_cur_zoom(self):
    #     view_up_left = self.scene().views()[0].mapToScene(int(0.02 * self.width),
    #                                                       int(0.02 * self.height))  # 2% buffer for frame
    #     view_low_right = self.scene().views()[0].mapToScene(int(0.98 * self.width),
    #                                                         int(0.98 * self.height))
    #     cur_dims = view_low_right - view_up_left
    #
    #     self.cur_zoom = self.cur_zoom = max(cur_dims.x()/self.max_width, cur_dims.y()/self.max_height)

    def set_image(self, location: (int, int), level: int):
        debug = self.dimensions
        image = self.slide.read_region(location, level, (self.width*3, self.height*3))
        q_image = QImage(image.tobytes(), image.width, image.height, QImage.Format.Format_RGBX8888)
        self.sendImage.emit(q_image, 1)

    def refactor_image(self):
        """
        Resets the metadata of a _slide after loading a new one or resizing the view.
        :return: /
        """
        if self.scene().views():
            scene_viewer = self.scene().views()[0].viewport()
            self.width = scene_viewer.width()
            self.height = scene_viewer.height()
            self.zoom_perc_levels = {}
            self.cur_zoom = 1

    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        old_pos = self.mapToScene(event.position().toPoint())
        scale_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        

        self.cur_zoom /= scale_factor
        self.scale(scale_factor, scale_factor)
        new_pos = self.mapToScene(event.position().toPoint())
        self.mouse_pos = new_pos
        new_pos_tuple = (int(new_pos.x()), int(new_pos.y()))
        #self.check_for_update(new_pos_tuple)
        move = new_pos - old_pos
        self.translate(move.x(), move.y())
        super(QGraphicsView, self).wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.panning = True
            self.pan_start = self.mapToScene(event.pos())
        super(QGraphicsView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Disables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.panning = False
        super(QGraphicsView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Realizes panning, if activated
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if self.panning:
            new_pos = self.mapToScene(event.pos())
            move = self.pan_start - new_pos
            self.pan_start = new_pos
            self.mouse_pos += QPointF(move.x()/self.width*self.dimensions[self.cur_level][0],
                                      move.y()/self.height*self.dimensions[self.cur_level][1])
            new_pos_tuple = (int(self.mouse_pos.x()), int(self.mouse_pos.y()))
            self.check_for_update(new_pos_tuple)
        super(QGraphicsView, self).mouseMoveEvent(event)
