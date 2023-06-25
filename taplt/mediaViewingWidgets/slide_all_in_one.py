import concurrent.futures as mp
import PIL.ImageQt as ImageQT

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from threading import Thread
from typing import *
from typing_extensions import TypedDict
import numpy as np
import os
openslide_path = os.path.abspath("../../openslide/bin")
os.add_dll_directory(openslide_path)
from openslide import OpenSlide


class slide_view(QGraphicsView):
    sendImage = pyqtSignal(QPixmap, float)

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
        self.panning: bool = False
        self.pan_start: QPointF = QPointF()
        self.cur_scaling_factor: float = 0.0
        self.max_scaling_factor: float = 0.0
        self.relative_scaling_factor: float = 0.0
        self.cur_level = 0
        self.dim_count = 0
        self.mouse_pos: QPointF = QPointF()
        self.down_sample_factors = {}
        self.dimensions = {}
        self.fused_image = QPixmap()
        self.painter = QPainter(self.fused_image)
        self.pixmap_item = QGraphicsPixmapItem()

    def fitInView(self, rect, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio):
        if not self.filepath:
            RuntimeError("There was no slide set!")
        super(slide_view, self).fitInView(rect, aspect_ratio_mode)

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
        self.mouse_pos = QPointF(0, 0)

        if not width or not height:
            self.width = self.scene().views()[0].viewport().width()
            self.height = self.scene().views()[0].viewport().height()

        rect = QRectF(QPointF(0, 0), QSizeF(self.width, self.height))

        self.fused_image = QPixmap(self.width * 2, self.height * 2)
        self.pixmap_item.setPixmap(self.fused_image)

        self.dimensions = np.array(self.slide.level_dimensions)
        self.dim_count = self.slide.level_count

        self.down_sample_factors = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        self.fitInView(rect)

        self.cur_scaling_factor = max(self.dimensions[0][0] / self.width, self.dimensions[0][1] / self.height)
        self.max_scaling_factor = self.cur_scaling_factor
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_scaling_factor)
        self.relative_scaling_factor = self.cur_scaling_factor / self.down_sample_factors[self.cur_level]
        self.pixmap_item.moveBy(-self.width * (self.down_sample_factors[self.cur_level] / self.cur_scaling_factor),
                                -self.height * (self.down_sample_factors[self.cur_level] / self.cur_scaling_factor))

        self.check_for_update()

    def check_for_update(self):
        self.width = self.scene().views()[0].viewport().width()
        self.height = self.scene().views()[0].viewport().height()

        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_scaling_factor)
        self.relative_scaling_factor = self.cur_scaling_factor / self.down_sample_factors[self.cur_level]

        max_threads = 16
        sqrt_thread_count = int(np.sqrt(max_threads))

        block_width = int(self.width * self.relative_scaling_factor / 4)
        block_height = int(self.height * self.relative_scaling_factor / 4)
        block_offset_width = int(self.width * self.cur_scaling_factor / 4)
        block_offset_height = int(self.height * self.cur_scaling_factor / 4)

        self.painter = QPainter(self.fused_image)

        with mp.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.process_image_block, i, self.mouse_pos, block_width,
                                       block_height, block_offset_width, block_offset_height, sqrt_thread_count)
                       for i in range(max_threads)]

            mp.wait(futures)

            self.painter.end()

            self.sendImage.emit(self.fused_image, self.down_sample_factors[self.cur_level] / self.cur_scaling_factor)

    def process_image_block(self, block_index, mouse_pos, block_width, block_height, block_offset_width,
                            block_offset_height, sqrt_threads):
        idx_width = block_index % sqrt_threads
        idx_height = block_index // sqrt_threads

        block_location = (
            idx_width * block_offset_width,
            idx_height * block_offset_height
        )

        image = self.slide.read_region(
            (int(mouse_pos.x() + block_location[0]), int(mouse_pos.y() + block_location[1])),
            self.cur_level,
            (block_width, block_height)
        )

        self.painter.drawPixmap(idx_width * block_width,
                                idx_height * block_height,
                                block_width, block_height, QPixmap.fromImage(ImageQT.ImageQt(image)))



    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        old_scaling_factor = self.cur_scaling_factor

        scale_factor = 1.1 if event.angleDelta().y() <= 0 else 1 / 1.1
        new_scaling_factor = min(max(self.cur_scaling_factor * scale_factor, 1), self.max_scaling_factor)

        if new_scaling_factor == self.cur_scaling_factor:
            return

        self.cur_scaling_factor = new_scaling_factor
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_scaling_factor)
        relative_scaling_factor = self.cur_scaling_factor/self.down_sample_factors[self.cur_level]

        new_pos = self.mapToScene(event.position().toPoint())
        new_pos = QPointF((new_pos.x()/self.width - 0.5) *
                          self.dimensions[self.dim_count - self.cur_level - 1][0] * relative_scaling_factor,
                          (new_pos.y()/self.height - 0.5) *
                          self.dimensions[self.dim_count - self.cur_level - 1][1] * relative_scaling_factor)

        self.mouse_pos += QPointF(self.width/2 * (old_scaling_factor - self.cur_scaling_factor),
                                  self.height/2 * (old_scaling_factor - self.cur_scaling_factor))
        self.mouse_pos += new_pos
        self.check_for_update()

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
            move *= 2
            self.pan_start = new_pos
            move = QPointF(move.x()/self.width*self.dimensions[self.dim_count - self.cur_level - 1][0],
                           move.y()/self.height*self.dimensions[self.dim_count - self.cur_level - 1][1])
            self.mouse_pos += move
            self.check_for_update()
        super(QGraphicsView, self).mouseMoveEvent(event)