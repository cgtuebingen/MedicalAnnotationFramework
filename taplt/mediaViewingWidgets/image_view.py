from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class ImageView(QGraphicsPixmapItem):
    def __init__(self, *args, file: str = None):
        """
        :param file: path to image to load
        """
        super(ImageView, self).__init__(*args)
        self.active_file = file
        self.setPixmap(QPixmap())
        if file is not None:
            self.set_image(file)

    @property
    def image_size(self) -> QSize:
        """
        :return: the QSize in pixels of the current image. Returns none if no image is set.
        """
        if self.active_file is not None:
            return self.pixmap().size()
        else:
            None

    def set_image(self, file: str):
        """
        :param file: Path to image to display. Will overwrite the existing one.
        :return: None
        """
        pixmap = QPixmap(file)
        self.resetTransform()
        self.setPixmap(pixmap)
        self.active_file = file

    def clear(self):
        """
        Clears the current image.
        """
        self.active_file = None
        self.setPixmap(QPixmap())

    @property
    def is_empty(self) -> bool:
        """
        Whether a picture is set.
        """
        return self.active_file is None

