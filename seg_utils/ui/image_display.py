from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from seg_utils.ui.image_viewer import ImageViewer
from seg_utils.ui.graphics_scene import ImageViewerScene
from seg_utils.ui.shape import Shape
from seg_utils.ui.annotation_painter import AnnotationGroup

from typing import List


class ImageDisplay(QWidget):
    """class to manage the central display in the GUI
    controls a QGraphicsView and a QGraphicsScene for drawing """

    sRequestLabelListUpdate = pyqtSignal(int)
    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(ImageDisplay, self).__init__(*args)

        # main components of the display
        self.scene = ImageViewerScene()
        self.image_viewer = ImageViewer(self.scene)

        self.pixmap = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap)
        self.annotations = AnnotationGroup(scene=self.scene)

        # put the viewer in the ImageDisplay-Frame
        self.image_viewer.setFrameShape(QFrame.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.image_viewer)

        self.labels = []  # type: List[Shape]
        self.temp_label = None  # type: Shape
        self.draw_new_color = None  # type: QColor

    def clear(self):
        """This function deletes all currently stored labels
        and triggers the image_viewer to display a default image"""
        self.scene.b_isInitialized = False
        self.image_viewer.b_isEmpty = True
        self.scene.clear()
        self.set_labels([])

    def get_pixmap_dimensions(self):
        return [self.pixmap.pixmap().width(), self.pixmap.pixmap().height()]

    def init_image(self, pixmap: QPixmap, labels):
        self.pixmap.setPixmap(pixmap)
        self.set_labels(labels)

    def is_empty(self):
        return self.image_viewer.b_isEmpty

    def set_initialized(self):
        self.scene.b_isInitialized = True
        self.image_viewer.b_isEmpty = False

    def set_labels(self, labels: List[Shape]):
        self.annotations.clear()
        self.annotations.add_shapes(labels)

    def set_mode(self, mode: int):
        assert mode in [self.CREATE, self.EDIT]
        self.scene.mode = mode

    def set_shape_type(self, shape_type):
        self.scene.shape_type = shape_type

    def set_temp_label(self, points: List[QPointF] = None, shape_type: str = None):
        if points and shape_type:
            self.temp_label = Shape(image_size=self.pixmap.pixmap().size(),
                                    points=points,
                                    shape_type=shape_type,
                                    color=self.draw_new_color)
            self.annotations.add_shapes(self.temp_label)
        else:
            self.annotations.remove_shapes(self.temp_label)
            self.temp_label = None
