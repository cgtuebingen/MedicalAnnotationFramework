from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont, QIcon

from seg_utils.ui.list_widgets_new import LabelList


class NewLabelDialog(QDialog):
    def __init__(self, *args):
        super(NewLabelDialog, self).__init__(*args)

        self.setFixedSize(QSize(300, 400))
        self.setWindowTitle("Select class of new shape")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(5)

        # Line Edit for searching/creating classes
        self.shape_input = QLineEdit()
        self.shape_input.setPlaceholderText("Enter shape label")
        self.shape_input.setMaximumHeight(25)

        self.class_name = ""
        self.label_list = LabelList()
        self.confirm = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # connect
        self.shape_input.textChanged.connect(self.handle_shape_input)
        self.confirm.accepted.connect(self.close)
        self.confirm.rejected.connect(self.on_cancel)
        self.label_list.itemClicked.connect(self.on_list_selection)

        self.layout().addWidget(self.shape_input)
        self.layout().addWidget(self.label_list)
        self.layout().addWidget(self.confirm)

    def handle_shape_input(self):
        """ function to filter the list according to user input """
        text = self.shape_input.text()

        # iterate through list, display only matches
        for item_idx in range(self.label_list.count()):
            item = self.listWidget.item(item_idx)
            if text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)

    def on_cancel(self):
        """ ensures that the result is an empty string"""
        self.class_name = ""
        self.close()

    def on_list_selection(self, item: QListWidgetItem):
        """ assigns the item name to the class variable"""
        self.class_name = item.text()





def move_to_center(widget, parent_pos: QPoint, parent_size: QSize):
    # TODO: implement move_to_center somewhere else, so the dialogs don't have to demand a parent widget
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)
