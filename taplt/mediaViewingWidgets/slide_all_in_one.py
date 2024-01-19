import concurrent.futures as mp
import PIL.ImageQt as ImageQT
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import numpy as np
import os
import sys
if sys.platform.startswith("win"):
    openslide_path = os.path.abspath("../openslide/bin")
    os.add_dll_directory(openslide_path)
from openslide import OpenSlide


class slide_view(QGraphicsView):
    sendPixmap = pyqtSignal(QGraphicsPixmapItem)

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

        self.anchor_point = QPoint()
        self.image_patches = {}

        self.max_threads = 16  # os.cpu_count()
        self.sqrt_thread_count = int(np.sqrt(self.max_threads))

        self.zoomed = True

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

        self.fused_image = QPixmap(self.width * 4, self.height * 4)
        self.pixmap_item.setPixmap(self.fused_image)

        self.dim_count = self.slide.level_count
        self.level_downsamples = [self.slide.level_downsamples[level] for level in range(self.slide.level_count)]

        self.max_downsample = self.cur_downsample = max(self.slide.level_dimensions[0][0] / self.width,
                                                        self.slide.level_dimensions[0][1] / self.height)
        self.cur_level = self.slide.get_best_level_for_downsample(self.max_downsample)
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]

        self.pixmap_item.setPos(-self.width / self.cur_level_zoom, -self.height / self.cur_level_zoom)
        self.pixmap_item.setScale(1 / self.cur_level_zoom)

        self.anchor_point = QPoint(0, 0)

        self.image_patches = {i: QPixmap(self.width, self.height) for i in range(self.max_threads)}
        self.image_patches = np.array(list(self.image_patches.values()))
        self.image_patches = self.image_patches.reshape([self.sqrt_thread_count, self.sqrt_thread_count])

        self.zoomed = True

        self.update_pixmap()
        self.sendPixmap.emit(self.pixmap_item)

    def update_pixmap(self):
        """
        This method updated the pixmap.
        It should only be called when the pixmap is moved or zoomed.
        :return: /
        """
        self.width = self.frameRect().width()
        self.height = self.frameRect().height()

        patch_width_pix = int(self.width)
        patch_height_pix = int(self.height)
        patch_width_slide = int(self.get_cur_patch_width())
        patch_height_slide = int(self.get_cur_patch_height())

        new_patches = self.check_for_new_patches()

        offset_anchor_point = self.anchor_point - QPoint(patch_width_slide, patch_height_slide)

        if any(new_patches):
            self.fused_image = QPixmap(self.width * 4, self.height * 4)
            self.fused_image.fill(0)
            self.painter = QPainter(self.fused_image)

            with mp.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = [executor.submit(self.process_image_block, i, offset_anchor_point, patch_width_pix,
                                           patch_height_pix, patch_width_slide, patch_height_slide,
                                           self.sqrt_thread_count, new_patches[i])
                           for i in range(self.max_threads)]

                mp.wait(futures)

                self.painter.end()

            self.pixmap_item.setPixmap(self.fused_image)

    def check_for_new_patches(self) -> list[bool]:
        """
        This method checks if new patches need to be loaded
        :return: This returns a list of booleans
        """
        if self.zoomed:
            self.zoomed = False
            return [True for r in range(self.max_threads)]

        else:
            grid_width = self.get_cur_patch_width()
            grid_height = self.get_cur_patch_height()

            int_mouse_pos = self.mouse_pos.toPoint()

            new_patches = [False for r in range(self.max_threads)]

            while int_mouse_pos.x() > self.anchor_point.x() + grid_width:
                self.pixmap_item.moveBy(self.get_cur_zoomed_patch_width(), 0)
                self.anchor_point += QPoint(grid_width, 0)
                new_patches[3] = True
                new_patches[7] = True
                new_patches[11] = True
                new_patches[15] = True
                self.image_patches = np.roll(self.image_patches, -1, axis=0)

            while int_mouse_pos.x() < self.anchor_point.x():
                self.pixmap_item.moveBy(-self.get_cur_zoomed_patch_width(), 0)
                self.anchor_point -= QPoint(grid_width, 0)
                new_patches[0] = True
                new_patches[4] = True
                new_patches[8] = True
                new_patches[12] = True
                self.image_patches = np.roll(self.image_patches, 1, axis=0)

            while int_mouse_pos.y() > self.anchor_point.y() + grid_height:
                self.pixmap_item.moveBy(0, self.get_cur_zoomed_patch_height())
                self.anchor_point += QPoint(0, grid_height)
                new_patches[12] = True
                new_patches[13] = True
                new_patches[14] = True
                new_patches[15] = True
                self.image_patches = np.roll(self.image_patches, -1, axis=1)

            while int_mouse_pos.y() < self.anchor_point.y():
                self.pixmap_item.moveBy(0, -self.get_cur_zoomed_patch_height())
                self.anchor_point -= QPoint(0, grid_height)
                new_patches[0] = True
                new_patches[1] = True
                new_patches[2] = True
                new_patches[3] = True
                self.image_patches = np.roll(self.image_patches, 1, axis=1)

        return new_patches

    def process_image_block(self, block_index: int, offset_anchor_point: QPointF, block_width: int, block_height: int,
                            block_width_slide: int, block_height_slide: int, sqrt_threads: int, generate_new: bool):
        """
        This method processes each block of the image.
        The number of blocks is determined by the max number of threads.

        :param block_index: The index of the block processed by the thread
        :param offset_anchor_point: The offset anchor point gives the upper left corner of the pixmap
        :param block_width: Describes the width of the current block in viewport coordinates
        :param block_height: Describes the height of the current block in viewport coordinates
        :param block_width_slide: Describes the width of the current block in slide coordinates
        :param block_height_slide: Describes the height of the current block in slide coordinates
        :param sqrt_threads: The square root of max threads, since the image is a rectangle
        :param generate_new: This is a boolean that checks if the current patch should be newly generated
        :return: /
        """
        idx_width = block_index % sqrt_threads
        idx_height = block_index // sqrt_threads

        block_location = (
            idx_width * block_width_slide,
            idx_height * block_height_slide
        )

        if generate_new:
            image = self.slide.read_region(
                (int(offset_anchor_point.x() + block_location[0]), int(offset_anchor_point.y() + block_location[1])),
                self.cur_level,
                (block_width, block_height)
            )

            self.image_patches[idx_width, idx_height] = QPixmap.fromImage(ImageQT.ImageQt(image))

        self.painter.drawPixmap(idx_width * block_width,
                                idx_height * block_height,
                                block_width, block_height, self.image_patches[idx_width, idx_height])

    def setAnnotationMode(self, b: bool):
        self.annotationMode = b

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Updates the pixmap of the widget is resized
        :param event: event to initialize the function
        :return: /
        """
        if self.slide:
            self.zoomed = True
            self.update_pixmap()

    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        old_downsample = self.cur_downsample

        old_mouse = self.get_mouse_vp(event)
        mouse_vp = event.position()

        scale_factor = 1.1 if event.angleDelta().y() <= 0 else 1 / 1.1
        new_downsample = min(max(self.cur_downsample * scale_factor, 0.3), self.max_downsample)

        if new_downsample == old_downsample:
            return

        if self.cur_level != self.slide.get_best_level_for_downsample(new_downsample):
            self.zoomed = True

        self.cur_downsample = new_downsample
        self.cur_level = self.slide.get_best_level_for_downsample(self.cur_downsample)
        self.cur_level_zoom = self.cur_downsample / self.level_downsamples[self.cur_level]

        self.mouse_pos += mouse_vp * old_downsample * (1 - scale_factor)

        self.pixmap_item.setScale(1 / self.cur_level_zoom)

        if self.zoomed:
            # TODO: This is still dependent on calling the mouse pos twice. This could be fixed by directly calculating
            #  the necessary vector. But I do not know how to calculate this vector.
            self.anchor_point = self.mouse_pos.toPoint()
            self.pixmap_item.setPos(-self.width / self.cur_level_zoom, -self.height / self.cur_level_zoom)
            old_mouse = self.get_mouse_vp(event)
            self.pixmap_item.setScale(1 / self.cur_level_zoom)
            new_mouse = self.get_mouse_vp(event)
            pix_move = (new_mouse - old_mouse) / self.cur_level_zoom
            self.pixmap_item.moveBy(pix_move.x(),
                                    pix_move.y())
        else:
            self.pixmap_item.setScale(1 / self.cur_level_zoom)

            pix_move = old_mouse * (1 - scale_factor) / self.cur_level_zoom

            self.pixmap_item.moveBy(-pix_move.x(),
                                    -pix_move.y())

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
            self.pixmap_item.moveBy(-move.x(), -move.y())
            self.pan_start = new_pos

            move = QPointF(move.x()*self.cur_downsample,
                           move.y()*self.cur_downsample)
            self.mouse_pos += move
            self.update_pixmap()
        super(QGraphicsView, self).mouseMoveEvent(event)

    def get_cur_zoomed_patch_width(self):
        """
        Utility method to calculate the current width of a patch relative to the zoom
        :return: zoomed patch width
        """
        return self.width / self.cur_level_zoom

    def get_cur_zoomed_patch_height(self):
        """
        Utility method to calculate the current height of a patch relative to the zoom
        :return: zoomed patch height
        """
        return self.height / self.cur_level_zoom

    def get_cur_patch_width(self):
        """
        Utility method to calculate the current width of a patch given by the current level
        :return: zoomed patch width
        """
        return int(self.width * self.level_downsamples[self.cur_level])

    def get_cur_patch_height(self):
        """
        Utility method to calculate the current height of a patch given by the current level
        :return: zoomed patch height
        """
        return int(self.height * self.level_downsamples[self.cur_level])

    def get_mouse_vp(self, event):
        """
        This method calculates the mouse position in the viewport relative to the position of the QPixmapItem during an
        event
        :return: mouse pos in viewport during event
        """
        top_left = - self.pixmap_item.pos()
        mouse_pos = event.position()
        return (top_left + mouse_pos) * self.cur_level_zoom
