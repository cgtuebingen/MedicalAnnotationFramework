from PyQt5.QtWidgets import (QDialog, QPushButton, QWidget, QLabel,
                             QVBoxLayout, QTextEdit, QHBoxLayout, QDialogButtonBox,
                             QStyle, QMessageBox)
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont

from seg_utils.ui.list_widget import ListWidget
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon, getIcon


class NewShapeDialog(QDialog):
    def __init__(self, parent: QWidget, *args):
        super(NewShapeDialog, self).__init__(*args)

        # Default values
        self.class_name = ""

        # Create the shape of the QDialog
        self.setFixedSize(QSize(300, 400))
        moveToCenter(self, parent.pos(), parent.size())
        self.setWindowTitle("Select class of new shape")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Textedit
        self.shapeText = QTextEdit(self)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.shapeText.setFont(font)
        self.shapeText.setPlaceholderText("Enter shape label")
        self.shapeText.setMaximumHeight(25)
        self.shapeText.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Buttons
        buttonWidget = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonWidget.button(QDialogButtonBox.Ok).clicked.connect(self.on_ButtonClicked)
        buttonWidget.button(QDialogButtonBox.Cancel).clicked.connect(self.on_ButtonClicked)

        # List of labels
        self.listWidget = ListWidget(self)
        self.listWidget.itemClicked.connect(self.on_ListSelection)

        # Combining everything
        layout.addWidget(self.shapeText)
        layout.addWidget(buttonWidget)
        layout.addWidget(self.listWidget)

        # Fill the listWidget
        for idx, _class in enumerate(parent.classes):
            item = createListWidgetItemWithSquareIcon(_class, parent.colorMap[idx], 10)
            self.listWidget.addItem(item)

    def on_ListSelection(self, item):
        self.class_name = item.text()
        self.setText(item.text())

    def on_ButtonClicked(self):
        self.close()

    def setText(self, text):
        self.shapeText.setText(text)
        # move the cursor to the end
        newCursor = self.shapeText.textCursor()
        newCursor.movePosition(self.shapeText.document().characterCount())
        self.shapeText.setTextCursor(newCursor)


class ForgotToSaveMessageBox(QMessageBox):
    def __init__(self, *args):
        super(ForgotToSaveMessageBox, self).__init__(*args)

        saveButton = QPushButton(getIcon('save'), "Save Changes")
        dismissButton = QPushButton(self.style().standardIcon(QStyle.SP_DialogDiscardButton), "Dismiss Changes")
        cancelButton = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")

        self.setWindowTitle("Caution: Unsaved Changes")
        self.setText("Unsaved Changes: How do you want to progress?")

        # NOTE FOR SOME REASON THE ORDER IS IMPORTANT DESPITE THE ROLE - IDK WHY
        self.addButton(saveButton, QMessageBox.AcceptRole)
        self.addButton(cancelButton, QMessageBox.RejectRole)
        self.addButton(dismissButton, QMessageBox.DestructiveRole)

        moveToCenter(self, self.parentWidget().pos(), self.parentWidget().size())
        
        
class DeleteShapeMessageBox(QMessageBox):
    def __init__(self, shape: str, *args):
        super(DeleteShapeMessageBox, self).__init__(*args)
        moveToCenter(self, self.parentWidget().pos(), self.parentWidget().size())
        reply = self.question(self, "Deleting Shape", f"You are about to delete {shape}. Continue?",
                      QMessageBox.Yes|QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer = 1
        else:
            self.answer = 0


def moveToCenter(widget, parent_pos: QPoint, parent_size: QSize):
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)