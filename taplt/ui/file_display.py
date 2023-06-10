import magic

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from taplt.ui.image_viewer import ImageViewer
from taplt.ui.annotation_group import AnnotationGroup
from taplt.ui.shape import Shape
from taplt.utils.qt import get_icon
from taplt.mediaViewingWidgets.video_display import VideoPlayer

from taplt.mediaViewingWidgets.slide_all_in_one import slide_view


class CenterDisplayWidget(QWidget):
    """ widget to manage the central display in the GUI
    controls a QGraphicsView and a QGraphicsScene for drawing on top of a pixmap """

    sRequestLabelListUpdate = pyqtSignal(int)
    sRequestSave = pyqtSignal()
    sChangeFile = pyqtSignal(int)
    sDrawingTooltip = pyqtSignal(str)
    modalitySwitched = pyqtSignal(str)
    CREATE, EDIT = 0, 1

    def __init__(self, *args):
        super(CenterDisplayWidget, self).__init__(*args)

        # for file types
        self.mime = magic.Magic(mime=True)

        # main components of the display
        self.scene = QGraphicsScene()
        self.image_viewer = ImageViewer(self.scene)

        self.video_player = VideoPlayer(self.scene)
        self.video_label = QLabel()
        self.video_player.frame_grabbed.connect(self.play_frames)

        # Setup of the slide viewer with its own scene
        self.slide_viewer = slide_view(self.scene)
        self.slide_viewer.setScene(self.scene)

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

        pixmap = QPixmap(filepath)
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

    def switch_to_modality(self, filepath: str):
        """
        A function that switches to the modality based on the ``filepath`` parameter
        :param filepath: The path to the file that we want to switch to
        """
        rect = QRectF(QPointF(0, 0), QSizeF(self.image_size))
        file_type = self.mime.from_file(filepath)

        if file_type.startswith('image') and not file_type.endswith('tiff'):
            self.modalitySwitched.emit('image')

            self.image_viewer.setHidden(False)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(True)

            self.video_player.pause()

            self.image_viewer.fitInView(rect)

        elif file_type.startswith('video'):
            self.modalitySwitched.emit('video')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(False)
            self.slide_viewer.setHidden(True)

            self.video_player.fitInView(rect)
            self.video_player.set_video(filepath)
            self.video_player.show()
            self.video_player.play()

        elif file_type.endswith('tiff'):
            self.modalitySwitched.emit('wsi')

            self.image_viewer.setHidden(True)
            self.video_player.setHidden(True)
            self.slide_viewer.setHidden(False)

            self.video_player.pause()

            self.slide_viewer.set_slide(filepath)
            self.slide_viewer.show()
            #self.slide_viewer.fitInView(rect)

        else:
            RuntimeError('The file type ' + file_type + ' is not supported.')
