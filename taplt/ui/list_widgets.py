from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import os
from typing import List

from taplt.ui.shape import Shape
from taplt.utils.qt import createListWidgetItemWithSquareIcon, get_icon
from taplt.utils.stylesheets import TAB_STYLESHEET, SETTING_STYLESHEET


class FileList(QListWidget):
    """ a list widget subclass to make use of context menu"""
    sDeleteFile = Signal(str)

    def __init__(self):
        super(FileList, self).__init__()
        self.setIconSize(QSize(11, 11))
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setItemAlignment(Qt.AlignmentFlag.AlignLeft)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu()
            action = QAction("Delete")
            action.triggered.connect(lambda: self.sDeleteFile.emit(item.text()))
            menu.addAction(action)
            menu.exec(event.globalPos())


class LabelList(QListWidget):
    """ a list widget to store annotation labels"""
    def __init__(self, *args):
        super().__init__(*args)
        self._icon_size = 10
        self.setFrameShape(QFrame.Shape.NoFrame)

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        item = self.itemAt(pos)
        if item:
            menu = QMenu()
            action = QAction("Delete")
            menu.addAction(action)
            global_pos = event.globalPos()
            menu.exec(global_pos)

    def update_with_classes(self, classes: List[str], color_map: List[QColor]):
        """ fills the list widget with the given class names and their corresponding colors"""
        self.clear()
        for idx, _class in enumerate(classes):
            item = createListWidgetItemWithSquareIcon(_class, color_map[idx], self._icon_size)
            self.addItem(item)

    def update_with_labels(self, labels: List[Shape]):
        """ fills the list widget with the given shape objects """
        self.clear()
        for lbl in labels:
            txt = lbl.label
            col = lbl.line_color
            item = createListWidgetItemWithSquareIcon(txt, col, self._icon_size)
            self.addItem(item)


class LabelsViewingWidget(QWidget):
    """ a widget to hold a LabelList displaying the (unique) label class names"""
    def __init__(self):
        super(LabelsViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("Labels")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.file_label)
        self.label_list = LabelList()
        self.label_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.layout().addWidget(self.label_list)


class FileViewingWidget(QWidget):
    """ holds a QTabWidget to be able to display both images and whole slide images"""
    itemClicked = Signal(QListWidgetItem)
    sRequestFileChange = Signal(int)
    sDeleteFile = Signal(str)

    def __init__(self):
        super(FileViewingWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.file_label = QLabel()
        self.file_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.file_label.setText("File List")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.file_label)

        self.tab = QTabWidget()
        self.tab.setContentsMargins(0, 0, 0, 0)
        self.tab.setStyleSheet(TAB_STYLESHEET)
        self.search_field = QTextEdit()

        # Size Policy
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.search_field.sizePolicy().hasHeightForWidth())
        self.search_field.setSizePolicy(size_policy)
        self.search_field.setMaximumHeight(25)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)

        self.search_field.setFont(font)
        self.search_field.setFrameShadow(QFrame.Shadow.Sunken)
        self.search_field.setLineWidth(0)
        self.search_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_field.setCursorWidth(1)
        self.search_field.setPlaceholderText("Search Filename")
        self.search_field.setObjectName("fileSearch")
        self.layout().addWidget(self.search_field)

        self.image_list = FileList()
        self.wsi_list = FileList()
        self.show_check_box = False

        self.tab.addTab(self.image_list, 'Images')
        self.tab.addTab(self.wsi_list, 'WSI')
        self.layout().addWidget(self.tab)

        self.image_list.itemClicked.connect(self.file_selected)
        self.image_list.sDeleteFile.connect(self.sDeleteFile.emit)
        self.search_field.textChanged.connect(self.search_text_changed)

    def file_selected(self):
        """gets the index of the selected file and emits a signal"""
        idx2 = self.image_list.currentRow()
        self.sRequestFileChange.emit(idx2)

    def get_img_idx(self, filename: str) -> int:
        """ searches through the ListWidget and returns the index of the item with the filename / -1 if not found"""
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.text() == filename:
                return i
        return -1

    def update_list(self, files: list, img_idx: int):
        """ clears the list widget and fills it again with the provided filenames"""
        self.image_list.clear()
        for file in files:
            filename = os.path.basename(file[0])

            # display check box if image is populated with at least 1 annotation
            if self.show_check_box and file[1]:
                icon = get_icon("checked")
                item = QListWidgetItem(icon, filename)
            else:
                item = QListWidgetItem(filename)
            self.image_list.addItem(item)
        if self.image_list.count() > 0:
            self.image_list.setCurrentRow(img_idx)

    def search_text_changed(self):
        """ filters the list regarding the user input in the search field"""
        cur_text = self.search_field.toPlainText()
        cur_list = self.tab.currentWidget()

        for idx in range(cur_list.count()):
            item = cur_list.item(idx)
            if cur_text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)


class SettingList(QListWidget):
    def __init__(self, settings):
        super(SettingList, self).__init__()
        self.setSpacing(5)
        self.setStyleSheet(SETTING_STYLESHEET)
        for setting in settings:
            item = QListWidgetItem(setting[0])
            checked = Qt.CheckState.Checked if setting[1] else Qt.CheckState.Unchecked
            item.setCheckState(checked)
            item.setToolTip(setting[2])
            self.addItem(item)
