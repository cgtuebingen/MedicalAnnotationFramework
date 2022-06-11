from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from seg_utils.ui.list_widgets import ListWidget
from seg_utils.ui.list_widgets_new import LabelList, CommentList
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs_new import CommentDialog

from typing import List


class PolyFrame(QWidget):
    """
    This class is used to build up the part in the right menu of the GUI
    where the currently created Polygons are displayed.

    Provides a clickable "Add comment" text next to each polygon item.
    """

    sUpdateLabels = pyqtSignal(list)
    itemClicked = pyqtSignal(int)

    def __init__(self, *args):
        super(PolyFrame, self).__init__(*args)
        self.setMinimumSize(QSize(0, 300))
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.current_labels = []

        # header line for the polyFrame
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.label.setText("Polygons")
        self.label.setAlignment(Qt.AlignCenter)

        # subFrame comprises the polyList and commentList
        self.subFrame = QFrame()
        self.subFrame.setMinimumSize(QSize(0, 300))
        self.subFrame.setFrameShape(QFrame.StyledPanel)
        self.subFrame.setLayout(QHBoxLayout())
        self.subFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.subFrame.layout().setSpacing(0)

        # displays the created Shapes
        self.polygon_list = LabelList()
        self.polygon_list.setFrameShape(QFrame.NoFrame)

        # places a clickable "Add comment" next to each item in the polyList
        self.comment_list = CommentList()
        self.comment_list.setFrameShape(QFrame.NoFrame)
        self.comment_list.setSpacing(1)
        self.comment_list.setCursor((QCursor(Qt.PointingHandCursor)))

        self.subFrame.layout().addWidget(self.polygon_list)
        self.subFrame.layout().addWidget(self.comment_list)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.subFrame)

        self.polygon_list.itemClicked.connect(self.handle_poly_click)
        self.comment_list.itemClicked.connect(self.handle_comment_click)

    def handle_comment_click(self, item: QListWidgetItem):
        """ opens up a dialog and stores the entered text as a comment"""
        idx = self.comment_list.row(item)
        lbl = self.current_labels[idx]
        comment = lbl.comment if lbl.comment else ""
        dlg = CommentDialog(comment)
        dlg.exec()

        # store the dialog result
        text = "Details" if dlg.comment else "Add comment"
        item.setText(text)
        self.current_labels[idx].comment = dlg.comment
        self.sUpdateLabels.emit(self.current_labels)

    def handle_poly_click(self, item: QListWidgetItem):
        """gets the index of the selected item and emits a signal"""
        idx = self.polygon_list.row(item)
        self.itemClicked.emit(idx)

    def shape_selected(self, idx: int):
        """selects the item with the corresponding index in the poly list"""
        self.polygon_list.item(idx).setSelected(True)

    def update_frame(self, current_labels: List[Shape]):
        """updates the polyList and comment_list with the specified labels"""
        self.current_labels = current_labels
        self.polygon_list.update_with_labels(current_labels)
        self.comment_list.update_list(current_labels)
