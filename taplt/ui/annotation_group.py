from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from typing import *
from dataclasses import dataclass

from taplt.utils.qt import colormap_rgb
from taplt.ui.shape import Shape
from taplt.ui.dialogs import NewLabelDialog, DeleteShapeMessageBox


class AnnotationGroup(QGraphicsObject):
    """ A group for managing annotation objects and their signals with a scene """
    item_highlighted = pyqtSignal(Shape)
    item_dehighlighted = pyqtSignal(Shape)
    updateShapes = pyqtSignal(list)
    shapeSelected = pyqtSignal(Shape)
    sLabelClassDeleted = pyqtSignal(str)
    sChange = pyqtSignal(int)
    sToolTip = pyqtSignal(str)

    @dataclass
    class AnnotationMode:
        EDIT: int = 0
        DRAW: int = 1

    def __init__(self):
        QGraphicsObject.__init__(self)
        self.annotations = {}  # type: Dict[int, Shape]
        self.classes = list()
        self.setAcceptHoverEvents(True)
        self.temp_shape: Shape = None
        self._num_colors = 10  # TODO: This needs to be updated based on what's in the image.
        self.color_map, new_color = colormap_rgb(n=self._num_colors)  # have a buffer for new classes
        self.draw_new_color = new_color
        self.mode = AnnotationGroup.AnnotationMode.EDIT
        self.shapeType = Shape.ShapeType.POLYGON
        self.drawing = False

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        pass

    @pyqtSlot()
    def set_drawing_to_false(self):
        self.drawing = False
        self.sToolTip.emit("")

    @pyqtSlot()
    def create_shape(self):
        if not self.drawing:
            self.drawing = True
            s = self.scene()  # type: QGraphicsScene
            self.temp_shape = Shape(image_size=QSize(int(s.width()), int(s.height())),
                                    shape_type=self.shapeType,
                                    mode=Shape.ShapeMode.CREATE,
                                    color=self.draw_new_color)
            self.add_shapes(self.temp_shape)
            self.temp_shape.drawingDone.connect(self.set_drawing_to_false)
            self.sToolTip.emit("Press right click to end the annotation.")
            self.temp_shape.grabMouse()
        else:
            pass

    def get_color_for_label(self, label_name: str):
        r"""Get a Color based on a label_name"""
        if label_name not in self.classes:
            return None
        label_index = self.classes.index(label_name)
        return self.color_map[label_index]

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
            shape.selected.connect(self.shape_selected)
            shape.deleted.connect(lambda: self.remove_shapes(shape))
            shape.mode_changed.connect(self.shape_mode_changed)
            shape.drawingDone.connect(self.set_label)
            shape.sChange.connect(self.sChange.emit)
            self.update()

    def deselect_all(self):
        """deselects all shapes"""
        for shape in self.annotations.values():
            shape.setSelected(False)

    def remove_shapes(self, shapes: Union[Shape, List[Shape]]):
        """
        Remove shapes from the group and scene if connected to one.
        :param shapes: a shape or list of shapes
        :return: None
        """
        if shapes is None:
            return
        if isinstance(shapes, Shape):
            dlg = DeleteShapeMessageBox(shapes.label)
            dlg.exec()
            if dlg.result() != QMessageBox.Ok:
                return
            shapes = [shapes]
            self.sChange.emit(1)
        ids_to_remove = []
        for shape_id in self.annotations:
            if self.annotations[shape_id] in shapes:
                ids_to_remove.append(shape_id)
                self.annotations[shape_id].deleteLater()
        [(self.annotations[x].disconnect(), self.annotations.pop(x)) for x in ids_to_remove]
        self.updateShapes.emit(list(self.annotations.values()))

    def clear(self):
        """
        Clears the group and scene of shapes
        :return:
        """
        self.remove_shapes(list(self.annotations.values()))

    def shape_selected(self):
        """gets the index of the selected shape and emits it"""
        shape = self.sender()
        for ann_id, ann in self.annotations.items():
            if ann != shape:
                ann.setSelected(False)
        self.shapeSelected.emit(shape)

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
            self.updateShapes.emit(list(self.annotations.values()))
            self.sChange.emit(0)

        # if user entered no label, remove shape
        else:
            self.remove_shapes([self.temp_shape])
            self.set_drawing_to_false()

    def set_mode(self, mode: Union[AnnotationMode, int]):
        self.mode = mode

    def set_type(self, type_of_shape: Union[Shape.ShapeType, str]):
        """
        Sets the type of the shape when an icon is clicked in the annotation toolbar
        """
        self.shapeType = type_of_shape
        

    def update_annotations(self, current_labels: List[Shape]):
        self.clear()

        # for some reason, bugs emerge when you pass the labels as a list
        for lbl in current_labels:
            self.add_shapes(lbl)
        self.updateShapes.emit(current_labels)


if __name__ == '__main__':
    from PyQt6.QtGui import *
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
        if event.button() == Qt.LeftButton:
            anno_group.create_shape()
    scene.mousePressEvent = mousePressEvent

    viewer.show()
    app.exec()
