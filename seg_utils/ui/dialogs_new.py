from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont, QIcon, QColor

from typing import List

from seg_utils.ui.list_widgets_new import LabelList
from seg_utils.utils.qt import get_icon


class DeleteShapeMessageBox(QMessageBox):
    def __init__(self, shape: str, *args):
        super(DeleteShapeMessageBox, self).__init__(*args)
        if self.parentWidget():
            move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())
        reply = self.question(self, "Deleting Shape", f"You are about to delete {shape}. Continue?",
                              QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer = 1
        else:
            self.answer = 0


class ForgotToSaveMessageBox(QMessageBox):
    def __init__(self, *args):
        super(ForgotToSaveMessageBox, self).__init__(*args)

        save_button = QPushButton(get_icon('save'), "Save Changes")
        dismiss_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogDiscardButton), "Dismiss Changes")
        cancel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")

        self.setWindowTitle("Caution: Unsaved Changes")
        self.setText("Unsaved Changes: How do you want to progress?")

        # NOTE FOR SOME REASON THE ORDER IS IMPORTANT DESPITE THE ROLE - IDK WHY
        self.addButton(save_button, QMessageBox.AcceptRole)
        self.addButton(cancel_button, QMessageBox.RejectRole)
        self.addButton(dismiss_button, QMessageBox.DestructiveRole)

        if self.parentWidget():
            move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())


class NewLabelDialog(QDialog):
    """ a dialog to display all existing label classes so that the user can decide on one
    user can also create new label classes"""
    def __init__(self, classes: List[str], color_map: List[QColor], *args):
        super(NewLabelDialog, self).__init__(*args)
        self.result = ""

        self.setFixedSize(QSize(300, 400))
        self.setWindowTitle("Select class of new shape")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(5)

        # Line Edit for searching/creating classes
        self.shape_input = QLineEdit()
        self.shape_input.setPlaceholderText("Enter shape label")
        self.shape_input.setMaximumHeight(25)

        # info label for when user is about to create a new class
        self.info = QLabel()
        self.info.setContentsMargins(0, 0, 0, 0)
        self.info.setFrameShape(QFrame.NoFrame)
        self.info.setStyleSheet("color: red")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # list widget with the already existing classes
        self.label_list = LabelList()
        self.label_list.update_with_classes(classes, color_map)
        self.confirm = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # connect
        self.shape_input.textChanged.connect(self.handle_shape_input)
        self.confirm.accepted.connect(self.on_close)
        self.confirm.rejected.connect(self.on_cancel)
        self.label_list.itemClicked.connect(self.on_list_selection)

        self.layout().addWidget(self.shape_input)
        self.layout().addWidget(self.info)
        self.layout().addWidget(self.label_list)
        self.layout().addWidget(self.confirm)

    def handle_shape_input(self):
        """ function to filter the list according to user input """
        self.info.clear()
        self.result = ""
        text = self.shape_input.text()
        matches = 0

        # iterate through list, display only matches
        for item_idx in range(self.label_list.count()):
            item = self.label_list.item(item_idx)
            if text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)
                matches += 1

        # option to create a new label class
        if matches == 0:
            self.info.setText("Create new label: {}".format(text))
            self.result = text

    def on_cancel(self):
        """ ensures that the result is an empty string"""
        self.result = ""
        self.close()

    def on_close(self):
        """ prevents an empty result when user clicks Ok"""
        if self.result:
            self.close()
        else:
            self.info.setText("Please select or create a label class")

    def on_list_selection(self, item: QListWidgetItem):
        """ assigns the item name to the class variable"""
        self.info.clear()
        self.result = item.text()


def move_to_center(widget, parent_pos: QPoint, parent_size: QSize):
    # TODO: implement move_to_center somewhere else, so the dialogs don't have to demand a parent widget
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)
