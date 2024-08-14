from PySide6.QtWidgets import QGraphicsObject, QGraphicsScene, QGraphicsPixmapItem, QApplication, QGraphicsView, \
    QMessageBox
from PySide6.QtCore import Signal, Slot, QPointF, QSize, Qt
from typing import Dict, List, Union
from dataclasses import dataclass

from taplt.utils.qt import colormap_rgb
from taplt.ui.shape import Shape
from taplt.ui.dialogs import NewLabelDialog, DeleteShapeMessageBox
from taplt.utils.project_structure import Modality

class AnnotationGroup(QGraphicsObject):
    """ A group for managing annotation objects and their signals with a scene """
    item_highlighted = Signal(Shape)
    item_dehighlighted = Signal(Shape)
    updateShapes = Signal(list)
    shapeSelected = Signal(Shape)
    sLabelClassDeleted = Signal(str)
    sChange = Signal(int)
    sToolTip = Signal(str)

    @dataclass
    class AnnotationMode:
        EDIT: int = 0
        DRAW: int = 1

    def __init__(self):
        super().__init__()
        self.annotations: Dict[int, Shape] = {}
        self.classes: List[str] = []
        self.setAcceptHoverEvents(True)
        self.temp_shape: Shape = None
        self._num_colors = 10
        self.color_map, new_color = colormap_rgb(n=self._num_colors)
        self.draw_new_color = new_color
        self.mode = AnnotationGroup.AnnotationMode.EDIT
        self.shapeType = Shape.ShapeType.POLYGON
        self.drawing = False
        self.modality = None

        self._scene_offset = QPointF(0, 0)  # To keep track of scene offset

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        # Empty because this group does not need to paint itself
        pass

    @Slot()
    def set_drawing_to_false(self):
        self.drawing = False
        self.sToolTip.emit("")

    @Slot()
    def create_shape(self):
        if not self.drawing:
            self.drawing = True
            s = self.scene()  # type: QGraphicsScene
            self.temp_shape = Shape(image_size=QSize(int(s.width()), int(s.height())),
                                    shape_type=self.shapeType,
                                    mode=Shape.ShapeMode.CREATE,
                                    color=self.draw_new_color,
                                    modality=self.modality)
            self.add_shapes(self.temp_shape)
            self.temp_shape.drawingDone.connect(self.set_drawing_to_false)
            self.sToolTip.emit("Press right click to end the annotation.")
            self.temp_shape.grabMouse()
        else:
            pass

    def get_color_for_label(self, label_name: str):
        """Get a Color based on a label_name"""
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
            shape.setFlag(QGraphicsObject.ItemIgnoresTransformations)  # Ignore scene transformations
            new_id = 0 if not self.annotations else max(self.annotations.keys()) + 1
            self.annotations[new_id] = shape
            shape.selected.connect(self.shape_selected)
            shape.deleted.connect(lambda: self.remove_shapes(shape))
            shape.mode_changed.connect(self.shape_mode_changed)
            shape.drawingDone.connect(self.set_label)
            shape.sChange.connect(self.sChange.emit)
            self.update()

    def deselect_all(self):
        """Deselects all shapes"""
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
        for shape_id in ids_to_remove:
            self.annotations.pop(shape_id).disconnect()
        self.updateShapes.emit(list(self.annotations.values()))

    def clear(self):
        """Clears the group and scene of shapes"""
        self.remove_shapes(list(self.annotations.values()))

    def shape_selected(self):
        """Gets the index of the selected shape and emits it"""
        shape = self.sender()
        for ann_id, ann in self.annotations.items():
            if ann != shape:
                ann.setSelected(False)
        self.shapeSelected.emit(shape)

    @Slot(int)
    def shape_mode_changed(self, mode: Union[int, Shape.ShapeMode]):
        shape = self.sender()  # type: Shape
        if mode == Shape.ShapeMode.FIXED:
            shape.update_color(self.color_map[shape.group_id])

    def set_label(self):
        """Opens a dialog to let user enter a label"""
        dlg = NewLabelDialog(self.classes, self.color_map)
        dlg.exec()
        label = dlg.result

        # Set the label, add to classes if necessary
        if label:
            if label not in self.classes:
                self.classes.append(label)
            self.temp_shape.group_id = self.classes.index(label)
            self.temp_shape.label = label
            self.temp_shape.set_mode(Shape.ShapeMode.FIXED)
            self.updateShapes.emit(list(self.annotations.values()))
            self.sChange.emit(0)
        else:
            self.remove_shapes([self.temp_shape])
            self.set_drawing_to_false()

    def set_mode(self, mode: Union[AnnotationMode, int]):
        self.mode = mode

    def set_type(self, type_of_shape: Union[Shape.ShapeType, str]):
        """Sets the type of the shape when an icon is clicked in the annotation toolbar"""
        self.shapeType = type_of_shape

    def set_modality(self, modality: Modality):
        """Sets the modality for the annotation group."""
        self.modality = modality

    def update_annotations(self, current_labels: List[Shape]):
        self.clear()
        for lbl in current_labels:
            self.add_shapes(lbl)
        self.updateShapes.emit(current_labels)

    @Slot(QPointF)
    def pixmap_compensation(self, compensation: QPointF):
        for shape in self.annotations.values():
            if shape.modality == Modality.slide:
                shape.moveBy(-compensation.x(), -compensation.y())

    def updatePosition(self, sceneOffset: QPointF):
        """Adjust the positions of all annotations based on the scene offset"""
        self._scene_offset = sceneOffset
        for shape in self.annotations.values():
            # Adjust the shape position based on the scene offset
            shape.setPos(shape.pos() + sceneOffset)

if __name__ == '__main__':
    from PySide6.QtGui import QPixmap
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

    def onSceneMoved():
        """Slot to handle scene movement and adjust annotations"""
        sceneOffset = viewer.mapToScene(viewer.viewport().rect().topLeft()) - viewer.mapToScene(viewer.viewport().rect().topLeft())
        anno_group.updatePosition(sceneOffset)

    # Connect scene's signal to handle panning and zooming adjustments
    scene.sceneRectChanged.connect(onSceneMoved)

    viewer.show()
    app.exec()
