from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import *
from typing_extensions import TypedDict
import numpy as np
from openslide import OpenSlide

class slide_view(QGraphicsView):

    def __init__(self, *args):
        super(slide_view, self).__init__(*args)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)

        self._slide: OpenSlide = None
        self.filepath = None
        self.width = self.scene().width()
        self.height = self.scene().height()
        self.panning = False
        self.pan_start = None
        self.cur_zoom: float = 0.0
        self.zoom_perc_levels = {}
        self.cur_level = 0
        desired_type = QGraphicsPixmapItem
        self.pixmap_item = self.scene().items()[0]

        #self.pixmap_item: QGraphicsPixmapItem = QGraphicsPixmapItem()
        self.mouse_pos = np.array([0, 0])

    def fitInView(self, rect, aspectratioMode = Qt.AspectRatioMode.KeepAspectRatio):
        if not self.filepath:
            RuntimeError("There was no slide set!")

        super(slide_view, self).fitInView(rect, aspectratioMode)
        self.cur_zoom = 1.0


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
        self.filepath = filepath
        if not width or not height:
            width = self.scene().views()[0].viewport().width()
            height = self.scene().views()[0].viewport().height()
        self.calculate_zoom_levels(width, height)
        self.blockSignals(False)

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
        self.blockSignals(True)
        self.width = width  # assigned if window size changes
        self.height = height  # assigned if window size changes

        dimensions = np.array(self._slide.level_dimensions)

        self.zoom_perc_levels = {i: size[0] / dimensions[0][0] for i, size in enumerate(dimensions)}

        view_up_left = self.scene().views()[0].mapToScene(int(0.02 * self.width),
                                                          int(0.02 * self.height))  # 2% buffer for frame
        view_low_right = self.scene().views()[0].mapToScene(int(0.98 * self.width),
                                                            int(0.98 * self.height))
        cur_dims = view_low_right - view_up_left

        self.cur_zoom = max(cur_dims.x()/dimensions[0][0], cur_dims.y()/dimensions[0][1])
        for i in range(len(self.zoom_perc_levels)):
            if self.zoom_perc_levels[i] <= self.cur_zoom:
                self.cur_level = i
                break

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
        self.blockSignals(False)
        # self.updating_zoom_stack()

    def check_for_update(self, mouse_pos):
        new_level = 0
        for i in range(len(self.zoom_perc_levels)):
            if self.zoom_perc_levels[i] <= self.cur_zoom:
                new_level = i
                break
        if new_level != self.cur_level:
            self.cur_level = new_level
            self.set_image(mouse_pos, self.cur_level)

    def set_image(self, location: (int, int), level: int):
        image = self._slide.read_region(location, 0, (self.width, self.height))
        q_image = QImage(image.tobytes(), image.width, image.height, QImage.Format.Format_RGBA8888)
        self.pixmap_item.resetTransform()
        self.pixmap_item.setPixmap(QPixmap(q_image))
        self.pixmap_item.setScale(2 ** self.cur_level)
        self.pixmap_item.setPos(*self.location)

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
        self.scale(scale_factor, scale_factor)
        self.cur_level *= scale_factor
        new_pos = self.mapToScene(event.position().toPoint())
        self.mouse_pos = new_pos
        new_pos_tuple = (int(new_pos.x()), int(new_pos.y()))
        self.check_for_update(new_pos_tuple)
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
            move = new_pos - self.pan_start
            self.translate(move.x(), move.y())
            self.pan_start = self.mapToScene(event.pos())
        super(QGraphicsView, self).mouseMoveEvent(event)
