from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from typing import *

from seg_utils.ui.shape import Shape


class AnnotationPainter(QGraphicsItemGroup):
    def __init__(self):
        super(AnnotationPainter, self).__init__()

        self.annotations = []  # type: List[Shape]

    def add_shapes(self, new_shapes: Union[Shape, List[Shape]]):
        if isinstance(new_shapes, Shape):
            new_shapes = [new_shapes]
        for shape in new_shapes:
            self.addToGroup(shape)

    def clear(self):
        for shape in self.childItems():
            self.removeFromGroup(shape)