from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import numpy as np
from .slideloader import SlideLoader


class SlideView(QGraphicsObject):
    start_checking = pyqtSignal()

    def __init__(self, filepath: str = None):
        """
        Initialization of SlideView.
        :param filepath: path to the slide data. The data type is based on the OpenSlide library and can handle:
                         Aperio (.svs, .tif), Hamamatsu (.vms, .vmu, .ndpi), Leica (.scn), MIRAX (.mrxs),
                         Philips (.tiff), Sakura (.svslide), Trestle (.tif), Ventana (.bif, .tif),
                         Generic tiled TIFF (.tif) (see openslide.org)
        :type filepath: str
        """
        super(SlideView, self).__init__()

        self.slide_loader: SlideLoader = SlideLoader()

        self.scene_pos: np.ndarray = np.array([0, 0])  # upper right position of the scene
        self.mouse_pos: np.ndarray = None  # current mouse position on the scene
        self.view_width: int = None
        self.view_height: int = None
        self.num_lvl: int = None  # total number of _slide level
        self.slide_lvl_active: int = None  # number of current displayed _slide level
        self.slide_lvl_goal: int = None  # number of wanted _slide level after zooming

        self.pixmap_item: QGraphicsPixmapItem = QGraphicsPixmapItem(parent=self)
        self.setAcceptHoverEvents(True)
        self.start_checking.connect(self.update_image_check, Qt.ConnectionType.QueuedConnection)
        self.in_scene: bool = self.scene() is not None

        if filepath is not None:
            self.load_new_image(filepath)
            if self.scene():
                if self.scene().views():
                    self.num_lvl: int = self.slide_loader.get_num_lvl()             # total number of _slide level
                    self.slide_lvl_active: int = self.slide_loader.get_num_lvl()    # number of current displayed _slide level
                    self.slide_lvl_goal: int = self.slide_loader.get_num_lvl()      # number of wanted _slide level after zooming
                    self._set_image()
                    self.start_checking.emit()
                    self.in_scene = True

    def boundingRect(self) -> QRectF:
        """
        This function defines the outer bounds of the item as a rectangle; all painting must be restricted
        to inside an item's bounding rect. QGraphicsView uses this to determine whether the item requires redrawing.
        :return: Returns the bounding rect of this item's descendants (i.e., its children, their children, etc.) in
        local coordinates. The rectangle will contain all descendants after they have been mapped to local coordinates.
        If the item has no children, this function returns an empty QRectF.
        (see https://doc.qt.io/qt-6/qgraphicsitem.html)
        """
        return self.childrenBoundingRect()

    def paint(self, p: QPainter, o: QStyleOptionGraphicsItem, widget=None):
        """
        This function, which is usually called by QGraphicsView, paints the contents of an item in local coordinates.
        Reimplement this function in a QGraphicsItem subclass to provide the item's painting implementation, using
        painter. The option parameter provides style options for the item, such as its state, exposed area and its
        level-of-detail hints. The widget argument is optional. If provided, it points to the widget that is being
        painted on; otherwise, it is 0. For cached painting, widget is always 0.
        (see https://doc.qt.io/qt-6/qgraphicsitem.html)
        :return: /
        """
        if not self.in_scene and self.scene().views() is not None:
            self.in_scene = True
            if self.slide_loader.current_file is not None:
                self.refactor_image()
                self._set_image()

    def load_new_image(self, filepath: str):
        """
        Loads and displays a new image
        :param filepath: path of the _slide data. The data type is based on the OpenSlide library and can handle:
                         Aperio (.svs, .tif), Hamamatsu (.vms, .vmu, .ndpi), Leica (.scn), MIRAX (.mrxs),
                         Philips (.tiff), Sakura (.svslide), Trestle (.tif), Ventana (.bif, .tif),
                         Generic tiled TIFF (.tif) (see https://openslide.org)
        :type filepath: str
        :return: /
        """
        self.blockSignals(True)
        self.slide_loader.set_slide(filepath)
        if self.in_scene:
            self.refactor_image()
            self._set_image()
        self.blockSignals(False)

    def refactor_image(self):
        """
        Resets the metadata of a _slide after loading a new one or resizing the view.
        :return: /
        """
        if self.scene().views():
            scene_viewer = self.scene().views()[0].viewport()
            self.view_width = scene_viewer.width()
            self.view_height = scene_viewer.height()
            self.slide_loader.update_size(width=self.view_width, height=self.view_height)
            self.num_lvl = self.slide_loader.get_num_lvl()
            self.slide_lvl_active = self.num_lvl
            self.slide_lvl_goal = self.num_lvl
            self.scene_pos = np.array([0, 0])
            self.mouse_pos = self.slide_loader.get_mouse_pos()

    def _set_image(self):
        """
        Displays the image and handles the scene position of the new image
        :return: /
        """
        # load position and data
        slides = self.slide_loader.get_zoom_stack()
        self.scene_pos = slides[self.slide_lvl_active]['position']
        image = slides[self.slide_lvl_active]['data']

        # set the image
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        q_image = QImage(image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        self.pixmap_item.resetTransform()
        self.pixmap_item.setPixmap(QPixmap(q_image))

        # stretch the image into normed size and set the scene position
        # important: use pixmap item and not the scene. Otherwise, a movement during in and out zooming will occur.
        self.pixmap_item.setScale(2 ** self.slide_lvl_active)
        self.pixmap_item.setPos(*self.scene_pos)

    def slide_change(self, slide_change: int):
        """
        Adds value to the _slide level goal, the displayed _slide level is handled internal
        :param slide_change: wanted difference to current _slide level
        :type slide_change: int
        :return: /
        """
        self.slide_lvl_goal += slide_change
        self.slide_lvl_goal = max([self.slide_lvl_goal, 0])             # goal can not be less zero
        self.slide_lvl_goal = min([self.slide_lvl_goal, self.num_lvl])  # goal can not be more when max number of level

    @pyqtSlot()
    def update_image_check(self):
        """
        Checks which level can be and if unloaded areas are displayed. This function decides if a new image will be
        displayed. It goes through all level from the goal to the current one. If a _slide fits completely into the
        view, it will be displayed. If no _slide fits, it will stay in the current level, but checks if a corner of the
        view is outside the _slide. If so, the current slide_level will be raised (prevents displaying of unloaded
        areas).
        :return: /
        """
        if self.scene():  # don't run code without a scene, prevents crashes
            if self.view_width != self.scene().views()[0].viewport().width() or \
               self.view_height != self.scene().views()[0].viewport().height():
                self.refactor_image()

            slides = self.slide_loader.get_zoom_stack()
            view_up_left = self.scene().views()[0].mapToScene(int(0.02 * self.view_width),
                                                              int(0.02 * self.view_height))  # 2% buffer for frame
            view_low_right = self.scene().views()[0].mapToScene(int(0.98 * self.view_width),
                                                                int(0.98 * self.view_height))  # 2% buffer for frame

            for lvl in range(min(self.slide_lvl_goal, self.slide_lvl_active),
                             max(self.slide_lvl_goal, self.slide_lvl_active) + 1):
                scene_up_left_goal = np.asarray(slides[lvl]['position'])
                scene_low_right_goal = scene_up_left_goal + self.slide_loader.get_slide_size(lvl) * 2 ** lvl

                # check for best _slide level
                if (view_up_left.x() > scene_up_left_goal[0] and  # check if _slide fits completely int the view
                    view_up_left.y() > scene_up_left_goal[1] and  # completely is the reason for use of "and"
                    view_low_right.x() < scene_low_right_goal[0] and
                    view_low_right.y() < scene_low_right_goal[1]) and \
                        lvl < self.slide_lvl_active:  # to ensure that not every time an image will be displayed
                    self.slide_lvl_active = lvl
                    self._set_image()
                    break   # if a _slide fits, second check is not needed (code efficiency)

                # check for unloaded areas
                elif (view_up_left.x() < scene_up_left_goal[0] or  # check if one corner is unloaded
                      view_up_left.y() < scene_up_left_goal[1] or  # cover of all corners needs "or"
                      view_low_right.x() > scene_low_right_goal[0] or
                      view_low_right.y() > scene_low_right_goal[1]) and lvl == self.slide_lvl_active:
                    self.slide_lvl_active += 1
                    if self.slide_lvl_active >= self.num_lvl:  # check if you are already on the highest level
                        self.slide_lvl_active = self.num_lvl
                        self._set_image()
                        # Stop function, if on the highest level(no update is required
                        # most of the time, the view on the highest level will be outside the _slide
                        return  # prevents emitting start_checking/stops the function

                    self._set_image()
        self.start_checking.emit()

    def wheelEvent(self, event: QGraphicsSceneWheelEvent):
        """
        WheelEvent will cause a zoom. This function changes the wanted _slide level according to the zoom direction.
        Also it will set the active _slide level to the highest possible. Therefore, the "update_image_check" will handle
        the correct displayed _slide level.
        :param event: event to initialize the function
        :type event: QGraphicsSceneWheelEvent
        :return: /
        """
        hysteresis = 1.5
        # to ensure a hysteresis (need to be larger when 1)
        # theoretically 2 is enough, but it seems to work better with 1.5
        image_pos_upleft = self.scene().views()[0].mapToScene(0, 0)
        image_pos_lowright = self.scene().views()[0].mapToScene(self.view_width, self.view_height)

        if self.view_width >= self.view_height:  # check for larger dimension
            width_image = (image_pos_lowright.x() - image_pos_upleft.x()) / (2 ** self.slide_lvl_active)
            if width_image <= self.view_width and event.delta() > 0:
                self.slide_change(int(-1))
            if width_image / hysteresis > self.view_width and event.delta() < 0:    # to ensure a hysteresis
                self.slide_change(int(+1))

        else:
            height_image = (image_pos_lowright.y() - image_pos_upleft.y()) / (2 ** self.slide_lvl_active)
            if height_image <= self.view_height and event.delta() > 0:
                self.slide_change(int(-1))
            if height_image / hysteresis > self.view_height and event.delta() < 0:  # to ensure a hysteresis
                self.slide_change(int(+1))

        self.slide_lvl_active = self.num_lvl    # set active level to highest possible
        self.start_checking.emit()  # restart the update (after pausing on highest level)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Adds a level after panning to prevent unloaded data
        :param event: event to initialize the function
        :type event: QGraphicsSceneMouseEvent
        :return: /
        """
        self.slide_lvl_active = min([self.slide_lvl_active + 1, self.num_lvl])
        self._set_image()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Function needs to be implemented for other QGraphicsSceneMouseEvent.
        :param event: event to initialize the function
        :type event: QGraphicsSceneMouseEvent
        :return: /
        """
        pass

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Gives the _slide loader the current mouse position
        :param event: event to initialize the function
        :type event: QGraphicsSceneHoverEvent
        :return: /
        """
        mouse_scene_pos = self.mapToScene(event.pos())
        self.mouse_pos = np.array([mouse_scene_pos.x(), mouse_scene_pos.y()]).astype(int)
        self.slide_loader._mouse_pos = self.mouse_pos
