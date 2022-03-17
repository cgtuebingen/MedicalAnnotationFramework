from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor
from seg_utils.ui.list_widgets import ListWidget


class PolyFrame(QWidget):
    """
    This class is used to build up the part in the right menu of the GUI
    where the currently created Polygons are displayed.

    Provides a clickable "Add comment" text next to each polygon item.
    """
    def __init__(self, *args):
        super(PolyFrame, self).__init__(*args)
        self.setMinimumSize(QSize(0, 300))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # header line for the polyFrame
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.label.setText("Polygons")
        self.label.setAlignment(Qt.AlignCenter)

        # subFrame comprises the polyList and commentList
        self.subFrame = QFrame(self)
        self.subFrame.setMinimumSize(QSize(0, 300))
        self.subFrame.setFrameShape(QFrame.StyledPanel)
        self.subFrameLayout = QHBoxLayout(self.subFrame)
        self.subFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.subFrameLayout.setSpacing(0)

        # displays the created Shapes
        self.polygon_list = ListWidget(self.subFrame)
        self.polygon_list.setFrameShape(QFrame.NoFrame)

        # places a clickable "Add comment" next to each item in the polyList
        self.commentList = ListWidget(self.subFrame, is_comment_list=True)
        self.commentList.setFrameShape(QFrame.NoFrame)
        self.commentList.setSpacing(1)
        self.commentList.setCursor((QCursor(Qt.PointingHandCursor)))

        self.subFrameLayout.addWidget(self.polygon_list)
        self.subFrameLayout.addWidget(self.commentList)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.subFrame)

    def get_index_from_selected(self, item):
        """returns the indices of the selected items in polyList and commentList, respectively"""
        return self.polygon_list.row(item), self.commentList.row(item)

    def update_frame(self, current_labels):
        """updates the polyList and commentList with the specified labels"""
        self.polygon_list.update_list(current_labels)
        self.commentList.update_list(current_labels)
