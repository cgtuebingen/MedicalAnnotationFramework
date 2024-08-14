from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QApplication, QGraphicsRectItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QWheelEvent, QBrush, QColor, QTransform


class AnnotationView(QGraphicsView):
    def __init__(self, annotations_scene: QGraphicsScene):
        super().__init__(annotations_scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setMouseTracking(True)
        self.current_view = None
        self.setStyleSheet("background: transparent;")  # Make sure the background is transparent if needed

    def set_view(self, view):
        print("Setting view")
        self.current_view = view

    def synchronize_zoom(self, global_zoom):
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        transform = QTransform(1, 0, 0,
                               0, 1, 0,
                               0, 0, 1)
        self.setTransform(transform)
        print(self.viewportTransform())
        self.translate(-self.viewportTransform().m31(), self.viewportTransform().m32())
        self.scale(1/global_zoom, 1/global_zoom)
        print(self.viewportTransform())
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    def mousePressEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Enables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Disables panning of the image
        :param event: event to initialize the function
        :type event: QMouseEvent
        :return: /
        """
        print("Hällo")
        if event.button() == Qt.MouseButton.LeftButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """
        Enables zooming of the image
        :param event: event to initialize the function
        :type event: QWheelEvent
        :return: /
        """
        # Calculate scale factor
        scale_factor = 1.1 if event.angleDelta().y() > 0 else 1.0 / 1.1

        # Get the current mouse position in the scene before scaling
        old_pos = self.mapToScene(event.position().toPoint())

        # Apply the scaling
        self.scale(scale_factor, scale_factor)

        # Get the new mouse position in the scene after scaling
        new_pos = self.mapToScene(event.position().toPoint())

        # Calculate the translation to keep the zoom centered under the mouse
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

        super().wheelEvent(event)

    def drawRectangle(self, dimensions):
        scene_rect = QGraphicsRectItem(0, 0, dimensions[0], dimensions[1])
        scene_rect.setBrush(QBrush(QColor(0, 255, 0, 128)))
        self.scene().addItem(scene_rect)
        rect_item = QGraphicsRectItem(1000, 1000, 2000, 2000)
        rect_item.setBrush(QBrush(QColor(255, 0, 0, 128)))
        self.scene().addItem(rect_item)

    def add_annotation(self, annotation):
        self.scene().addItem(annotation)

    def clear_annotations(self):
        self.scene().clear()