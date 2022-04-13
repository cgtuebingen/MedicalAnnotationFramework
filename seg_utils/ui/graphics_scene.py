from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class ImageViewerScene(QGraphicsScene):
    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(ImageViewerScene, self).__init__(*args)
        self.b_isInitialized = False  # boolean for if a pixmap is set and everything else is set up
        self.mode = self.EDIT
        
    def is_in_drawing_mode(self) -> bool:
        """Returns true if currently in drawing mode"""
        return self.mode == self.CREATE

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for moving the mouse"""
        super(ImageViewerScene, self).mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for pressing the mouse. Handling of shape selection and of drawing for various shapes
        """
        QGraphicsScene.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event) -> None:
        QGraphicsScene.mouseReleaseEvent(self, event)
