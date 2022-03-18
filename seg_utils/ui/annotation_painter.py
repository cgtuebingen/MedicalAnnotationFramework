from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from typing import *

from seg_utils.ui.shape import Shape


class AnnotationGroup(QObject):
    item_highlighted = pyqtSignal(Shape)
    item_dehighlighted = pyqtSignal(Shape)
    item_clicked = pyqtSignal(Shape, QGraphicsSceneMouseEvent)

    def __init__(self, scene: QGraphicsScene = None):
        QObject.__init__(self)
        self.annotations = {}  # type: Dict[int, Shape]
        self.highlighted_item = None  # type: Shape
        self.scene = scene  # type: QGraphicsScene

    def set_scene(self, scene: QGraphicsScene):
        shapes = []
        if self.scene:
            shapes = self.annotations.values()
            self.remove_shapes(shapes)

        self.scene = scene
        self.add_shapes(shapes)

    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def paint(self, *args):
        pass

    @pyqtSlot(int)
    def on_hover_enter(self, shape_id: int):
        self.item_highlighted.emit(self.annotations[shape_id])

    @pyqtSlot(int)
    def on_hover_leave(self, shape_id: int):
        self.item_dehighlighted.emit(self.annotations[shape_id])

    def add_shapes(self, new_shapes: Union[Shape, List[Shape]]):
        """
        Add new shapes to the group
        :param new_shapes: a single or list of new shapes to add to the group
        :return: None
        """
        if isinstance(new_shapes, Shape):
            new_shapes = [new_shapes]
        for shape in new_shapes:
            if self.scene:
                self.scene.addItem(shape)
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
        if isinstance(shapes, Shape):
            shapes = [shapes]
            ids_to_remove = []
        for shape_id in self.annotations:
            if self.annotations[shape_id] in shapes:
                ids_to_remove.append(shape_id)
                if self.scene:
                    self.scene.removeItem(self.annotations[shape_id])
        [self.annotations.pop(x) for x in ids_to_remove]

    def clear(self):
        """
        Clears the group and scene of shapes
        :return:
        """
        self.remove_shapes(list(self.annotations.values()))
