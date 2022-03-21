from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from typing import *

from seg_utils.ui.shape import Shape


class AnnotationGroup(QGraphicsObject, QGraphicsItem):
    """ A group for managing annotation objects and their signals with a scene """
    item_highlighted = pyqtSignal(Shape)
    item_dehighlighted = pyqtSignal(Shape)
    item_clicked = pyqtSignal(Shape, QGraphicsSceneMouseEvent)

    def __init__(self):
        QGraphicsObject.__init__(self)
        QGraphicsItem.__init__(self)
        self.annotations = {}  # type: Dict[int, Shape]
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def paint(self, *args):
        pass

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        for annotation in self.annotations:
            self.annotations[annotation].is_selected = self.annotations[annotation].is_highlighted
        super(AnnotationGroup, self).mousePressEvent(event)

    @pyqtSlot(int)
    def on_hover_enter(self, shape_id: int):
        self.item_highlighted.emit(self.annotations[shape_id])
        self.update()

    @pyqtSlot(int)
    def on_hover_leave(self, shape_id: int):
        self.item_dehighlighted.emit(self.annotations[shape_id])
        self.update()

    def add_shapes(self, new_shapes: Union[Shape, List[Shape]]):
        """
        Add new shapes to the group
        :param new_shapes: a single or list of new shapes to add to the group
        :return: None
        """
        if isinstance(new_shapes, Shape):
            new_shapes = [new_shapes]
        for shape in new_shapes:
            shape.setParentItem(self)
            new_id = 0 if not self.annotations else max(self.annotations.keys()) + 1
            self.annotations[new_id] = shape
            shape.hover_enter.connect(lambda: self.on_hover_enter(new_id))
            shape.hover_exit.connect(lambda: self.on_hover_leave(new_id))
            shape.clicked.connect(lambda x: self.item_clicked.emit(self.annotations[new_id], x))

    def remove_shapes(self, shapes: Union[Shape, List[Shape]]):
        """
        Remove shapes from the group and scene if connected to one.
        :param shapes: a shape or list of shapes
        :return: None
        """
        if shapes is None:
            return
        if isinstance(shapes, Shape):
            shapes = [shapes]
        ids_to_remove = []
        for shape_id in self.annotations:
            if self.annotations[shape_id] in shapes:
                ids_to_remove.append(shape_id)
                self.annotations[shape_id].setParentItem(None)
        [self.annotations.pop(x) for x in ids_to_remove]

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent, **kwargs):
        [x.hoverMoveEvent(event) for x in self.childItems()]

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent, **kwargs):
        [x.hoverEnterEvent(event) for x in self.childItems()]

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent, **kwargs):
        [x.hoverLeaveEvent(event) for x in self.childItems()]

    def clear(self):
        """
        Clears the group and scene of shapes
        :return:
        """
        self.remove_shapes(list(self.annotations.values()))
