from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QPolygonF, QVector2D
from PyQt5.QtCore import QPointF, Qt, QRectF, QSize

from copy import deepcopy
from typing import Tuple, Union, List, Optional
import numpy as np
from seg_utils.config import VERTEX_SIZE, SCALING_INITIAL

from seg_utils.utils.qt import closestEuclideanDistance


class Shape(QGraphicsItem):
    def __init__(self,
                 image_size: QSize,
                 label: str = None,
                 points: List[QPointF] = [],
                 color: QColor = None,
                 shape_type: str = None,
                 flags=None,
                 group_id=None,
                 label_dict: Optional[dict] = None):
        super(Shape, self).__init__()
        self.image_size = image_size
        self.image_rect = QRectF(0, 0, self.image_size.width(), self.image_size.height())
        self.vertex_size = VERTEX_SIZE

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
        else:
            self.label = label
            _points = points
            self.shape_type = shape_type
            self.flags = flags
            self.group_id = group_id

        self._path = None  # only necessary for the temporary Polygon and trace
        self._anchorPoint = None
        self.line_color, self.brush_color = QColor(), QColor()
        self.initColor(color)
        self.selected_color = Qt.GlobalColor.white
        self.vertices = VertexCollection(_points, self.line_color, self.brush_color, self.vertex_size)

        # distinction between highlighted (hovering over it) and selecting it (click)
        self._isHighlighted = False
        self._isClosedPath = False
        self._isSelected = False
        self.initShape()

    def __repr__(self):
        return f"Shape [{self.label.capitalize()}, {self.shape_type.capitalize()}]"

    def __eq__(self, other):
        if self.vertices.vertices == other.vertices.vertices and self.label == other.label:
            return True
        else:
            return False

    @property
    def isHighlighted(self) -> bool:
        return self._isHighlighted

    @isHighlighted.setter
    def isHighlighted(self, value: bool):
        self._isHighlighted = value

    @property
    def isSelected(self) -> bool:
        return self._isSelected

    @isSelected.setter
    def isSelected(self, value: bool):
        self._isSelected = value

    @property
    def isClosedPath(self) -> bool:
        return self._isClosedPath

    @isClosedPath.setter
    def isClosedPath(self, value: bool):
        self._isClosedPath = value

    def boundingRect(self) -> QRectF:
        return self.vertices.boundingRect()

    def to_dict(self) -> Tuple[dict, str]:
        r"""Returns a dict and a string from a shape item as those can be easier serialized
        with pickle compared to own classes"""
        # TODO: maybe json serialization? Or look into how one can pickle own classes and depickle them
        dict = {'label': self.label,
                'points': [[_pt.x(), _pt.y()] for _pt in self.vertices.vertices],
                'shape_type': self.shape_type,
                'flags': self.flags,
                'group_id': self.group_id}
        return dict, self.label

    def initShape(self):
        if self.shape_type not in ['polygon', 'rectangle', 'circle', 'tempTrace', 'tempPolygon']:
            raise AttributeError("Unsupported Shape")
        # Add additional points
        if self.shape_type in ['rectangle', 'circle'] and len(self.vertices.vertices) == 2:
            self.vertices.completePoly()

        # Generate path for the temporary Shapes
        if self.shape_type in ['tempTrace', 'tempPolygon']:
            # those two require unclosed paths and therefore work on paths
            self.initPath()

    def initColor(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)

    def initPath(self):
        self._path = QPainterPath()
        self._path.moveTo(self.vertices.vertices[0])
        for _pnt in self.vertices.vertices[1:]:
            self._path.lineTo(_pnt)

    def updateColor(self, color: QColor):
        if color:
            self.line_color, self.brush_color = color, deepcopy(color)
            self.brush_color.setAlphaF(0.5)
            self.vertices.updateColor(self.line_color, self.brush_color)

    def resetAnchor(self):
        """Resets the anchor set """
        self._anchorPoint = None

    def moveVertex(self, vNum: int, newPos: QPointF):
        """Handles the movement of one vertex"""
        if self.shape_type == 'polygon':
            self.vertices.vertices[vNum] = QPointF(newPos.x(), newPos.y())
        elif self.shape_type in ['rectangle', 'circle']:
            if not self._anchorPoint:
                # this point is the anchor a.k.a the point diagonally from the selected one
                # however, as i am rebuilding the shape from there, i only need to select the anchor once and store it
                self._anchorPoint = deepcopy(self.vertices.vertices[vNum - 2])
                print("New Anchor Set")
            self.vertices.vertices = QPolygonF([self._anchorPoint, newPos])

        if self.shape_type in ['rectangle', 'circle'] and len(self.vertices.vertices) == 2:
            self.vertices.completePoly()

        self.vertices.updateSelAndHigh(np.asarray([newPos.x(), newPos.y()]))

    def moveShape(self, displacement: QPointF) -> None:
        r"""Moves the shape by the given displacement"""
        displacement = self.checkDisplacement(displacement)
        if self.shape_type in ['polygon', 'rectangle', 'circle']:
            self.vertices.vertices.translate(displacement)

    def checkDisplacement(self, displacement: QPointF) -> List[QPointF]:
        """This function checks whether the bounding rect of the current shape exceeds the image if the
        displacement is applied. If so, no displacement is applied"""
        new_br = deepcopy(self.boundingRect())
        new_br.translate(displacement.x(), displacement.y())
        if self.image_rect.contains(new_br):
            return displacement
        else:
            return QPointF(0.0, 0.0)

    def paint(self, painter: QPainter) -> None:
        if len(self.vertices.vertices) > 0:
            # SELECTION
            if self.isSelected:
                painter.setPen(QPen(self.selected_color, 1))
            else:
                painter.setPen(QPen(self.line_color, 1))  # TODO: pen width depending on the image size

            # HIGHLIGHT BRUSH
            if self.isHighlighted or self.isSelected:
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
                if self.isSelected or self.isHighlighted or self.vertices.selectedVertex != -1:
                    self.vertices.paint(painter)

    def setScaling(self, zoom: int, max_size: int):
        r"""Sets the zoom coming from the imageviewer as the vertices can be displayed with different size.
        Currently, the max size is not used but is left in for future iterations"""
        if zoom <= 5:
            _scaling = SCALING_INITIAL/zoom
        else:
            _scaling = 1
        self.vertices._scaling = _scaling

    def contains(self, point: QPointF) -> bool:
        r"""Reimplementation as the initial method for a QGraphicsItem uses the shape,
        which results in the bounding rectangle. As both tempRectangle and tempTrace do not need
        a contain method due to being an unfinished shape, no method is here for them"""

        if self.shape_type in ['rectangle', 'polygon']:
            return self.vertices.vertices.containsPoint(point, Qt.OddEvenFill)

        elif self.shape_type in ['circle']:
            # elliptic formula is (x²/a² + y²/b² = 1) so if the point fulfills the equation respectively
            # is smaller than 1, the points is inside
            rect = self.boundingRect()
            centerpoint = rect.center()
            a = rect.width()/2
            b = rect.height()/2
            value = (point.x()-centerpoint.x()) ** 2 / a ** 2 + (point.y() - centerpoint.y()) ** 2 / b ** 2
            if value <= 1:
                return True
            else:
                return False

    @staticmethod
    def toQPointFList(point_list: List[List[float]]) -> List[QPointF]:
        return [QPointF(*_pt) for _pt in point_list]

    @staticmethod
    def QPointFToList(point_list: List[QPointF]) -> List[List[float]]:
        return [[pt.x(), pt.y()] for pt in point_list]

    @staticmethod
    def QRectFToPoints(rectangle: QRectF) -> List[QPointF]:
        r"""This function returns the bounding points of a QRectF in clockwise order starting with the top left"""
        return [rectangle.topLeft(), rectangle.topRight(), rectangle.bottomRight(), rectangle.bottomLeft()]


