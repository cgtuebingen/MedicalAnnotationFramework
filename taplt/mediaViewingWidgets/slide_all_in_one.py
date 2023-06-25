import concurrent.futures as mp
import PIL.ImageQt as ImageQT

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


class Worker(QThread):
    output = pyqtSignal(int, QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.existing = False
        self.index = 0
        self.position = QPointF()
        self.width = 0
        self.height = 0
        self.cur_level = 0
        self.slide: OpenSlide = None

    def set_params(self, _index, _position, _width, _height, _level, _slide):
        self.index = _index
        self.position = _position
        self.width = _width
        self.height = _height
        self.cur_level = _level
        self.slide = _slide

    def run(self):
        block_location = (
            int((self.index % 4) * self.width),
            int((self.index // 4) * self.height)
        )
        level = self.cur_level

        image = self.slide.read_region(
            (int(self.position.x() + block_location[0]), int(self.position.y() + block_location[1])),
            level,
            (self.width, self.height)
        )
        q_image = QImage(image.tobytes(), image.width, image.height, QImage.Format.Format_RGBX8888)

        self.output.emit(self.index, q_image)

        print(self.index)

    def __del__(self):
        self.existing = True
        self.wait()


class slide_view(QGraphicsView):
    sendImage = pyqtSignal(QPixmap, float)
    blockProcessed = pyqtSignal(int, QImage)

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
        self.threads = []
        self.blockProcessed.connect(self.store_image_block)
        self.image_blocks = {}

    def fitInView(self, rect, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio):
        if not self.filepath:
            RuntimeError("There was no slide set!")
        super(slide_view, self).fitInView(rect, aspect_ratio_mode)
        self.cur_scaling_factor = max(self.dimensions[0][0]/self.width, self.dimensions[0][1]/self.height)
        self.max_scaling_factor = self.cur_scaling_factor

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

        self.dimensions = np.array(self.slide.level_dimensions)
        self.dim_count = self.slide.level_count

        self.fitInView(rect)
        self.down_sample_factors = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        self.check_for_update((0, 0))

    def check_for_update(self, mouse_pos):
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_scaling_factor)
        self.relative_scaling_factor = self.cur_scaling_factor / self.down_sample_factors[self.cur_level]
        block_width = int(self.width * self.relative_scaling_factor / 4)
        block_height = int(self.height * self.relative_scaling_factor / 4)
        block_offset_width = int(self.width * self.cur_scaling_factor / 4)
        block_offset_height = int(self.height * self.cur_scaling_factor / 4)

        self.threads = []
        parameters = []

        with mp.ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            for i in range(16):
                future = executor.submit(self.process_image_block, i, self.mouse_pos, block_width,
                                         block_height, block_offset_width, block_offset_height)
                futures.append(future)

            for future in mp.as_completed(futures):
                _index, result = future.result()
                self.image_blocks[_index] = result

            self.stitch_image()

    def process_image_block(self, block_index, mouse_pos, block_width, block_height, block_offset_width, block_offset_height):
        block_location = (
            int((block_index % 4) * block_offset_width),
            int((block_index // 4) * block_offset_height)
        )

        image = self.slide.read_region(
            (int(mouse_pos.x() + block_location[0]), int(mouse_pos.y() + block_location[1])),
            self.cur_level,
            (block_width, block_height)
        )
        return block_index, image

    @pyqtSlot(int, QImage)
    def store_image_block(self, index, image):
        self.image_blocks[index] = image
        print('executed')

    def stitch_image(self):
        # Check if all threads have finished
        width = int(self.width * self.relative_scaling_factor)
        height = int(self.height * self.relative_scaling_factor)
        # Create a new QImage with the dimensions of the first image
        fused_image = QPixmap(width, height)

        # Create a QPainter object to draw on the fused image
        painter = QPainter(fused_image)

        # Iterate over the image list and draw each image onto the fused image
        for i in range(len(self.image_blocks)):
            image = self.image_blocks[i]
            print(type(image))
            painter.drawPixmap((i % 4) * int(width/4), (i // 4) * int(height/4),
                              int(width/4), int(height/4), QPixmap.fromImage(ImageQT.ImageQt(self.image_blocks[i])))

        painter.end()  # End painting

        # Emit the fused image
        self.sendImage.emit(fused_image, self.down_sample_factors[self.cur_level] / self.cur_scaling_factor)

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
        new_pos = QPointF((new_pos.x() - self.width/2.0)/self.width *
                          self.dimensions[self.dim_count - self.cur_level - 1][0] * relative_scaling_factor,
                          (new_pos.y() - self.height/2.0)/self.height *
                          self.dimensions[self.dim_count - self.cur_level - 1][1] * relative_scaling_factor)
        self.mouse_pos += QPointF(self.width/2 * (old_scaling_factor - self.cur_scaling_factor),
                                  self.height/2 * (old_scaling_factor - self.cur_scaling_factor))
        self.mouse_pos += new_pos
        new_pos_tuple = (int(self.mouse_pos.x()), int(self.mouse_pos.y()))
        self.check_for_update(new_pos_tuple)

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
            self.mouse_pos += QPointF(move.x()/self.width*self.dimensions[self.dim_count - self.cur_level - 1][0],
                                      move.y()/self.height*self.dimensions[self.dim_count - self.cur_level - 1][1])
            new_pos_tuple = (int(self.mouse_pos.x()), int(self.mouse_pos.y()))
            self.check_for_update(new_pos_tuple)
        super(QGraphicsView, self).mouseMoveEvent(event)
