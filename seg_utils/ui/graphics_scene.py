from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np


class ImageViewerScene(QGraphicsScene):
    mouse_pressed = pyqtSignal(QGraphicsSceneMouseEvent)
    sRequestContextMenu = pyqtSignal(int, QPoint)

    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(ImageViewerScene, self).__init__(*args)
        self.b_isInitialized = False  # boolean for if a pixmap is set and everything else is set up
        self.mode = self.EDIT
        self.shape_type = None
        self.starting_point = QPointF()  # point upon click
        self.last_point = QPointF()  # necessary for moving the shapes as it stores the previous pos
        self._startButtonPressed = False  # whether the left button was clicked
        self.poly_points = []  # list of points for the polygon drawing

        # this is for highlighting
        self.hShape = -1
        self.vShape = -1
        self.vNum = -1

    def check_out_of_bounds(self, scene_pos: QPointF) -> QPointF:
        """Returns the corrected scene pos which is limited by the boundaries of the image"""
        rect = self.itemsBoundingRect()  # type: QRect
        pixmap_size = np.array((rect.width(), rect.height()))
        scene_pos = np.clip(np.array((scene_pos.x(), scene_pos.y())), np.array((0, 0)), pixmap_size)
        return QPointF(scene_pos[0], scene_pos[1])
        
    def is_in_drawing_mode(self) -> bool:
        """Returns true if currently in drawing mode"""
        return self.mode == self.CREATE

    # def is_on_beginning(self, point: QPointF) -> bool:
    #     """Check if a point is within the area around the starting point"""
    #     if self.poly_points:
    #         vertex_center = self.poly_points[0]
    #         size = VERTEX_SIZE / 2
    #         vertex_rect = QRectF(vertex_center - QPointF(size, size),
    #                              vertex_center + QPointF(size, size))
    #
    #         if vertex_rect.contains(point):
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for moving the mouse"""
        super(ImageViewerScene, self).mouseMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for pressing the mouse. Handling of shape selection and of drawing for various shapes
        """
        QGraphicsScene.mousePressEvent(self, event)
        self.mouse_pressed.emit(event)

    def mouseReleaseEvent(self, event) -> None:
        QGraphicsScene.mouseReleaseEvent(self, event)

    def selected_shape(self):
        """returns the index of the shape which is selected
           or -1 if no shape is currently selected"""
        selected_shape = -1
        for _item_idx, _item in enumerate(self.items()[0].widget().labels):
            if _item.isSelected:
                selected_shape = _item_idx
        return selected_shape

    def set_closed_path(self):
        """resets the class variables and signals the draw-stop"""
        self._startButtonPressed = False
        self.sDrawingDone.emit(self.poly_points, self.shape_type)
        self.poly_points = []
        self.starting_point = QPointF()
