from PyQt5.QtWidgets import (QDialog, QPushButton, QWidget, QLabel,
                             QVBoxLayout, QTextEdit, QHBoxLayout, QDialogButtonBox,
                             QStyle, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap

from seg_utils.ui.list_widget import ListWidget
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon, getIcon


class NewLabelDialog(QDialog):
    def __init__(self, parent: QWidget, *args):
        super(NewLabelDialog, self).__init__(*args)

        # Default values
        self.class_name = ""
        self.parent = parent

        # Create the shape of the QDialog
        self.setFixedSize(QSize(300, 400))
        moveToCenter(self, self.parent.pos(), self.parent.size())
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

        self.fill()

    def fill(self):
        """ get all the current label classes and display them in the dialog """
        self.listWidget.clear()
        for idx, _class in enumerate(self.parent.classes):
            item = createListWidgetItemWithSquareIcon(_class, self.parent.colorMap[idx], 10)
            self.listWidget.addItem(item)

        # last entry in the list is used for creating a new label_class
        item = QListWidgetItem(QIcon('icons/plus.png'), "New")
        self.listWidget.addItem(item)

    def on_ListSelection(self, item):
        """ handles the functions to be executed when user selects something from the list"""
        text = item.text()

        # let user enter a new label class
        if text == "New":
            create_new_class = CreateNewLabelClassDialog(self)
            create_new_class.exec()
            if create_new_class.new_label_class:
                text = create_new_class.new_label_class

                idx = len(self.parent.classes)
                self.parent.classes[text] = idx
                self.fill()

        # use the selected/created label class to name the label
        self.class_name = text
        self.setText(text)

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


class CreateNewLabelClassDialog(QDialog):
    """
    handles a QDialog used to let the user enter a new label class
    """
    def __init__(self, parent: NewLabelDialog):
        super(CreateNewLabelClassDialog, self).__init__()

        self.setFixedSize(QSize(200, 120))
        moveToCenter(self, parent.pos(), parent.size())
        self.setWindowTitle("Create new Shape class")

        # need it later to prevent duplicates
        self.new_label_class = ""
        self.existing_classes = parent.parent.classes

        # Textedit
        self.shapeText = QTextEdit(self)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.shapeText.setFont(font)
        self.shapeText.setPlaceholderText("Enter new Shape name")
        self.shapeText.setMaximumHeight(25)

        # Buttons
        self.buttonWidget = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonWidget.accepted.connect(self.ok_clicked)
        self.buttonWidget.rejected.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(self.shapeText)
        layout.addWidget(self.buttonWidget)

    def ok_clicked(self):
        """ only accepts the new label class if
        (1) the name doesn't already exist and
        (2) the name is not an empty string"""
        name = self.shapeText.toPlainText()
        if name in self.existing_classes:
            self.shapeText.setText("")
            self.shapeText.setPlaceholderText("'{}' already exists".format(name))
        elif name:
            self.new_label_class = name
            self.close()


class SelectFileTypeDialog(QDialog):
    """
    handles a QDialog to let the user select between video, image and whole slide image
    the selected type is the used when importing a new file
    """
    def __init__(self):
        super(SelectFileTypeDialog, self).__init__()

        self.setFixedSize(QSize(250, 150))
        self.setWindowTitle("Select File Type")

        self.filetype = ""
        stylesheet = """QPushButton {
                        background-color: lightgray;
                        color: black;
                        min-height: 2em;
                        border-width: 2px;
                        border-radius: 8px;
                        border-color: black;
                        font: bold 12px;
                        padding: 2px;
                        }
                        QPushButton::hover {
                        background-color: gray;
                        }
                        QPushButton::pressed {
                        border-style: outset;
                        }"""

        # create buttons and apply stylesheet
        v = QPushButton("Video")
        i = QPushButton("Image")
        w = QPushButton("Whole Slide Image")
        v.setStyleSheet(stylesheet)
        i.setStyleSheet(stylesheet)
        w.setStyleSheet(stylesheet)

        # TODO: Extend by other accepted types, substitute 'whatever' by actual WSI type
        v.clicked.connect(lambda: self.set_type("mp4"))
        i.clicked.connect(lambda: self.set_type("png"))
        w.clicked.connect(lambda: self.set_type("whatever"))

        ft_layout = QVBoxLayout(self)
        ft_layout.addWidget(v)
        ft_layout.addWidget(i)
        ft_layout.addWidget(w)

    def set_type(self, t: str):
        """ updates the class variable by the selected filetype"""
        self.filetype = t
        self.close()


def moveToCenter(widget, parent_pos: QPoint, parent_size: QSize):
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)