import concurrent.futures as mp
import PIL.ImageQt as ImageQT
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import numpy as np
import os
openslide_path = os.path.abspath("../openslide/bin")
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

        self.annotationMode = False

        self.slide: OpenSlide = None
        self.filepath = None

        self.width = self.frameRect().width()
        self.height = self.frameRect().height()
        self.mouse_pos: QPointF = QPointF()

        self.panning: bool = False
        self.pan_start: QPointF = QPointF()

        self.cur_downsample: float = 0.0
        self.max_downsample: float = 0.0
        self.cur_level_zoom: float = 0.0
        self.level_downsamples = {}
        self.cur_level = 0
        self.dim_count = 0

        self.fused_image = QPixmap()
        self.painter = QPainter(self.fused_image)
        self.pixmap_item = QGraphicsPixmapItem()
        self.pixmap_item.setPixmap(self.fused_image)

    def load_slide(self, filepath: str, width: int = None, height: int = None):
        """
        Loads the currently selected slide and sets up all other parameters needed to display the image.
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
            self.width = self.frameRect().width()
            self.height = self.frameRect().height()

        self.fused_image = QPixmap(self.width * 2, self.height * 2)
        self.pixmap_item.setPixmap(self.fused_image)

        self.dim_count = self.slide.level_count
        self.level_downsamples = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        self.max_downsample = max(self.slide.level_dimensions[0][0] / self.width,
                                  self.slide.level_dimensions[0][1] / self.height)
        self.cur_downsample = self.max_downsample
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_downsample)
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]

        self.pixmap_item.moveBy(-self.width * (self.level_downsamples[self.cur_level] / self.cur_downsample),
                                -self.height * (self.level_downsamples[self.cur_level] / self.cur_downsample))

        self.update_pixmap()

    def update_pixmap(self):
        """
        This method updated the pixmap.
        It should only be called when the pixmap is moved or zoomed.
        :return: /
        """
        self.width = self.frameRect().width()
        self.height = self.frameRect().height()
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_downsample)
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]
        self.fused_image = QPixmap(self.width * 2, self.height * 2)

        max_threads = os.cpu_count()
        sqrt_thread_count = int(np.sqrt(max_threads))

        block_width_vp = int(self.width * self.cur_level_zoom / sqrt_thread_count)
        block_height_vp = int(self.height * self.cur_level_zoom / sqrt_thread_count)
        block_width_slide = int(self.width * self.cur_downsample / sqrt_thread_count)
        block_height_slide = int(self.height * self.cur_downsample / sqrt_thread_count)

        self.painter = QPainter(self.fused_image)

        with mp.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.process_image_block, i, self.mouse_pos, block_width_vp,
                                       block_height_vp, block_width_slide, block_height_slide, sqrt_thread_count)
                       for i in range(max_threads)]

            mp.wait(futures)

            self.painter.end()

            self.sendImage.emit(self.fused_image, self.level_downsamples[self.cur_level] / self.cur_downsample)

    def process_image_block(self, block_index: int, mouse_pos: QPointF, block_width_vp: int, block_height_vp: int,
                            block_width_slide: int, block_height_slide: int, sqrt_threads: int):
        """
        This method processes each block of the image.
        The number of blocks is determined by the max number of threads.

        :param block_index: The index of the block processed by the thread
        :param mouse_pos: The position of the mouse denotes the upper left corner of the slide in the viewport
        :param block_width_vp: Describes the width of the current block in viewport coordinates
        :param block_height_vp: Describes the height of the current block in viewport coordinates
        :param block_width_slide: Describes the width of the current block in slide coordinates
        :param block_height_slide: Describes the height of the current block in slide coordinates
        :param sqrt_threads: The square root of max threads, since the image is a rectangle
        :return: /
        """
        idx_width = block_index % sqrt_threads
        idx_height = block_index // sqrt_threads

        block_location = (
            idx_width * block_width_slide,
            idx_height * block_height_slide
        )

        image = self.slide.read_region(
            (int(mouse_pos.x() + block_location[0]), int(mouse_pos.y() + block_location[1])),
            self.cur_level,
            (block_width_vp, block_height_vp)
        )

        self.painter.drawPixmap(idx_width * block_width_vp,
                                idx_height * block_height_vp,
                                block_width_vp, block_height_vp, QPixmap.fromImage(ImageQT.ImageQt(image)))

    def setAnnotationMode(self, b: bool):
        self.annotationMode = b

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Updates the pixmap of the widget is resized
        :param event: event to initialize the function
        :return: /
        """
        if self.slide:
            self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        old_scaling_factor = self.cur_downsample

        scale_factor = 1.1 if event.angleDelta().y() <= 0 else 1 / 1.1
        new_scaling_factor = min(max(self.cur_downsample * scale_factor, 1), self.max_downsample)

        if new_scaling_factor == self.cur_downsample:
            return

        self.cur_downsample = new_scaling_factor
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_downsample)
        relative_scaling_factor = self.cur_downsample / self.level_downsamples[self.cur_level]

        new_pos = self.mapToScene(event.position().toPoint())
        new_pos = QPointF((new_pos.x()/self.width - 0.5) *
                          self.slide.level_dimensions[self.dim_count - self.cur_level - 1][0] * relative_scaling_factor,
                          (new_pos.y()/self.height - 0.5) *
                          self.slide.level_dimensions[self.dim_count - self.cur_level - 1][1] * relative_scaling_factor)

        self.mouse_pos += QPointF(self.width / 2 * (old_scaling_factor - self.cur_downsample),
                                  self.height / 2 * (old_scaling_factor - self.cur_downsample))
        self.mouse_pos += new_pos
        self.update_pixmap()

    def mousePressEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton and not self.annotationMode:
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
        if event.button() == Qt.MouseButton.LeftButton and not self.annotationMode:
            self.panning = False
        super(QGraphicsView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Realizes panning, if activated
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if self.panning and not self.annotationMode:
            new_pos = self.mapToScene(event.pos())
            move = self.pan_start - new_pos
            move *= 2
            self.pan_start = new_pos
            move = QPointF(move.x()/self.width*self.slide.level_dimensions[self.dim_count - self.cur_level - 1][0],
                           move.y()/self.height*self.slide.level_dimensions[self.dim_count - self.cur_level - 1][1])
            self.mouse_pos += move
            self.update_pixmap()
        super(QGraphicsView, self).mouseMoveEvent(event)