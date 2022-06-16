from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from typing import *

from seg_utils.utils.qt import colormap_rgb
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs_new import NewLabelDialog


class AnnotationGroup(QGraphicsObject):
    """ A group for managing annotation objects and their signals with a scene """
    item_highlighted = pyqtSignal(Shape)
    item_dehighlighted = pyqtSignal(Shape)
    # item_clicked = pyqtSignal(Shape, QGraphicsSceneMouseEvent)
    shapeCreated = pyqtSignal(list)
    shapeSelected = pyqtSignal(int)

    def __init__(self):
        QGraphicsObject.__init__(self)
        self.annotations = {}  # type: Dict[int, Shape]
        self.classes = list()
        self.setAcceptHoverEvents(True)
        self.temp_shape: Shape = None
        self._num_colors = 10  # TODO: This needs to be updated based on what's in the image.
        self.color_map, new_color = colormap_rgb(n=self._num_colors)  # have a buffer for new classes
        self.draw_new_color = new_color

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        pass

    @pyqtSlot()
    def create_shape(self):
        s = self.scene()  # type: QGraphicsScene
        self.temp_shape = Shape(image_size=QSize(s.width(), s.height()),
                                shape_type='tempTrace',
                                mode=Shape.ShapeMode.CREATE,
                                color=self.draw_new_color)
        self.add_shapes(self.temp_shape)
        self.temp_shape.grabMouse()

    def get_color_for_label(self, label_name: str):
        r"""Get a Color based on a label_name"""
        if label_name not in self.classes:
            return None
        label_index = self.classes.index(label_name)
        return self.color_map[label_index]

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
            shape.setParentItem(self)
            new_id = 0 if not self.annotations else max(self.annotations.keys()) + 1
            self.annotations[new_id] = shape
            shape.hover_enter.connect(lambda: self.on_hover_enter(new_id))
            shape.hover_exit.connect(lambda: self.on_hover_leave(new_id))
            # shape.clicked.connect(lambda x: self.item_clicked.emit(self.annotations[new_id], x))
            shape.selected.connect(self.shape_selected)
            shape.deleted.connect(lambda: self.remove_shapes(shape))
            shape.mode_changed.connect(self.shape_mode_changed)
            shape.drawingDone.connect(self.set_label)
            self.update()

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
        [(self.annotations[x].disconnect(), self.annotations.pop(x)) for x in ids_to_remove]

    def clear(self):
        """
        Clears the group and scene of shapes
        :return:
        """
        self.remove_shapes(list(self.annotations.values()))
        self.temp_shape = None

    def shape_selected(self):
        """gets the index of the selected shape and emits it"""
        shape = self.sender()
        result = -1
        for ann_id, ann in self.annotations.items():
            if ann == shape:
                result = ann_id
            else:
                ann.setSelected(False)
        self.shapeSelected.emit(result)

    def label_selected(self, idx: int):
        """sets the annotation with the corresponding index selected"""
        for annotation in self.annotations.values():
            annotation.setSelected(False)
        self.annotations[idx].setSelected(True)

    @pyqtSlot(int)
    def shape_mode_changed(self, mode: Union[int, Shape.ShapeMode]):
        shape = self.sender()  # type: Shape
        if mode == Shape.ShapeMode.FIXED:
            shape.update_color(self.color_map[shape.group_id])

    def set_label(self):
        """
        opens a dialog to let user enter a label
        :return: None
        """
        dlg = NewLabelDialog(self.classes, self.color_map)
        dlg.exec()
        label = dlg.result

        # set the label, add to classes if necessary
        if label:
            if label not in self.classes:
                self.classes.append(label)
            self.temp_shape.group_id = self.classes.index(label)
            self.temp_shape.label = label
            self.temp_shape.set_mode(Shape.ShapeMode.FIXED)
            self.shapeCreated.emit(list(self.annotations.values()))

        # if user entered no label, remove shape
        else:
            self.remove_shapes(self.temp_shape)
            self.scene().removeItem(self.temp_shape)


if __name__ == '__main__':
    from PyQt5.QtGui import *
    import numpy as np
    from PIL.ImageQt import ImageQt
    from PIL import Image

    app = QApplication([])
    scene = QGraphicsScene()
    viewer = QGraphicsView(scene)

    anno_group = AnnotationGroup()
    pixmap = QPixmap.fromImage(ImageQt(Image.fromarray(np.random.randint(0, 150, (400, 600), np.uint8))))
    scene.addItem(QGraphicsPixmapItem(pixmap))
    scene.addItem(anno_group)

    def mousePressEvent(event):
        anno_group.create_shape()
    scene.mousePressEvent = mousePressEvent

    viewer.show()
    app.exec()
