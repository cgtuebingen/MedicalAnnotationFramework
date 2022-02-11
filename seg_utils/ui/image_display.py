from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import QSize, pyqtSignal, QPointF
from PyQt5.QtGui import QPixmap, QColor

from seg_utils.ui.image_viewer import ImageViewer
from seg_utils.ui.canvas import Canvas
from seg_utils.ui.graphics_scene import ImageViewerScene
from seg_utils.ui.shape import Shape

from typing import List


class ImageDisplay(QFrame):
    """class to manage the central display in the GUI
    controls a QGraphicsView, a QGraphicsScene, a QPixmap and a QWidget for drawing (canvas)"""

    sRequestLabelListUpdate = pyqtSignal(int)
    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(ImageDisplay, self).__init__(*args)

        # main components of the display
        self.image_viewer = ImageViewer(self)
        self.scene = ImageViewerScene(self.image_viewer)
        self.canvas = Canvas()
        self.pixmap = QPixmap()

        # connecting the components
        self.canvas.resize(QSize(0, 0))
        self.proxy = self.scene.addWidget(self.canvas)
        self.image_viewer.setScene(self.scene)

        # put the viewer in the ImageDisplay-Frame
        self.image_viewer.setFrameShape(QFrame.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.image_viewer)

        self.labels = List[Shape]
        self.temp_label = None  # type: Shape
        self.draw_new_color = None  # type: QColor

        # connect events
        self.scene.sShapeHovered.connect(self.shape_hovered)
        self.scene.sShapeSelected.connect(self.shape_selected)
        self.scene.sResetSelAndHigh.connect(self.on_reset_sel_and_high)
        self.canvas.sRequestFitInView.connect(self.image_viewer.fitInView)

    def clear(self):
        """This function deletes all currently stored labels
        and triggers the image_viewer to display a default image"""
        self.scene.b_isInitialized = False
        self.image_viewer.b_isEmpty = True
        self.canvas.pixmap = None
        self.set_labels([])

    def get_pixmap_dimensions(self):
        return [self.pixmap.width(), self.pixmap.height()]

    def init_image(self, pixmap: QPixmap, labels):
        self.pixmap = pixmap
        self.canvas.set_pixmap(self.pixmap)
        self.set_labels(labels)

    def is_empty(self):
        return self.image_viewer.b_isEmpty

    def on_reset_highlight(self):
        self.labels = list(map(self.reset_highlight, self.labels))

    def on_reset_selected(self):
        self.labels = list(map(self.reset_selection, self.labels))

    def on_reset_sel_and_high(self):
        self.on_reset_highlight()
        self.on_reset_selected()

    @staticmethod
    def reset_highlight(label: Shape):
        """resets the highlighting attribute"""
        label.is_highlighted = False
        label.vertices.highlighted_vertex = -1
        return label

    @staticmethod
    def reset_selection(label: Shape):
        """resets the selection attribute"""
        label.isSelected = False
        label.vertices.selected_vertex = -1
        return label

    def set_initialized(self):
        self.scene.b_isInitialized = True
        self.image_viewer.b_isEmpty = False

    def set_labels(self, labels: List[Shape]):
        self.labels = labels
        self.update_canvas()

    def set_mode(self, mode: int):
        assert mode in [self.CREATE, self.EDIT]
        self.scene.mode = mode

    def set_shape_type(self, shape_type):
        self.scene.shape_type = shape_type

    def set_temp_label(self, points: List[QPointF] = None, shape_type: str = None):
        if points and shape_type:
            self.temp_label = Shape(image_size=self.pixmap.size(),
                                    points=points,
                                    shape_type=shape_type,
                                    color=self.draw_new_color)
        else:
            self.temp_label = None

        self.update_canvas()

    def shape_hovered(self, shape_idx: int, closest_vertex_shape: int, vertex_idx: int):
        self.on_reset_highlight()
        if shape_idx > -1:
            shp = self.labels[shape_idx]
            shp.is_highlighted = True
        self.vertex_highlighted(closest_vertex_shape, vertex_idx)
        self.update_canvas()

    def shape_selected(self, shape_idx: int, closest_vertex_shape: int, vertex_idx: int):
        self.on_reset_selected()
        if shape_idx != -1:
            shp = self.labels[shape_idx]
            shp.isSelected = True
            self.sRequestLabelListUpdate.emit(shape_idx)
        self.vertex_selected(closest_vertex_shape, vertex_idx)
        self.update_canvas()

    def update_canvas(self):
        """updates the class variables of the canvas object and triggers a paintEvent"""
        self.canvas.labels = self.labels
        self.canvas.temp_label = self.temp_label
        self.canvas.update()

    def vertex_highlighted(self, shape_idx: int, vertex_idx: int):
        if shape_idx != -1:
            shp = self.labels[shape_idx]  # type: Shape
            shp.vertices.highlighted_vertex = vertex_idx

    def vertex_selected(self, shape_idx: int, vertex_idx: int):
        if vertex_idx != -1:
            shp = self.labels[shape_idx]  # type: Shape
            shp.vertices.selected_vertex = vertex_idx
