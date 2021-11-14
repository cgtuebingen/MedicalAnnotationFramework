# This file creates the UI without the QT Designer as it is cumbersome to include more functionality
# to the QT Designer if it is individual

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from seg_utils.ui.image_viewer import ImageViewer
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.list_widget import ListWidget
from seg_utils.ui.comment_window import CommentWindow


class LabelUI(object):
    def setupUI(self, mainWindow):
        mainWindow.setObjectName("MainWindow")
        mainWindow.resize(1276, 968)
        mainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)

        # mainWidget where Everything is included
        # contains Vertical Layout where e.g. a header can be included
        self.mainWidget = QtWidgets.QWidget(mainWindow)
        self.mainWidget.setObjectName("mainWidget")
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName("verticalLayout")

        # Body of the widget arrange as horizontral layout
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
        self.imageDisplay = ImageViewer(self.centerFrame)
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
        self.labelList = QtWidgets.QListWidget(self.labelFrame)
        self.labelList.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.labelList.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.labelList.setObjectName("labelList")
        self.labelList.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.labelLayout.addWidget(self.labelList)
        self.rightMenuLayout.addWidget(self.labelFrame)
        
        # Frame for the Polygons
        self.polyFrame = QtWidgets.QFrame(self.rightMenuFrame)
        self.polyFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.polyFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.polyFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.polyFrame.setObjectName("polyFrame")
        self.polyLayout = QtWidgets.QVBoxLayout(self.polyFrame)
        self.polyLayout.setContentsMargins(0, 0, 0, 0)
        self.polyLayout.setSpacing(0)
        self.polyLayout.setObjectName("polyLayout")
        self.polyLabel = QtWidgets.QLabel(self.polyFrame)
        self.polyLabel.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.polyLabel.setObjectName("polyLabel")
        self.polyLabel.setText("Polygons")
        self.polyLayout.addWidget(self.polyLabel)

        # polySubFrame comprises both the PolygonList and the corresponding "Add comment"-List
        self.polySubFrame = QtWidgets.QFrame(self.polyFrame)
        self.polySubFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.polySubFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.polySubFrame.setObjectName("polySubFrame")
        self.subFrameLayout = QtWidgets.QHBoxLayout(self.polySubFrame)
        self.subFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.subFrameLayout.setSpacing(0)
        self.subFrameLayout.setObjectName("subFrameLayout")

        # displays the created Shapes
        self.polyList = ListWidget(self.polyFrame)
        self.polyList.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.polyList.setObjectName("polyList")

        # places a clickable "Add comment" next to each item in the polyList
        self.commentList = ListWidget(self.polyFrame)
        self.commentList.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.commentList.setObjectName("commentList")
        self.commentList.setSpacing(1)
        self.commentList.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))
        self.commentList.setStyleSheet("selection-color: blue;"
                                       "selection-background-color: white;")

        self.subFrameLayout.addWidget(self.polyList)
        self.subFrameLayout.addWidget(self.commentList)
        self.polyLayout.addWidget(self.polySubFrame)
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
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fileSearch.sizePolicy().hasHeightForWidth())
        self.fileSearch.setSizePolicy(sizePolicy)
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
        self.fileList = QtWidgets.QListWidget(self.fileFrame)
        self.fileList.setIconSize(QtCore.QSize(7, 7))
        self.fileList.setItemAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.fileList.setObjectName("fileList")
        self.fileLayout.addWidget(self.fileList)
        self.rightMenuLayout.addWidget(self.fileFrame)
        self.bodyLayout.addWidget(self.rightMenuFrame)
        self.rightMenuFrame.raise_()
        self.centerFrame.raise_()
        self.mainLayout.addWidget(self.bodyFrame)
        mainWindow.setCentralWidget(self.mainWidget)
        self.menubar = QtWidgets.QMenuBar(mainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1276, 22))
        self.menubar.setObjectName("menubar")
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)
        self.toolBar = Toolbar(mainWindow)
        mainWindow.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.initMargins()

        # window for comments
        self.commentWindow = CommentWindow()
        self.commentWindow.move(self.toolBar.geometry().width(), 0)
