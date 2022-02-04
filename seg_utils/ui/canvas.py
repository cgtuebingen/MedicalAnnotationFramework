from PyQt5.QtCore import QRectF, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QWidget

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
        self.labels = [Shape]
        self.temp_label = None
        self.pixmap = QPixmap()
        self._painter = QPainter()

    def set_pixmap(self, pixmap: QPixmap):
        """Sets the pixmap and resizes the Widget to the size of the pixmap as this is just connected
        to the Scene and the image_viewer will display the scene respectively a view into the scene"""
        self.pixmap = pixmap
        self.resize(self.pixmap.size())
        self.sRequestFitInView.emit(QRectF(self.pixmap.rect()))

    def paintEvent(self, event) -> None:
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        self._painter.begin(self)
        self._painter.setRenderHint(QPainter.Antialiasing)
        self._painter.setRenderHint(QPainter.HighQualityAntialiasing)
        self._painter.setRenderHint(QPainter.SmoothPixmapTransform)
        self._painter.drawPixmap(0, 0, self.pixmap)
        if self.labels:
            for _label in self.labels:
                _label.paint(painter=self._painter)
        if self.temp_label:
            self.temp_label.paint(self._painter)

        self._painter.end()
