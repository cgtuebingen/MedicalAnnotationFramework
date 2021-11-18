from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor
from seg_utils.ui.list_widget import ListWidget


class PolyFrame(QFrame):
    """
    This class is used to build up the part in the right menu of the GUI
    where the currently created Polygons are displayed.

    Provides a clickable "Add comment" text next to each polygon item.
    """
    def __init__(self, *args):
        super(PolyFrame, self).__init__(*args)
        self.setMinimumSize(QSize(0, 300))
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setObjectName("polyFrame")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setObjectName("polyLayout")

        # header line for the polyFrame
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.label.setObjectName("polyLabel")
        self.label.setText("Polygons")

        # subFrame comprises the polyList and commentList
        self.subFrame = QFrame(self)
        self.subFrame.setMinimumSize(QSize(0, 300))
        self.subFrame.setFrameShape(QFrame.StyledPanel)
        self.subFrame.setObjectName("polySubFrame")
        self.subFrameLayout = QHBoxLayout(self.subFrame)
        self.subFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.subFrameLayout.setSpacing(0)
        self.subFrameLayout.setObjectName("subFrameLayout")

        # displays the created Shapes
        self.polyList = ListWidget(self.subFrame)
        self.polyList.setFrameShape(QFrame.NoFrame)
        self.polyList.setObjectName("polyList")

        # places a clickable "Add comment" next to each item in the polyList
        self.commentList = ListWidget(self.subFrame)
        self.commentList.setFrameShape(QFrame.NoFrame)
        self.commentList.setObjectName("commentList")
        self.commentList.setSpacing(1)
        self.commentList.setCursor((QCursor(Qt.PointingHandCursor)))
        self.commentList.setStyleSheet("selection-color: blue;"
                                       "selection-background-color: white;")

        self.subFrameLayout.addWidget(self.polyList)
        self.subFrameLayout.addWidget(self.commentList)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.subFrame)
