from PyQt5.QtWidgets import QListWidget, QMenu
from PyQt5.QtCore import pyqtSignal, QPoint

from seg_utils.ui.shape import Shape
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon

from typing import List, Union

class ListWidget(QListWidget):
    sRequestContextMenu = pyqtSignal(int, QPoint)

    def __init__(self, *args):
        super(ListWidget, self).__init__(*args)
        self._icon_size = 10
        self.contextMenu = QMenu(self)

    def updateList(self, current_label: List[Shape]):
        self.clear()
        for lbl in current_label:
            txt = lbl.label
            col = lbl.line_color
            item = createListWidgetItemWithSquareIcon(txt, col, self._icon_size)
            self.addItem(item)

    def contextMenuEvent(self, event) -> None:
        pos = event.pos()
        idx = self.row(self.itemAt(pos))
        self.sRequestContextMenu.emit(idx, self.mapToGlobal(pos))

