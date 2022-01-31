from PyQt5.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QPoint

from seg_utils.config import VERTEX_SIZE

from typing import Tuple
import numpy as np


class ImageViewerScene(QGraphicsScene):
    sShapeHovered = pyqtSignal(int, int, int)
    sShapeSelected = pyqtSignal(int, int, int)

    sRequestContextMenu = pyqtSignal(int, QPoint)
    sRequestAnchorReset = pyqtSignal(int)

    sDrawing = pyqtSignal(list, str)
    sDrawingDone = pyqtSignal(list, str)
    sMoveVertex = pyqtSignal(int, int, QPointF)
    sMoveShape = pyqtSignal(int, QPointF)

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
        pixmap_size = self.items()[0].widget().pixmap.size()
        pixmap_size = np.array((pixmap_size.width(), pixmap_size.height()))
        scene_pos = np.clip(np.array((scene_pos.x(), scene_pos.y())), np.array((0, 0)), pixmap_size)
        return QPointF(scene_pos[0], scene_pos[1])
        
    def is_in_drawing_mode(self) -> bool:
        """Returns true if currently in drawing mode"""
        return self.mode == self.CREATE

    def is_mouse_on_shape(self, event: QGraphicsSceneMouseEvent) -> Tuple[int, int, int]:
        r"""Check if event position is within the boundaries of a shape

            :param event: Mouse Event on scene
            :returns: hovered shape index, closest shape index, vertex index
        """
        selected_shape = -1
        is_on_vertex = []
        closest_vertex = []
        # only contains one item which is the proxy item aka the canvas
        for _item_idx, _item in enumerate(self.items()[0].widget().labels):
            # Check if it is in the shape
            if _item.contains(event.scenePos()):
                selected_shape = _item_idx
            _isOnVert, _cVert = _item.vertices.isOnVertex(event.scenePos())
            is_on_vertex.append(_isOnVert)
            closest_vertex.append(_cVert)
        # check if any of them are True, i.e. the vertex is highlighted
        if any(is_on_vertex):
            return selected_shape, int(np.argmax(is_on_vertex)), closest_vertex[np.argmax(is_on_vertex)]
        else:
            return selected_shape, -1, -1

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
                else:
                    self.hShape, self.vShape, self.vNum = self.is_mouse_on_shape(event)
                    self.sShapeHovered.emit(self.hShape, self.vShape, self.vNum)

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
                    self.hShape, self.vShape, self.vNum = self.is_mouse_on_shape(event)
                    self.sShapeSelected.emit(self.hShape, self.vShape, self.vNum)

            elif event.button() == Qt.MouseButton.RightButton:
                # Context Menu
                if not self.is_in_drawing_mode():
                    sel_shape = self.selected_shape()
                    self.sRequestContextMenu.emit(sel_shape, event.screenPos())

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

    def selected_shape(self):
        """returns the index of the shape which is highlighted
           or -1 if no shape is currently highlighted"""
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
