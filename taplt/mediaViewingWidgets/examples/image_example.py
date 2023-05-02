from PyQt6.QtWidgets import *
from media_viewing_widgets import ImageView
from graphics_view import GraphicsView


if __name__ == '__main__':
    # may need High DPI scaling
    app = QApplication(['test'])

    slide_view = ImageView()

    scene = QGraphicsScene()
    scene.addItem(slide_view)

    viewer = GraphicsView(scene)
    viewer.resize(1000, 600)
    viewer.show()
    slide_view.set_image(QFileDialog().getOpenFileName()[0])
    viewer.fitInView()

    app.exec()
