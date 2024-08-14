from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from taplt.media_viewing_widgets.widgets.video_viewer import VideoPlayer
from taplt.media_viewing_widgets.widgets.image_viewer import ImageViewer
from taplt.media_viewing_widgets.widgets.slide_viewer import SlideView

from taplt.ui.annotation_group import AnnotationGroup
from taplt.ui.shape import Shape
from taplt.utils.qt import get_icon
from taplt.utils.project_structure import modality, Modality
from taplt.ui.annotations_view import AnnotationView


class CenterDisplayWidget(QWidget):
    """ widget to manage the central display in the GUI
    controls a QGraphicsView and a QGraphicsScene for drawing on top of a pixmap """

    sRequestLabelListUpdate = Signal(int)
    sRequestSave = Signal()
    sChangeFile = Signal(int)
    sDrawingTooltip = Signal(str)
    modalitySwitched = Signal(str)
    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(CenterDisplayWidget, self).__init__(*args)

        # main components of the display
        self.annotations_scene = QGraphicsScene()
        self.viewer_scene = QGraphicsScene()
        self.viewer_scene.sceneRectChanged.connect(self.synchronize_scene_sizes)
        self.viewer_scene.sceneRectChanged.connect(self.synchronize_scene_sizes)

        self.current_viewer = None

        self.image_viewer = ImageViewer(self.viewer_scene)

        self.video_player = VideoPlayer(self.viewer_scene)
        self.video_label = QLabel()
        self.video_player.frame_grabbed.connect(self.play_frames)

        # Setup of the slide viewer with its own scene
        self.slide_viewer = SlideView(self.viewer_scene)
        self.slide_viewer.sendPixmap.connect(self.set_pixmap_to_slide)

        self.annotations_view = AnnotationView(self.annotations_scene)
        self.annotations_view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.pixmap = QGraphicsPixmapItem()
        self.viewer_scene.addItem(self.pixmap)
        self.annotations = AnnotationGroup()
        self.annotations_scene.addItem(self.annotations)
        self.annotations.sToolTip.connect(self.sDrawingTooltip.emit)

        # self.slide_viewer.pix_move_compensated.connect(self.annotations.pixmap_compensation)

        # QLabel displaying the patient's id/name/alias
        self.patient_label = QLabel()
        self.patient_label.setContentsMargins(10, 0, 10, 0)

        self.hide_button = QPushButton(get_icon("next"), "", self)
        self.hide_button.setGeometry(0, 0, 40, 40)

        # put the viewer in the ImageDisplay-Frame
        self.image_viewer.setFrameShape(QFrame.Shape.NoFrame)
        self.layout = QStackedLayout(self)
        self.layout.addWidget(self.annotations_view)
        self.layout.addWidget(self.image_viewer)
        self.layout.addWidget(self.video_player)
        self.layout.addWidget(self.slide_viewer)
        self.layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # rect_item = QGraphicsRectItem(10, 10, 100, 50)
        # rect_item.setBrush(QBrush(QColor(255, 0, 0, 128))) # Red color with some transparency
        # rect_item.setZValue(100000)
        # self.annotations_scene.addItem(rect_item)

        # self.layout.addWidget(self.slide_wrapper)
        self.layout.addWidget(self.patient_label)

        # Modality of the current Display
        self.file_type = None
        self.slide_viewer.setAnnotationViewport(self.annotations_view.viewport())
        self.slide_viewer.setAnnotationView(self.annotations_view)

        self.annotations_scene.setSceneRect(QRectF(0,0,400, 400))

    def mousePressEvent(self, event: QMouseEvent):
        if self.annotations.mode == AnnotationGroup.AnnotationMode.DRAW:
            if event.button() == Qt.MouseButton.LeftButton:
                self.annotations.create_shape()
        event.accept()

    def clear(self):
        """This function deletes all currently stored labels
        and triggers the image_viewer to display a default image"""
        self.viewer_scene.b_isInitialized = False
        self.image_viewer.b_isEmpty = True
        self.viewer_scene.clear()
        self.set_labels([])

    def set_annotation_mode(self, mode: bool):
        self.slide_viewer.setAnnotationMode(mode)

    def get_pixmap_dimensions(self):
        return [self.pixmap.pixmap().width(), self.pixmap.pixmap().height()]

    def init_image(self, filepath: str, patient: str, labels: list, classes: list):
        """initializes the pixmap to display the image in the center widget
        return the current labels as shape objects"""
        self.set_initialized()
        self.annotations.classes = classes

        self.file_type = modality(filepath)

        if not self.file_type == Modality.slide:
            pixmap = QPixmap(filepath)
            self.image_size = pixmap.size()
        else:
            pixmap = QPixmap()
            self.image_size = self.slide_viewer.frameRect().size()

        self.pixmap.setPixmap(pixmap)

        self.pixmap.setZValue(10)
        
        labels = [Shape(image_size=self.image_size,
                        label_dict=_label,
                        color=self.annotations.get_color_for_label(_label['label']))
                  for _label in labels]

        self.annotations.update_annotations(labels)
        self.hide_button.raise_()

        self.switch_to_modality(filepath)
        self.patient_label.setText(patient)

        self.synchronize_scene_sizes(QRectF(QPointF(0, 0), QSizeF(self.image_size)))

        return labels

    def is_empty(self):
        return self.image_viewer.b_isEmpty

    def set_initialized(self):
        self.viewer_scene.b_isInitialized = True
        self.image_viewer.b_isEmpty = False

    def play_frames(self, image: QImage, t):
        pix = QPixmap.fromImage(image)
        self.video_label.setPixmap(pix)
        self.video_label.show()

    @Slot(QGraphicsPixmapItem)
    def set_pixmap_to_slide(self, pixmap):
        self.pixmap.setPixmap(pixmap)
        self.pixmap.setZValue(0)

    def synchronize_scene_sizes(self, rect):
        """Synchronize the size of the annotations_scene with the viewer_scene"""
        viewer_rect = rect
        self.annotations_scene.setSceneRect(viewer_rect)

        if self.current_viewer and self.current_viewer == self.slide_viewer:
            new_rect = QRectF(QPointF(0, 0), QPointF(self.slide_viewer.slide.dimensions[0],
                                                     self.slide_viewer.slide.dimensions[1]))
            self.annotations_scene.setSceneRect(new_rect)

    def switch_to_modality(self, filepath: str):
        """
        A function that switches to the modality based on the ``filepath`` parameter
        :param filepath: The path to the file that we want to switch to
        """
        rect = QRectF(QPointF(0, 0), QSizeF(self.image_size))
        self.file_type = modality(filepath)
        self.annotations.set_modality(self.file_type)

        if self.file_type == Modality.image:
            self.modalitySwitched.emit('image')
            self.image_viewer.setHidden(False)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(True)
            self.annotations_view.set_view(self.image_viewer.viewport())

            self.video_player.pause()

            self.image_viewer.fitInView(rect)
            self.current_viewer = self.image_viewer

        elif self.file_type == Modality.video:
            self.modalitySwitched.emit('video')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(False)
            self.slide_viewer.setHidden(True)
            self.annotations_view.set_view(self.video_player.viewport())

            self.video_player.fitInView(rect)
            self.video_player.set_video(filepath)
            self.video_player.show()
            self.video_player.play()
            self.current_viewer = self.video_player

        elif self.file_type == Modality.slide:

            self.modalitySwitched.emit('slide')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(False)
            self.annotations_view.set_view(self.slide_viewer.viewport())

            self.video_player.pause()

            self.slide_viewer.load_slide(filepath)
            self.slide_viewer.show()
            self.current_viewer = self.slide_viewer

        else:
            RuntimeError('The file type ' + self.file_type + ' is not supported.')

        self.synchronize_scene_sizes(rect)
