from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from typing import *

from seg_utils.config import VERTEX_SIZE
from seg_utils.ui.shape import Shape


class Canvas(QWidget):
    r"""Base drawing widget as it should be instantiated and then connected to a scene
     https://forum.qt.io/topic/93327/how-can-i-use-qpainter-to-paint-on-qgraphicsview/3
     """
    sRequestFitInView = pyqtSignal(QRectF)

    CREATE, EDIT = 0, 1

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        self.vertex_size = VERTEX_SIZE
        self.labels = []  # type: List[Shape]
        self.temp_label = None
        self.pixmap = QGraphicsPixmapItem()
        self._item_group = QGraphicsItemGroup()

    def add_label(self, new_label):
        self._item_group.addToGroup(new_label)

    def remove_label(self, label):
        self._item_group.removeFromGroup(label)

    def get_label_index(self, label: Shape):
        for i, item in self._item_group.childItems():
            if label == item:
                return i

    def set_labels(self, new_labels):
        for item in self._item_group.childItems():
            self._item_group.removeFromGroup(item)
        for new_label in new_labels:
            self._item_group.addToGroup(new_label)

    def set_pixmap(self, pixmap: QPixmap):
        """Sets the pixmap and resizes the Widget to the size of the pixmap as this is just connected
        to the Scene and the image_viewer will display the scene respectively a view into the scene"""
        self.pixmap.setPixmap(pixmap)
        self.sRequestFitInView.emit(QRectF(self.pixmap.boundingRect()))

    def clear(self):
        for item in self._item_group.childItems():
            self._item_group.removeFromGroup(item)
        self.pixmap.setPixmap(QPixmap())
