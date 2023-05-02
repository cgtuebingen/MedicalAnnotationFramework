# media-viewing-widgets
A tool to display and zoom into slide images (like tiff data).

## Install
```bash
git clone https://github.com/daniel89-code/media-viewing-widgets.git && cd media_viewing_widgets_tools
pip install .
```

## Usage
The `slide_view` widget should be implemented in a `QGraphicsScene`, which should be integrated into a separate 
`GraphicsView`.
```python
class BaseGraphicsScene(QGraphicsScene):
    def __init__(self):
        super(BaseGraphicsScene, self).__init__()
        
class GraphicsView(QGraphicsView):

    def __init__(self, *args):
        """
        Initialization of the GraphicsView
        :param args: /
        :type args: /
        """
        super(GraphicsView, self).__init__(*args)

        self._pan_start: QPointF = []   # starting point before panning
        self._panning: bool = False     # flag to enable panning

        self.setBackgroundBrush(QBrush(QColor("r")))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)

slide_view = SlideView(filepath=QFileDialog().getOpenFileName()[0])

scene = BaseGraphicsScene()
scene.addItem(slide_view)

viewer = GraphicsView()
viewer.setScene(scene)
```
It is important to implement `QWheelEvent` and `QMouseEvent` as well as passing these events to the children at 
the `GraphicsView` to enable zooming and loading of the images of the different slide levels. For example:
```python
def wheelEvent(self, event: QWheelEvent):
    """
    Scales the image and moves into the mouse position
    :param event: event to initialize the function
    :type event: QWheelEvent
    :return: /
    """
    old_pos = self.mapToScene(event.pos())
    scale_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
    self.scale(scale_factor, scale_factor)
    new_pos = self.mapToScene(event.position().toPoint())
    move = new_pos - old_pos
    self.translate(move.x(), move.y())
    super(GraphicsView, self).wheelEvent(event)

def mouseMoveEvent(self, event: QMouseEvent):
    """
    Realizes panning, if activated
    :param event: event to initialize the function
    :type event: QMouseEvent
    :return: /
    """
    if self._panning:
        new_pos = self.mapToScene(event.pos())
        move = new_pos - self._pan_start
        self.translate(move.x(), move.y())
        self._pan_start = self.mapToScene(event.pos())
    super(GraphicsView, self).mouseMoveEvent(event)
```

## Structure of the code
The basic idea is to enable a `GraphicsView` to handle images with different levels, each with a higher resolution. This 
means, while zooming in a new level is loaded, if the resolution of the current one is to low. Furthermore, a movement
to the mouse position while zooming in should be possible.

The complete program is build around two function: the `updating_zoom_stack` in the `SlideLoader` and the 
`update_image_check` in the `SlideView`. Both are constantly active.

The first one draws a line from the center of the image to the current mouse position and calculates the center of the 
images of the different levels along this line. Subsequently, this function saves an image according to the window size
of each slide level. The shifted centers enable a movement of the view to the mouse position.

```python 
@pyqtSlot()
def updating_zoom_stack(self):
    """
    The function calculates a stack of images of the respective level. Each image has an identical size , leading to
    display a smaller part of the _slide with a higher resultion. To ensure a movement to the mouse position while
    zooming in, the center of each image is located along a line. This line goes through the center of the highest
    level (largest image with smallest resolution) to the mouse position on the lowest level (smallest image with
    highest resolution). Hind: Image the stack as a flipped skew pyramid with the mouse position on the top. Moving
    the mouse equals moving the top of the pyramid with a fixed bottom.
    :return: /
    """
    new_stack: Dict[int, ZoomDict] = {}  # clear stack

    # set the centers for lowest and highest level
    center_high_lvl = (np.asarray(self._slide.level_dimensions[0]) / 2).astype(int)
    center_low_lvl = self._mouse_pos

    # check if an update is necessary
    diff = np.abs(self._old_center - center_low_lvl)
    reserve = np.asarray([self._view_width, self._view_height]) / 2

    if self._new_file or\
       diff[0] > reserve[0] or\
       diff[1] > reserve[1]:  # check if new position will fit into current slides; ensure stack loads for new files
        # calculate the centers along a line with a geometrical distribution.
        # Caution: The absolut distance must be distributed to cover the case to zoom into the right-hand side
        distance = np.abs(center_high_lvl - center_low_lvl)
        distance[0] = 1 if distance[0] == 0 else distance[0]  # geometrical space cannot work with "0"
        distance[1] = 1 if distance[1] == 0 else distance[1]  # geometrical space cannot work with "0"

        # calculating the centers depending on the positions
        if center_low_lvl[0] <= center_high_lvl[0]:
            centers_x = center_low_lvl[0] + np.around(np.geomspace(0.1, distance[0], num=self._num_lvl + 1),
                                                      decimals=1)
        else:
            centers_x = center_low_lvl[0] - np.around(np.geomspace(0.1, distance[0], num=self._num_lvl + 1),
                                                      decimals=1)
        if center_low_lvl[1] <= center_high_lvl[1]:
            centers_y = center_low_lvl[1] + np.around(np.geomspace(0.1, distance[1], num=self._num_lvl + 1),
                                                      decimals=1)
        else:
            centers_y = center_low_lvl[1] - np.around(np.geomspace(0.1, distance[1], num=self._num_lvl + 1),
                                                      decimals=1)
        slide_centers = np.stack([centers_x, centers_y], axis=1)

        # update the stack with the calculated centers
        for slide_lvl in range(self._num_lvl + 1):
            slide_pos = (slide_centers[slide_lvl, :] - self._slide_size[slide_lvl] * 2 ** slide_lvl / 2).astype(int)
            data = np.array(self._slide.read_region(slide_pos, slide_lvl, self._slide_size[slide_lvl]).convert('RGB'))
            new_stack.update({slide_lvl: ZoomDict(position=slide_pos, data=data)})

        # override the zoom_stack with QMutexLocker to prevent parallel reading and writing
        with QMutexLocker(self._stack_mutex):
            self._zoom_stack = new_stack

        self._old_center = center_low_lvl

    self._new_file = False
    if self._updating_slides:
        self.update_slides.emit()  # use a signal for constant updating
```

This procedure may take a while. Therefore, the second function checks which level can be displayed completely. It gets
a desired level and starts checking from here on to the current one. Furthermore, it checks if unloaded areas are 
displayed after panning the view with the mouse.

```python 
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
                self.set_image()
                break   # if a _slide fits, second check is not needed (code efficiency)

            # check for unloaded areas
            elif (view_up_left.x() < scene_up_left_goal[0] or  # check if one corner is unloaded
                  view_up_left.y() < scene_up_left_goal[1] or  # cover of all corners needs "or"
                  view_low_right.x() > scene_low_right_goal[0] or
                  view_low_right.y() > scene_low_right_goal[1]) and lvl == self.slide_lvl_active:
                self.slide_lvl_active += 1
                if self.slide_lvl_active >= self.num_lvl:  # check if you are already on the highest level
                    self.slide_lvl_active = self.num_lvl
                    self.set_image()
                    # Stop function, if on the highest level(no update is required
                    # most of the time, the view on the highest level will be outside the _slide
                    return  # prevents emitting start_checking/stops the function

                self.set_image()
    self.start_checking.emit()
```
