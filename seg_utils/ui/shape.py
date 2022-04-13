from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from dataclasses import dataclass
import math
from copy import deepcopy
from typing import *
import numpy as np
from seg_utils.config import VERTEX_SIZE, SCALING_INITIAL

from seg_utils.utils.qt import closest_euclidean_distance


class Shape(QGraphicsObject):
    # TODO: Maybe we should make these QGraphicsItems again to reduce overhead.
    hover_enter = pyqtSignal()
    hover_exit = pyqtSignal()
    clicked = pyqtSignal(QGraphicsSceneMouseEvent)
    selected = pyqtSignal()
    deselected = pyqtSignal()
    mode_changed = pyqtSignal(int)
    deleted = pyqtSignal()

    @dataclass
    class ShapeMode:
        FIXED: int = 0
        EDIT: int = 1
        CREATE: int = 2

    @dataclass
    class ShapeType:
        POLYGON: str = 'polygon'
        RECTANGLE: str = 'rectangle'
        CIRCLE: str = 'circle'

    def __init__(self,
                 image_size: QSize,
                 label: str = None,
                 points: List[QPointF] = None,
                 color: QColor = None,
                 shape_type: str = None,
                 flags=None,
                 group_id=None,
                 label_dict: Optional[dict] = None,
                 mode: ShapeMode = ShapeMode.FIXED):
        super(Shape, self).__init__()

        _points = points if points else []
        self.image_size = image_size
        self.image_rect = QRectF(0, 0, self.image_size.width(), self.image_size.height())
        self.vertex_size = VERTEX_SIZE
        self.mode = mode
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # prioritize label dict
        if label_dict:
            if 'label' in label_dict:
                self.label = label_dict['label']
            if 'points' in label_dict:
                _points = [QPointF(_pt[0], _pt[1]) for _pt in label_dict['points']]
            if 'shape_type' in label_dict:
                self.shape_type = label_dict['shape_type']
            if 'flags' in label_dict:
                self.flags = label_dict['flags']
            if 'group_id' in label_dict:
                self.group_id = label_dict['group_id']
            if 'comment' in label_dict:
                self.comment = label_dict['comment']
        else:
            self.label = label
            self.shape_type = shape_type
            self.flags = flags
            self.group_id = group_id
            self.comment = ""

        self._path = None  # only necessary for the temporary Polygon and trace
        self._anchorPoint = None
        self.line_color, self.brush_color = QColor(), QColor()
        self.init_color(color)
        self.selected_color = Qt.GlobalColor.white
        self.vertices = VertexCollection(_points, self.line_color, self.brush_color, self.vertex_size)

        # distinction between highlighted (hovering over it) and selecting it (click)
        self._isHighlighted = False
        self._isClosedPath = False
        self.init_shape()
        self.scene_size: Tuple[float, float] = (1e7, 1e7)
        self.set_mode(mode)

    def set_mode(self, mode: Union[ShapeMode, int]):
        self.mode = mode
        if self.mode == Shape.ShapeMode.EDIT:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)

        if self.mode == Shape.ShapeMode.CREATE:
            self.setSelected(True)
        self.mode_changed.emit(self.mode)

    def clip_to_scene(self, scene_pos: QPointF) -> QPointF:
        rect = self.scene().itemsBoundingRect()  # type: QRect
        pixmap_size = np.array((rect.width(), rect.height()))
        scene_pos = np.clip(np.array((scene_pos.x(), scene_pos.y())), np.array((0, 0)), pixmap_size)
        return QPointF(scene_pos[0], scene_pos[1])

    def sceneEvent(self, event: QEvent) -> bool:
        return super(Shape, self).sceneEvent(event)

    @pyqtSlot(QGraphicsSceneMouseEvent)
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.mode == Shape.ShapeMode.CREATE:
            if len(self.vertices.vertices) > 0:
                delta = self.vertices.vertices[-1] - event.scenePos()
            else:
                delta = event.scenePos()
            if math.sqrt(delta.x() ** 2 + delta.y() ** 2) > 3:
                self.vertices.vertices.append(self.check_out_of_bounds(event.scenePos()))
                self.update()
        super(Shape, self).mouseMoveEvent(event)

    def check_out_of_bounds(self, pos: QPointF):
        scene_pos = np.clip(np.array((pos.x(), pos.y())),
                            np.array((0, 0)),
                            (self.image_size.width(), self.image_size.height()))
        return QPointF(scene_pos[0], scene_pos[1])

    @pyqtSlot(QGraphicsSceneMouseEvent)
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.contains(event.pos()):
            self.setSelected(True)
            self.clicked.emit(event)
        else:
            event.ignore()
        super(Shape, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.contains(event.pos()):
            self.set_mode(Shape.ShapeMode.EDIT)
        else:
            event.ignore()
        super(Shape, self).mouseDoubleClickEvent(event)

    @pyqtSlot(QGraphicsSceneMouseEvent)
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super(Shape, self).mousePressEvent(event)
        if self.mode == Shape.ShapeMode.EDIT:
            self.vertices.translate(self.pos())  # shift actual points to new location
            self.setPos(0, 0)  # reset the anchor to line up with the original origin
            self.set_mode(Shape.ShapeMode.FIXED)
        elif self.mode == Shape.ShapeMode.CREATE:
            self.set_mode(Shape.ShapeMode.FIXED)
            self.ungrabMouse()
            self.is_closed_path = True
            # TODO: base these off the actual values
            self.shape_type = 'polygon'
            self.group_id = 1

    @pyqtSlot(QGraphicsSceneHoverEvent)
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        event.ignore()
        super(Shape, self).hoverEnterEvent(event)

    @pyqtSlot(QGraphicsSceneHoverEvent)
    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.mode == Shape.ShapeMode.CREATE:
            pass
        else:
            if self.contains(event.pos()):
                if not self.is_highlighted:
                    self.is_highlighted = True
                    self.hover_enter.emit()
                    self.update()
            else:
                if self.is_highlighted:
                    self.is_highlighted = False
                    self.hover_exit.emit()
                    self.update()
        event.ignore()
        super(Shape, self).hoverMoveEvent(event)

    @pyqtSlot(QGraphicsSceneHoverEvent)
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.is_highlighted:
            self.is_highlighted = False
            self.hover_exit.emit()
            self.update()
        event.ignore()
        super(Shape, self).hoverLeaveEvent(event)

    def boundingRect(self) -> QRectF:
        if self.mode == Shape.ShapeMode.CREATE:
            # if creating the shape we need to ensure the mouse events get called, so we find the biggest boundingRect
            # in the scene. This could probably be done cleaner
            left_most = 0
            top_most = 0
            width = 0
            height = 0
            for item in self.scene().items():
                if item != self and item != self.parentItem():
                    p = item.pos()
                    r = item.boundingRect()
                    left_most = p.x() if p.x() < left_most else left_most
                    top_most = p.y() if p.y() < top_most else top_most
                    width = r.width() if r.width() > width else width
                    height = r.height() if r.height() > height else height
            return QRectF(left_most, top_most, width, height)
        return self.vertices.bounding_rect()

    def setSelected(self, selected: bool):
        QGraphicsItem.setSelected(self, selected)
        if self.isSelected():
            self.selected.emit()
        else:
            self.deselected.emit()

    def check_displacement(self, displacement: QPointF) -> QPointF:
        """This function checks whether the bounding rect of the current shape exceeds the image if the
        displacement is applied. If so, no displacement is applied"""
        new_br = deepcopy(self.boundingRect())
        new_br.translate(displacement.x(), displacement.y())
        if self.image_rect.contains(new_br):
            return displacement
        else:
            return QPointF(0.0, 0.0)

    def contains(self, point: QPointF, *args) -> bool:
        r"""Reimplementation as the initial method for a QGraphicsItem uses the shape,
        which results in the bounding rectangle. As both tempRectangle and tempTrace do not need
        a contain method due to being an unfinished shape, no method is here for them"""
        if self.shape_type in ['rectangle', 'polygon']:
            return self.vertices.vertices.containsPoint(point, Qt.OddEvenFill)

        elif self.shape_type in ['circle']:
            # elliptic formula is (x²/a² + y²/b² = 1) so if the point fulfills the equation respectively
            # is smaller than 1, the points is inside
            rect = self.boundingRect()
            center_point = rect.center()
            a = rect.width()/2
            b = rect.height()/2
            value = (point.x()-center_point.x()) ** 2 / a ** 2 + (point.y() - center_point.y()) ** 2 / b ** 2
            if value <= 1:
                return True
            else:
                return False
        return False

    def init_color(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)

    def init_path(self):
        self._path = QPainterPath()
        if self.vertices.vertices:
            self._path.moveTo(self.vertices.vertices[0])
            for _pnt in self.vertices.vertices[1:]:
                self._path.lineTo(_pnt)

    def init_shape(self):
        if self.shape_type not in ['polygon', 'rectangle', 'circle', 'tempTrace', 'tempPolygon']:
            raise AttributeError("Unsupported Shape")
        # Add additional points
        if self.shape_type in ['rectangle', 'circle'] and len(self.vertices.vertices) == 2:
            self.vertices.complete_poly()

        # Generate path for the temporary Shapes
        if self.shape_type in ['tempTrace', 'tempPolygon']:
            # those two require unclosed paths and therefore work on paths
            self.init_path()

    @property
    def is_closed_path(self) -> bool:
        return self._isClosedPath

    @is_closed_path.setter
    def is_closed_path(self, value: bool):
        self._isClosedPath = value

    @property
    def is_highlighted(self) -> bool:
        return self._isHighlighted

    @is_highlighted.setter
    def is_highlighted(self, value: bool):
        self._isHighlighted = value

    def move_vertex(self, v_num: int, new_pos: QPointF):
        """Handles the movement of one vertex"""
        if self.shape_type == 'polygon':
            self.vertices.vertices[v_num] = QPointF(new_pos.x(), new_pos.y())
        elif self.shape_type in ['rectangle', 'circle']:
            if not self._anchorPoint:
                # this point is the anchor a.k.a the point diagonally from the selected one
                # however, as i am rebuilding the shape from there, i only need to select the anchor once and store it
                self._anchorPoint = deepcopy(self.vertices.vertices[v_num - 2])
                print("New Anchor Set")
            self.vertices.vertices = QPolygonF([self._anchorPoint, new_pos])

        if self.shape_type in ['rectangle', 'circle'] and len(self.vertices.vertices) == 2:
            self.vertices.complete_poly()

        self.vertices.update_sel_and_high(np.asarray([new_pos.x(), new_pos.y()]))

    def paint(self, painter: QPainter, *args) -> None:
        if len(self.vertices.vertices) > 0:
            # SELECTION
            if self.isSelected():
                painter.setPen(QPen(self.selected_color, 1))
            else:
                painter.setPen(QPen(self.line_color, 1))  # TODO: pen width depending on the image size

            # HIGHLIGHT BRUSH
            if self.is_highlighted or self.isSelected():
                painter.setBrush(QBrush(self.brush_color))
            else:
                painter.setBrush(QBrush())

            # SHAPES DRAWING
            if self.shape_type in ['polygon', 'rectangle']:
                painter.drawPolygon(self.vertices.vertices)
                self.vertices.paint(painter)

            elif self.shape_type in ['tempTrace', 'tempPolygon']:
                painter.drawPath(self._path)
                self.vertices.paint(painter)

            elif self.shape_type == "circle":
                painter.drawEllipse(QRectF(self.vertices.vertices[0], self.vertices.vertices[2]))
                if self.isSelected or self.is_highlighted or self.vertices.selected_vertex != -1:
                    self.vertices.paint(painter)

    def to_dict(self) -> Tuple[dict, str]:
        r"""Returns a dict and a string from a shape item as those can be easier serialized
        with pickle compared to own classes"""
        # TODO: maybe json serialization? Or look into how one can pickle own classes and de-pickle them
        dictionary = {'label': self.label,
                      'points': [[_pt.x(), _pt.y()] for _pt in self.vertices.vertices],
                      'shape_type': self.shape_type,
                      'flags': self.flags,
                      'group_id': self.group_id,
                      'comment': self.comment}
        return dictionary, self.label

    def update_color(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)
            self.vertices.update_color(self.line_color, self.brush_color)


class VertexCollection(object):
    def __init__(self, points: List[QPointF], line_color: QColor, brush_color: QColor, vertex_size):
        self._points = QPolygonF(points)
        self.line_color = line_color
        self.brush_color = brush_color
        self.highlight_color = Qt.GlobalColor.white
        self.vertex_size = vertex_size
        self._highlight_size = 1
        self.highlighted_vertex = -1
        self.selected_vertex = -1
        self._scaling = SCALING_INITIAL

    def __len__(self):
        return len(self._points)

    def bounding_rect(self):
        return self._points.boundingRect()

    def translate(self, offset):
        self._points.translate(offset)

    def closest_vertex(self, point: np.ndarray) -> int:
        """Calculate the euclidean distance between a point and all vertices and return the index of
        the closest node to the point"""
        arr = np.asarray([[_pt.x(), _pt.y()] for _pt in self._points])
        return closest_euclidean_distance(point, arr)

    def complete_poly(self):
        """This function generates the other bounding points of the shape"""
        self._points.insert(1, QPointF(self._points[1].x(), self._points[0].y()))
        self._points.append(QPointF(self._points[0].x(), self._points[2].y()))

    def is_on_vertex(self, point: QPointF) -> Tuple[bool, int]:
        """Check if a point is within the closest vertex rectangle"""
        closest_vertex = self.closest_vertex(np.asarray([point.x(), point.y()]))
        vertex_center = self._points[closest_vertex]
        if closest_vertex in [self.highlighted_vertex, self.selected_vertex]:
            size = (self.vertex_size * self._scaling) / 2
        else:
            size = self.vertex_size / 2
        vertex_rect = QRectF(vertex_center - QPointF(size, size),
                             vertex_center + QPointF(size, size))

        if vertex_rect.contains(point):
            return True, closest_vertex
        else:
            return False, -1

    def paint(self, painter: QPainter):
        for _idx, _vertex in enumerate(self._points):
            qt_point = _vertex
            painter.setPen(QPen(self.line_color, 0.5))  # TODO: width dependent on the size of the image or something
            painter.setBrush(QBrush(self.brush_color))

            if _idx == self.selected_vertex:
                painter.setBrush(QBrush(self.highlight_color))
                painter.setPen(QPen(self.highlight_color, 0.5))
                size = (self.vertex_size * self._scaling) / 2

            elif _idx == self.highlighted_vertex:
                painter.setBrush(QBrush(self.highlight_color))
                size = (self.vertex_size * self._scaling) / 2
            else:
                size = self.vertex_size / 2  # determines the diagonal of the rectangle
            painter.drawRect(QRectF(qt_point - QPointF(size, size),
                                    qt_point + QPointF(size, size)))

    def update_color(self, line_color: QColor, brush_color: QColor):
        if line_color and brush_color:
            self.line_color = line_color
            self.brush_color = brush_color

    def update_sel_and_high(self, new_pos: np.ndarray):
        idx = self.closest_vertex(new_pos)
        self.selected_vertex = self.highlighted_vertex = idx

    @property
    def vertices(self) -> QPolygonF:
        return self._points

    @vertices.setter
    def vertices(self, value):
        self._points = value
