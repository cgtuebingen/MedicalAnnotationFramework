from PyQt5.QtWidgets import QWidget, QTextEdit, QListWidgetItem
from seg_utils.ui.shape import Shape


class CommentWindow(QWidget):
    """
    represents a QWidget holding a Text Edit Block where user can take notes for an annotation shape
    has pointer variables for (1) its corresponding shape object and (2) its corresponding button in the polyList
    """
    def __init__(self):
        super(CommentWindow, self).__init__()
        self.setGeometry(990, 210, 990, 210)
        self.setWindowTitle("Notes")
        self.comment = QTextEdit(self)
        self.comment.setMinimumSize(self.size())
        self.corr_shape = None  # type: Shape
        self.corr_item_in_list = None  # type: QListWidgetItem

    def update_pointers(self, shape: Shape, item: QListWidgetItem):
        """sets the pointer variables which indicate the corresponding annotation shape & button in polyList"""
        self.corr_shape = shape
        self.corr_item_in_list = item
