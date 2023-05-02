from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from media_viewing_widgets import VideoPlayer


if __name__ == '__main__':
    app = QApplication(["test"])
    vid = VideoPlayer()
    img = QLabel()

    def popup(image: QImage, t):
        image = image.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
        pix = QPixmap.fromImage(image)
        img.setPixmap(pix)
        img.show()

    vid.frame_grabbed.connect(popup)
    vid.set_video(QFileDialog().getOpenFileName()[0])
    vid.show()
    vid.play()
    app.exec()