class VertexCollection(object):
    def __init__(self, points: List[QPointF], line_color: QColor, brush_color: QColor, vertex_size):
        # i am going to save them as a polygon as it is a representation of a vector and i can access it like a matrix
        self._points = QPolygonF(points)
        self.line_color = line_color
        self.brush_color = brush_color
        self.highlight_color = Qt.GlobalColor.white
        self.vertex_size = vertex_size
        self._highlight_size = 1
        self.highlightedVertex = -1
        self.selectedVertex = -1
        self._scaling = SCALING_INITIAL

    """
    def __getitem__(self, item):
        if not isinstance(item, tuple):
            item = tuple((item,))
            # TODO: could be accelerated but most likely doesn't matter
        ret = tuple([self._points[_pt] for _pt in item])
        if len(ret) == 1:
            return ret[0]
        else:
            return ret
    """

    def __len__(self):
        return len(self._points)

    @property
    def vertices(self):
        return self._points

    @vertices.setter
    def vertices(self, value):
        self._points = value

    def paint(self, painter: QPainter):
        for _idx, _vertex in enumerate(self._points):
            qtpoint = _vertex
            painter.setPen(QPen(self.line_color, 0.5))  # TODO: width dependent on the size of the image or something
            painter.setBrush(QBrush(self.brush_color))

            if _idx == self.selectedVertex:
                painter.setBrush(QBrush(self.highlight_color))
                painter.setPen(QPen(self.highlight_color, 0.5))
                size = (self.vertex_size * self._scaling) / 2

            elif _idx == self.highlightedVertex:
                painter.setBrush(QBrush(self.highlight_color))
                size = (self.vertex_size * self._scaling) / 2
            else:
                size = self.vertex_size / 2  # determines the diagonal of the rectangle
            painter.drawRect(QRectF(qtpoint - QPointF(size, size),
                                    qtpoint + QPointF(size, size)))

    def closestVertex(self, point: np.ndarray) -> int:
        """Calculate the euclidean distance between a point and all vertices and return the index of
        the closest node to the point"""
        return closestEuclideanDistance(point, self.ListQPointF_to_Numpy(self._points))

    def isOnVertex(self, point: QPointF) -> Tuple[bool, int]:
        """Check if a point is within the closest vertex rectangle"""
        closestVertex = self.closestVertex(np.asarray([point.x(), point.y()]))
        vertexCenter = self._points[closestVertex]
        if closestVertex in [self.highlightedVertex, self.selectedVertex]:
            size = (self.vertex_size * self._scaling) / 2
        else:
            size = self.vertex_size / 2
        vertexRect = QRectF(vertexCenter - QPointF(size, size),
                            vertexCenter + QPointF(size, size))

        if vertexRect.contains(point):
            return True, closestVertex
        else:
            return False, -1

    def updateColor(self, line_color: QColor, brush_color: QColor):
        if line_color and brush_color:
            self.line_color = line_color
            self.brush_color = brush_color

    def updateSelAndHigh(self, newPos: np.ndarray):
        idx = self.closestVertex(newPos)
        self.selectedVertex = self.highlightedVertex = idx

    def boundingRect(self):
        return self._points.boundingRect()

    def completePoly(self):
        """This function generates the other bounding points of the shape"""
        self._points.insert(1, QPointF(self._points[1].x(), self._points[0].y()))
        self._points.append(QPointF(self._points[0].x(), self._points[2].y()))

    @staticmethod
    def ListQPointF_to_Numpy(point_list: List[QPointF]):
        return np.asarray([[_pt.x(), _pt.y()] for _pt in point_list])

