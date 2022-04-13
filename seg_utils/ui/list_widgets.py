from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from typing import List

from seg_utils.ui.shape import Shape
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon
from seg_utils.ui.misc_dialogs import CommentDialog


STYLESHEET = """QListWidget {
                color: rgb(0, 102, 204);
                selection-color: blue;
                selection-background-color: white;
                }
                QListWidget::item:hover {
                color: blue;
                }"""


class ListWidget(QListWidget):
    # TODO: change this to a QTreeWidget with 2 columns

    def __init__(self, *args, is_comment_list=False):
        super(ListWidget, self).__init__(*args)
        self._icon_size = 10
        self.is_comment_list = is_comment_list
        if self.is_comment_list:
            self.setStyleSheet(STYLESHEET)
            self.itemClicked.connect(self.handle_click)
        self.itemClicked.connect(self.item_selected)

    @pyqtSlot(QListWidgetItem)
    def item_selected(self, item: QListWidgetItem):
        shape = item.data(Qt.UserRole)
        # TODO: This check needs to be deleted once this widget isn't used for a lot of different things
        if shape is None:
            return
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == shape:
                item.data(Qt.UserRole).setSelected(True)
            else:
                item.data(Qt.UserRole).setSelected(False)

    @pyqtSlot()
    def on_shape_selected(self):
        shape = self.sender()
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == shape:
                item.setSelected(True)
                break

    @pyqtSlot()
    def on_shape_deselected(self):
        shape = self.sender()
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == shape:
                item.setSelected(False)
                break

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        idx = self.row(self.itemAt(pos))

    def update_list(self, current_label: List[Shape]):
        self.clear()
        if self.is_comment_list:
            for lbl in current_label:
                text = "Details" if lbl.comment else "Add comment"
                item = QListWidgetItem()
                item.setData(Qt.UserRole, lbl)  # store reference to shape so it can be used later
                item.setText(text)
                self.addItem(item)
        else:
            for lbl in current_label:
                txt = lbl.label
                col = lbl.line_color
                item = createListWidgetItemWithSquareIcon(txt, col, self._icon_size)
                item.setData(Qt.UserRole, lbl)    # store reference to shape so it can be used later
                self.addItem(item)

        for lbl in current_label:
            lbl.selected.connect(self.on_shape_selected)
            lbl.deselected.connect(self.on_shape_deselected)

    def handle_click(self, item: QListWidgetItem):
        """Either shows a blank comment window or the previously written comment for this label"""
        comment = ""
        data = item.data(Qt.UserRole)
        if data is not None:
            if item.text() != "Add comment" and item.data(Qt.UserRole).comment is not None:
                comment = item.data(Qt.UserRole).comment

        dlg = CommentDialog(comment)
        dlg.exec()

        text = "Details" if dlg.comment else "Add comment"
        item.setText(text)
        item.data(Qt.UserRole).comment = dlg.comment


class LabelsViewingWidget(QWidget):
    def __init__(self):
        super(LabelsViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("Labels")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.file_label)
        self.label_list = ListWidget()
        self.label_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.layout().addWidget(self.label_list)


class FileViewingWidget(QWidget):
    itemClicked = pyqtSignal(QListWidgetItem)
    search_text_changed = pyqtSignal()

    def __init__(self):
        super(FileViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("File List")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.file_label)
        self.search_field = QTextEdit()

        # Size Policy
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.search_field.sizePolicy().hasHeightForWidth())
        self.search_field.setSizePolicy(size_policy)
        self.search_field.setMaximumHeight(25)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)

        self.search_field.setFont(font)
        self.search_field.setFrameShadow(QFrame.Sunken)
        self.search_field.setLineWidth(0)
        self.search_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setCursorWidth(1)
        self.search_field.setPlaceholderText("Search Filename")
        self.search_field.setObjectName("fileSearch")
        self.layout().addWidget(self.search_field)

        self.file_list = ListWidget()
        self.file_list.setIconSize(QSize(7, 7))
        self.file_list.setItemAlignment(Qt.AlignmentFlag.AlignLeft)
        self.file_list.setObjectName("fileList")
        self.layout().addWidget(self.file_list)

        # TODO: This should all be done within this widget. There should be little need for outside connections
        self.file_list.itemClicked.connect(self.itemClicked.emit)
        self.search_field.textChanged.connect(self.search_text_changed.emit)