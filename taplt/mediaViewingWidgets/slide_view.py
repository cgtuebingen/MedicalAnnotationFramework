from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from taplt.mediaViewingWidgets.slide_loader import SlideLoader


class SlideView(QGraphicsView):
    def __init__(self, *args):
        super(SlideView, self).__init__(*args)

        self._pan_start: QPointF = None   # starting point before panning
        self._panning: bool = False     # flag to enable panning

        self.setBackgroundBrush(QBrush(QColor("r")))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)
        self.annotationMode = False

    def fitInView(self) -> None:
        slide = self.items()[2].slide_handler._slide
        (width, height) = slide.dimensions
        rect = QRectF(QPointF(0, 0), QPointF(width, height))
        unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
        self.scale(1 / unity.width(), 1 / unity.height())
        view_rect = self.viewport().rect()
        scene_rect = self.transform().mapRect(rect)
        factor = min(view_rect.width() / scene_rect.width(),
                     view_rect.height() / scene_rect.height())
        self.scale(factor, factor)

    def setAnnotationMode(self, b: bool):
        self.annotationMode = b

    def wheelEvent(self, event: QWheelEvent):
        """
        Scales the image and moves into the mouse position
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        if not self.annotationMode:
            old_pos = self.mapToScene(event.position().toPoint())
            scale_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
            self.scale(scale_factor, scale_factor)
            new_pos = self.mapToScene(event.position().toPoint())
            move = new_pos - old_pos
            self.translate(move.x(), move.y())
        super(SlideView, self).wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if not self.annotationMode:
            if event.button() == Qt.MouseButton.LeftButton:
                self._panning = True
                self._pan_start = self.mapToScene(event.pos())
        super(SlideView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Disables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if not self.annotationMode:
            if event.button() == Qt.MouseButton.LeftButton:
                self._panning = False
        super(SlideView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Realizes panning, if activated
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if not self.annotationMode:
            if self._panning:
                new_pos = self.mapToScene(event.pos())
                move = new_pos - self._pan_start
                self.translate(move.x(), move.y())
                self._pan_start = self.mapToScene(event.pos())
        super(SlideView, self).mouseMoveEvent(event)
