from PyQt5.QtWidgets import QListWidget, QMenu, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, QPoint
from PyQt5.QtGui import QColor

from seg_utils.ui.shape import Shape
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon

from typing import List, Union

class ListWidget(QListWidget):
    sRequestContextMenu = pyqtSignal(int, QPoint)

    def __init__(self, *args, is_comment_list=False):
        super(ListWidget, self).__init__(*args)
        self._icon_size = 10
        self.contextMenu = QMenu(self)
        self.is_comment_list = is_comment_list

    def update_list(self, current_label: List[Shape]):
        self.clear()
        if self.is_comment_list:
            for lbl in current_label:
                text = "Details" if lbl.comment else "Add comment"
                item = QListWidgetItem()
                item.setText(text)
                item.setForeground(QColor(0, 102, 204))
                self.addItem(item)
        else:
            for lbl in current_label:
                txt = lbl.label
                col = lbl.line_color
                item = createListWidgetItemWithSquareIcon(txt, col, self._icon_size)
                self.addItem(item)

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        idx = self.row(self.itemAt(pos))
        self.sRequestContextMenu.emit(idx, self.mapToGlobal(pos))

