from PyQt5.QtCore import QRectF, pyqtSignal, pyqtSlot, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QWidget

from seg_utils.config import VERTEX_SIZE
from seg_utils.ui.shape import Shape

from typing import List
from random import randint


class Canvas(QWidget):
    r"""Base drawing widget as it should be instantiated and then connected to a scene
     https://forum.qt.io/topic/93327/how-can-i-use-qpainter-to-paint-on-qgraphicsview/3
     """
    sRequestFitInView = pyqtSignal(QRectF)
    sRequestLabelListUpdate = pyqtSignal(int)

    CREATE, EDIT = 0, 1

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        self.vertex_size = VERTEX_SIZE
        self.drawNewColor = None
        self.labels = [Shape]
        self.temp_label = None
        self.pixmap = QPixmap()
        self.mode = self.EDIT
        self._painter = QPainter()

    def setPixmap(self, pixmap: QPixmap):
        r"""Sets the pixmap and resizes the Widget to the size of the pixmaps as this is just connected
        to the Scene and the image_viewer will display the scene respectively a view into the scene"""
        self.pixmap = pixmap
        self.resize(self.pixmap.size())
        self.sRequestFitInView.emit(QRectF(self.pixmap.rect()))

    def setLabels(self, labels: List[Shape]):
        """Set the labels which are drawn on the canvas"""
        self.labels = labels
        self.update()

    def setNewColor(self, color: QColor):
        """Sets the color for drawing a new item"""
        self.drawNewColor = color

    def setTempLabel(self, points: List[QPointF] = None, shape_type: str = None):
        if points and shape_type:
            self.temp_label = Shape(image_size=self.pixmap.size(),
                                    points=points,
                                    shape_type=shape_type,
                                    color=self.drawNewColor)
        else:
            self.temp_label = None

        self.update()

    def handleShapeHovered(self,  shape_idx: int, closest_vertex_shape: int, vertex_idx: int):
        """Handles both shape and vertex highlighting in one call as I then only have to update it once"""
        self.on_ResetHighlight()
        if shape_idx > -1:
            self.labels[shape_idx].isHighlighted = True
        self.handleVertexHighlighted(closest_vertex_shape, vertex_idx)
        self.update()

    def handleShapeSelected(self, shape_idx: int, closest_vertex_shape: int, vertex_idx: int):
        self.on_ResetSelected()
        if shape_idx != -1:
            self.labels[shape_idx].isSelected = True
            self.sRequestLabelListUpdate.emit(shape_idx)
        self.handleVertexSelected(closest_vertex_shape, vertex_idx)
        self.update()

    def handleVertexHighlighted(self, shape_idx: int, vertex_idx: int):
        if shape_idx != -1:
            self.labels[shape_idx].vertices.highlightedVertex = vertex_idx

    def handleVertexSelected(self, shape_idx: int, vertex_idx: int):
        if vertex_idx != -1:
            self.labels[shape_idx].vertices.selectedVertex = vertex_idx

    def on_ResetHighlight(self):
        self.labels = list(map(self.resetHighlight, self.labels))

    def on_ResetSelected(self):
        self.labels = list(map(self.resetSelection, self.labels))

    def on_ResetSelAndHigh(self):
        self.labels = list(map(self.resetHighlight, self.labels))
        self.labels = list(map(self.resetSelection, self.labels))

    @staticmethod
    def resetHighlight(label: Shape):
        r"""Resets the highlighting attribute"""
        label.isHighlighted = False
        label.vertices.highlightedVertex = -1
        return label

    @staticmethod
    def resetSelection(label: Shape):
        label.isSelected = False
        label.vertices.selectedVertex = -1
        return label

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
                _label.paint(self._painter)
        if self.temp_label:
            self.temp_label.paint(self._painter)

        self._painter.end()

