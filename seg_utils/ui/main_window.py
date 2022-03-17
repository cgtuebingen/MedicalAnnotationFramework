from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from seg_utils.ui.image_display import ImageDisplay
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.src.actions import Action
from seg_utils.ui.list_widgets import FileViewingWidget, LabelsViewingWidget


class LabelingMainWindow(QMainWindow):
    """ The main window for the application """
    def __init__(self):
        super(LabelingMainWindow, self).__init__()
        self.setWindowTitle("The All-Purpose Labeling Tool")
        self.resize(1276, 968)
        # The main widget set as focus. Based on a horizontal layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(QHBoxLayout())
        self.main_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.main_widget.layout().setSpacing(0)

        # Center Frame of the body where the image will be displayed in
        self.center_frame = QFrame()
        self.center_frame.setLayout(QVBoxLayout())
        self.center_frame.layout().setContentsMargins(0, 0, 0, 0)
        self.center_frame.layout().setSpacing(0)
        # TODO: The center frame should be given a widget to say "No files to display". This should not be handled
        #       within the ImageDisplay widget
        self.image_display = ImageDisplay()
        self.image_display.setFrameShape(QFrame.NoFrame)
        self.center_frame.layout().addWidget(self.image_display)

        # Right Menu
        self.right_menu_widget = QWidget()
        self.right_menu_widget.setMaximumWidth(200)
        self.right_menu_widget.setLayout(QVBoxLayout())
        self.right_menu_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.right_menu_widget.layout().setSpacing(0)

        # the labels and polygon lists
        self.labels_list = LabelsViewingWidget()
        self.poly_frame = PolyFrame()
        self.right_menu_widget.layout().addWidget(self.labels_list)
        self.right_menu_widget.layout().addWidget(self.poly_frame)

        # the file list
        self.file_list = FileViewingWidget()
        self.right_menu_widget.layout().addWidget(self.file_list)
        self.main_widget.layout().addWidget(self.center_frame)
        self.main_widget.layout().addWidget(self.right_menu_widget)
        self.setCentralWidget(self.main_widget)

        self.menubar = QMenuBar()
        self.menubar.setGeometry(QRect(0, 0, 1276, 22))
        self.setMenuBar(self.menubar)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.toolBar = Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.init_margins()
        self.init_toolbar_actions(self)

    def init_toolbar_actions(self, parent):
        """Initialise all actions present which can be connected to buttons or menu items"""
        # TODO: some shortcuts don't work
        # TODO: Figure out a more modular way to set up these actions
        action_new_project = Action(parent,
                                    "New\nProject",
                                    None,
                                    'Ctrl+N',
                                    "new",
                                    "New project",
                                    enabled=True)
        action_open_project = Action(parent,
                                     "Open\nProject",
                                     None,
                                     'Ctrl+O',
                                     "open",
                                     "Open project",
                                     enabled=True)
        action_save = Action(parent,
                             "Save",
                             None,
                             'Ctrl+S',
                             "save",
                             "Save current state to database")
        action_import = Action(parent,
                               "Import",
                               None,
                               'Ctrl+I',
                               "import",
                               "Import a new file to database")
        action_next_image = Action(parent,
                                   "Next\nImage",
                                   None,
                                   'Right',
                                   "next",
                                   "Go to next image")
        action_prev_image = Action(parent,
                                   "Previous\nImage",
                                   None,
                                   'Left',
                                   "prev",
                                   "Go to previous image")
        action_draw_poly = Action(parent,
                                  "Draw\nPolygon",
                                  None,
                                  icon="polygon",
                                  tip="Draw Polygon (right click to show options)",
                                  checkable=True)
        action_trace_outline = Action(parent,
                                      "Draw\nTrace",
                                      None,
                                      icon="outline",
                                      tip="Trace Outline",
                                      checkable=True)
        action_draw_circle = Action(parent,
                                    "Draw\nCircle",
                                    None,
                                    icon="circle",
                                    tip="Draw Circle",
                                    checkable=True)
        action_draw_rectangle = Action(parent,
                                       "Draw\nRectangle",
                                       None,
                                       icon="square",
                                       tip="Draw Rectangle",
                                       checkable=True)
        action_quit = Action(parent,
                             "Quit\nProgram",
                             None,
                             icon="quit",
                             tip="Quit Program",
                             checkable=True,
                             enabled=True)

        actions = ((action_new_project,
                    action_open_project,
                    action_save,
                    action_import,
                    action_next_image,
                    action_prev_image,
                    action_draw_poly,
                    action_trace_outline,
                    action_draw_circle,
                    action_draw_rectangle,
                    action_quit))

        # Init Toolbar
        self.toolBar.addActions(actions)
