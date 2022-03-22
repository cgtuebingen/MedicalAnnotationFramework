from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from seg_utils.config import VERTEX_SIZE

from typing import *
import numpy as np


class ImageViewerScene(QGraphicsScene):
    mouse_pressed = pyqtSignal(QGraphicsSceneMouseEvent)
    sRequestContextMenu = pyqtSignal(int, QPoint)
    sRequestAnchorReset = pyqtSignal(int)

    sDrawing = pyqtSignal(list, str)
    sDrawingDone = pyqtSignal(list, str)
    sMoveVertex = pyqtSignal(int, int, QPointF)
    sMoveShape = pyqtSignal(int, QPointF)

    sResetSelAndHigh = pyqtSignal()

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

    def highlighted_shape(self):
        """returns the index of the shape which is highlighted
        or -1 if no shape is currently highlighted"""
        i, shape = self.annotations.get_hovered_item()
        return i
        
    def is_in_drawing_mode(self) -> bool:
        """Returns true if currently in drawing mode"""
        return self.mode == self.CREATE

    def is_on_beginning(self, point: QPointF) -> bool:
        """Check if a point is within the area around the starting point"""
        if self.poly_points:
            vertex_center = self.poly_points[0]
            size = VERTEX_SIZE / 2
            vertex_rect = QRectF(vertex_center - QPointF(size, size),
                                 vertex_center + QPointF(size, size))

            if vertex_rect.contains(point):
                return True
            else:
                return False
        else:
            return False

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for moving the mouse"""
        if self.b_isInitialized:
            if self.is_in_drawing_mode():
                if self.shape_type in ['tempPolygon']:
                    # intermediate points are rendered but only as temporary shapes
                    # this allows the clicking for new points which are then saved
                    intermediate_points = self.poly_points + [self.check_out_of_bounds(event.scenePos())]
                    self.sDrawing.emit(intermediate_points, self.shape_type)
                else:
                    if self._startButtonPressed:
                        if self.shape_type in ['tempTrace']:
                            self.poly_points.append(self.check_out_of_bounds(event.scenePos()))
                            self.sDrawing.emit(self.poly_points, self.shape_type)
                        elif self.shape_type in ['circle', 'rectangle']:
                            self.sDrawing.emit([self.starting_point, self.check_out_of_bounds(event.scenePos())],
                                               self.shape_type)
            else:
                # Here is the handling for the highlighting (if no start button is pressed)
                # of shapes but also if one moves vertices or the entire shape
                if self._startButtonPressed:
                    # TODO: maybe change the ordering as then the vertex move has priority compared to shape move
                    # this discriminates between whether one moves the entire shape of only a vertex
                    if self.hShape != -1:
                        self.sMoveShape.emit(self.hShape, self.check_out_of_bounds(event.scenePos()) - self.last_point)
                        self.last_point = self.check_out_of_bounds(event.scenePos())
                    else:
                        self.sMoveVertex.emit(self.vShape, self.vNum, self.check_out_of_bounds(event.scenePos()))
        QGraphicsScene.mouseMoveEvent(self, event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        r"""Handle the event for pressing the mouse. Handling of shape selection and of drawing for various shapes
        """
        if self.b_isInitialized:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.is_in_drawing_mode():
                    self._startButtonPressed = True
                    self.starting_point = self.check_out_of_bounds(event.scenePos())
                    if self.shape_type in ['tempPolygon']:
                        if self.is_on_beginning(self.starting_point) and len(self.poly_points) > 1:
                            self.set_closed_path()
                        else:
                            self.poly_points.append(self.starting_point)
                            self.sDrawing.emit(self.poly_points, self.shape_type)
                else:
                    self._startButtonPressed = True
                    self.starting_point = self.check_out_of_bounds(event.scenePos())
                    self.last_point = self.starting_point

            elif event.button() == Qt.MouseButton.RightButton:
                # Context Menu
                if not self.is_in_drawing_mode():
                    # if user right-clicked a shape, put it in 'selected' state (makes things easier)
                    # evoke context menu
                    shape_idx, _, _ = self.is_mouse_on_shape(event)
                    self.sResetSelAndHigh.emit()
                    self.sRequestContextMenu.emit(shape_idx, event.screenPos())
        QGraphicsScene.mousePressEvent(self, event)
        self.mouse_pressed.emit(event)

    def mouseReleaseEvent(self, event) -> None:
        if self.b_isInitialized:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.is_in_drawing_mode():
                    if self.shape_type in ['circle', 'rectangle']:
                        # this ends the drawing for the above shapes
                        self._startButtonPressed = False
                        self.sDrawingDone.emit([self.starting_point,
                                                self.check_out_of_bounds(event.scenePos())],
                                               self.shape_type)
                        self.starting_point = QPointF()
                    elif self.shape_type in ['tempTrace']:
                        self.set_closed_path()
                else:
                    self.sRequestAnchorReset.emit(self.vShape)
                    self._startButtonPressed = False
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
