from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from taplt.ui.image_viewer import ImageViewer
from taplt.ui.annotation_group import AnnotationGroup
from taplt.ui.shape import Shape
from taplt.utils.qt import get_icon
from taplt.media_viewing_widgets.widgets.video_viewer import VideoPlayer

from taplt.media_viewing_widgets.widgets.slide_viewer import SlideView
from taplt.utils.project_structure import modality, Modality


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
        self.scene = QGraphicsScene()
        self.image_viewer = ImageViewer(self.scene)

        self.video_player = VideoPlayer(self.scene)
        self.video_label = QLabel()
        self.video_player.frame_grabbed.connect(self.play_frames)

        # Setup of the slide viewer with its own scene
        self.slide_viewer = SlideView(self.scene)
        self.slide_viewer.sendPixmap.connect(self.set_pixmap_to_slide)

        self.pixmap = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap)
        self.annotations = AnnotationGroup()
        self.scene.addItem(self.annotations)
        self.annotations.sToolTip.connect(self.sDrawingTooltip.emit)

        # QLabel displaying the patient's id/name/alias
        self.patient_label = QLabel()
        self.patient_label.setContentsMargins(10, 0, 10, 0)

        self.hide_button = QPushButton(get_icon("next"), "", self)
        self.hide_button.setGeometry(0, 0, 40, 40)

        # put the viewer in the ImageDisplay-Frame
        self.image_viewer.setFrameShape(QFrame.Shape.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.image_viewer)
        self.layout.addWidget(self.video_player)
        self.layout.addWidget(self.slide_viewer)

        # self.layout.addWidget(self.slide_wrapper)
        self.layout.addWidget(self.patient_label)

    def mousePressEvent(self, event: QMouseEvent):
        if self.annotations.mode == AnnotationGroup.AnnotationMode.DRAW:
            if event.button() == Qt.MouseButton.LeftButton:
                self.annotations.create_shape()
        event.accept()

    def clear(self):
        """This function deletes all currently stored labels
        and triggers the image_viewer to display a default image"""
        self.scene.b_isInitialized = False
        self.image_viewer.b_isEmpty = True
        self.scene.clear()
        self.set_labels([])

    def get_pixmap_dimensions(self):
        return [self.pixmap.pixmap().width(), self.pixmap.pixmap().height()]

    def init_image(self, filepath: str, patient: str, labels: list, classes: list):
        """initializes the pixmap to display the image in the center widget
        return the current labels as shape objects"""
        self.set_initialized()
        self.annotations.classes = classes

        file_type = modality(filepath)

        if not file_type == Modality.slide:
            pixmap = QPixmap(filepath)
        else:
            pixmap = QPixmap()

        self.image_size = pixmap.size()
        self.pixmap.setPixmap(pixmap)
        
        labels = [Shape(image_size=self.image_size,
                        label_dict=_label,
                        color=self.annotations.get_color_for_label(_label['label']))
                  for _label in labels]

        self.annotations.update_annotations(labels)
        self.hide_button.raise_()

        self.switch_to_modality(filepath)
        self.patient_label.setText(patient)
        return labels

    def is_empty(self):
        return self.image_viewer.b_isEmpty

    def set_initialized(self):
        self.scene.b_isInitialized = True
        self.image_viewer.b_isEmpty = False

    def play_frames(self, image: QImage, t):
        pix = QPixmap.fromImage(image)
        self.video_label.setPixmap(pix)
        self.video_label.show()

    @Slot(QGraphicsPixmapItem)
    def set_pixmap_to_slide(self, pixmap_item):
        self.scene.removeItem(self.annotations)
        self.scene.addItem(pixmap_item)
        self.scene.addItem(self.annotations)

    def switch_to_modality(self, filepath: str):
        """
        A function that switches to the modality based on the ``filepath`` parameter
        :param filepath: The path to the file that we want to switch to
        """
        rect = QRectF(QPointF(0, 0), QSizeF(self.image_size))
        file_type = modality(filepath)
        if self.slide_viewer.pixmap_item and self.slide_viewer.pixmap_item in self.scene.items():
            self.scene.removeItem(self.slide_viewer.pixmap_item)

        if file_type == Modality.image:
            self.modalitySwitched.emit('image')
            self.image_viewer.setHidden(False)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(True)

            self.video_player.pause()

            self.image_viewer.fitInView(rect)

        elif file_type == Modality.video:
            self.modalitySwitched.emit('video')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(False)
            self.slide_viewer.setHidden(True)

            self.video_player.fitInView(rect)
            self.video_player.set_video(filepath)
            self.video_player.show()
            self.video_player.play()

        elif file_type == Modality.slide:

            self.modalitySwitched.emit('slide')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(False)

            self.video_player.pause()

            self.slide_viewer.load_slide(filepath)
            self.slide_viewer.show()

        else:
            RuntimeError('The file type ' + file_type + ' is not supported.')
