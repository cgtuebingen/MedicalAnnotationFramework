# This file creates the UI without the QT Designer as it is cumbersome to include more functionality
# to the QT Designer if it is individual

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from seg_utils.ui.image_display import ImageDisplay
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.ui.list_widget import ListWidget
from seg_utils.src.actions import Action


class LabelUI(object):
    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.resize(1276, 968)
        main_window.setTabShape(QtWidgets.QTabWidget.Rounded)

        # mainWidget where Everything is included
        # contains Vertical Layout where e.g. a header can be included
        self.mainWidget = QtWidgets.QWidget(main_window)
        self.mainWidget.setObjectName("mainWidget")
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName("verticalLayout")

        # Body of the widget arrange as horizontal layout
        self.bodyFrame = QtWidgets.QFrame(self.mainWidget)
        self.bodyFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.bodyFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.bodyFrame.setObjectName("bodyFrame")
        self.bodyLayout = QtWidgets.QHBoxLayout(self.bodyFrame)
        self.bodyLayout.setContentsMargins(0, 0, 0, 0)
        self.bodyLayout.setSpacing(0)
        self.bodyLayout.setObjectName("bodyLayout")

        # Center Frame of the body where the image will be displayed in
        self.centerFrame = QtWidgets.QFrame(self.bodyFrame)
        self.centerFrame.setAutoFillBackground(False)
        self.centerFrame.setStyleSheet("")
        self.centerFrame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.centerFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.centerFrame.setObjectName("centerFrame")
        self.centerLayout = QtWidgets.QVBoxLayout(self.centerFrame)
        self.centerLayout.setContentsMargins(0, 0, 0, 0)
        self.centerLayout.setSpacing(0)
        self.centerLayout.setObjectName("centerLayout")
        self.imageDisplay = ImageDisplay(self.centerFrame)
        self.imageDisplay.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.imageDisplay.setObjectName("imageDisplay")
        self.centerLayout.addWidget(self.imageDisplay)
        self.bodyLayout.addWidget(self.centerFrame)
        
        # Right Menu
        self.rightMenuFrame = QtWidgets.QFrame(self.bodyFrame)
        self.rightMenuFrame.setMaximumSize(QtCore.QSize(200, 16777215))
        self.rightMenuFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.rightMenuFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.rightMenuFrame.setObjectName("rightMenuFrame")
        self.rightMenuLayout = QtWidgets.QVBoxLayout(self.rightMenuFrame)
        self.rightMenuLayout.setContentsMargins(0, 0, 0, 0)
        self.rightMenuLayout.setSpacing(0)
        self.rightMenuLayout.setObjectName("rightMenuLayout")
        
        # Frame for the label list
        self.labelFrame = QtWidgets.QFrame(self.rightMenuFrame)
        self.labelFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.labelFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.labelFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.labelFrame.setObjectName("labelFrame")
        self.labelLayout = QtWidgets.QVBoxLayout(self.labelFrame)
        self.labelLayout.setContentsMargins(0, 0, 0, 0)
        self.labelLayout.setSpacing(0)
        self.labelLayout.setObjectName("labelLayout")
        self.labelListLabel = QtWidgets.QLabel(self.labelFrame)
        self.labelListLabel.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.labelListLabel.setObjectName("labelListLabel")
        self.labelListLabel.setText("Labels")
        self.labelLayout.addWidget(self.labelListLabel)
        self.labelList = ListWidget(self.labelFrame)
        self.labelList.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.labelList.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.labelList.setObjectName("labelList")
        self.labelList.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.labelLayout.addWidget(self.labelList)
        self.rightMenuLayout.addWidget(self.labelFrame)
        
        # Frame for the Polygons
        self.polyFrame = PolyFrame(self.rightMenuFrame)
        self.rightMenuLayout.addWidget(self.polyFrame)

        # Frame for the file list
        self.fileFrame = QtWidgets.QFrame(self.rightMenuFrame)
        self.fileFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.fileFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.fileFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.fileFrame.setObjectName("fileFrame")
        self.fileLayout = QtWidgets.QVBoxLayout(self.fileFrame)
        self.fileLayout.setContentsMargins(0, 0, 0, 0)
        self.fileLayout.setSpacing(0)
        self.fileLayout.setObjectName("fileLayout")
        self.fileLabel = QtWidgets.QLabel(self.fileFrame)
        self.fileLabel.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.fileLabel.setObjectName("fileLabel")
        self.fileLabel.setText("File List")
        self.fileLayout.addWidget(self.fileLabel)
        self.fileSearch = QtWidgets.QTextEdit(self.fileFrame)

        # Size Policy
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.fileSearch.sizePolicy().hasHeightForWidth())
        self.fileSearch.setSizePolicy(size_policy)
        self.fileSearch.setMaximumSize(QtCore.QSize(16777215, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.fileSearch.setFont(font)
        self.fileSearch.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.fileSearch.setLineWidth(0)
        self.fileSearch.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fileSearch.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fileSearch.setCursorWidth(1)
        self.fileSearch.setPlaceholderText("Search Filename")
        self.fileSearch.setObjectName("fileSearch")
        self.fileLayout.addWidget(self.fileSearch)
        self.fileList = ListWidget(self.fileFrame)
        self.fileList.setIconSize(QtCore.QSize(7, 7))
        self.fileList.setItemAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.fileList.setObjectName("fileList")
        self.fileLayout.addWidget(self.fileList)
        self.rightMenuLayout.addWidget(self.fileFrame)
        self.bodyLayout.addWidget(self.rightMenuFrame)
        self.rightMenuFrame.raise_()
        self.centerFrame.raise_()
        self.mainLayout.addWidget(self.bodyFrame)
        main_window.setCentralWidget(self.mainWidget)

        self.menubar = QtWidgets.QMenuBar(main_window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1276, 22))
        self.menubar.setObjectName("menubar")
        main_window.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.toolBar = Toolbar(main_window)
        main_window.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.init_margins()
        self.init_toolbar_actions(main_window)

    def init_toolbar_actions(self, parent):
        """Initialise all actions present which can be connected to buttons or menu items"""
        # TODO: some shortcuts dont work
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
