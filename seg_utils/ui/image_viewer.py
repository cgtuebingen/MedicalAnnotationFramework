from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtGui import *
from PyQt5.QtCore import *

PLACEHOLDER_TEXT = "No files to display"


class ImageViewer(QGraphicsView):
    def __init__(self, *args):
        super(ImageViewer, self).__init__(*args)
        self.b_isEmpty = True

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)

        # Protected Item
        self._scaling_factor = 5 / 4
        self._enableZoomPan = False

    def fitInView(self, rect: QRectF, mode: Qt.AspectRatioMode = Qt.AspectRatioMode.IgnoreAspectRatio) -> None:
        if not rect.isNull():
            self.setSceneRect(rect)
            if not self.b_isEmpty:
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                view_rect = self.viewport().rect()
                scene_rect = self.transform().mapRect(rect)
                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())
                self.scale(factor, factor)

    def resizeEvent(self, event: QResizeEvent) -> None:
        bounds = self.scene().itemsBoundingRect()
        self.fitInView(bounds, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        """Responsible for Zoom.Redefines base function"""
        if not self.b_isEmpty:
            if self._enableZoomPan:
                factor = self._scaling_factor if event.angleDelta().y() > 0 else 1/self._scaling_factor
                self.scale(factor, factor)

    def keyPressEvent(self, event) -> None:
        if not self.b_isEmpty:
            if event.key() == Qt.Key.Key_Control:
                self._enableZoomPan = True
                self.setDragMode(QGraphicsView.ScrollHandDrag)

    def keyReleaseEvent(self, event) -> None:
        if not self.b_isEmpty:
            if event.key() == Qt.Key.Key_Control:
                self._enableZoomPan = False
                self.setDragMode(QGraphicsView.NoDrag)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.b_isEmpty:
            painter = QPainter(self.viewport())
            painter.save()
            col = self.palette().placeholderText().color()
            painter.setPen(col)
            fm = self.fontMetrics()
            elided_text = fm.elidedText(
                PLACEHOLDER_TEXT, Qt.ElideRight, self.viewport().width()
            )
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, elided_text)
            painter.restore()