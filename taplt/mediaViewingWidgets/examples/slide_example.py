from PyQt6.QtWidgets import *
from taplt.mediaViewingWidgets.slide_view import SlideView


if __name__ == '__main__':
    # may need High DPI scaling
    app = QApplication(['test'])

    slide_view = SlideView()

    scene = QGraphicsScene()
    scene.addItem(slide_view)

    viewer = SlideView(scene)
    viewer.resize(1000, 600)
    viewer.show()
    slide_view.load_new_image(QFileDialog().getOpenFileName()[0])
    viewer.fitInView()

    app.exec()
