from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from seg_utils.ui.dialogs import CommentDialog, DeleteShapeMessageBox
from seg_utils.ui.shape import Shape

from typing import List


class TreeWidget(QTreeWidget):
    """tree widget to display annotations in a list (all at top level)
    second column is used to let user enter or view comments"""
    sItemClicked = pyqtSignal(int)
    sUpdateLabels = pyqtSignal(list)

    def __init__(self):
        super(TreeWidget, self).__init__()

        self.setColumnCount(2)
        self.setFrameShape(QFrame.NoFrame)
        self.setHeaderLabels(["Annotation", "Your notes"])
        self.current_labels = list()
        self.clicked.connect(self.handle_click)

    def delete_item(self, item: QTreeWidgetItem):
        """deletes a given item from the tree and updates the label shapes"""
        dlg = DeleteShapeMessageBox(item.text(0))
        if dlg.answer == 1:
            root = self.invisibleRootItem()
            idx = root.indexOfChild(item)
            root.removeChild(item)
            self.current_labels.pop(idx)
            self.sUpdateLabels.emit(self.current_labels)

    def handle_click(self, idx: QModelIndex):
        """handles an item click in the QTreeWidget, if user clicked at the right part, open up a comment dialog"""
        row, column = idx.row(), idx.column()

        if column == 0:
            self.sItemClicked.emit(row)
        elif column == 1:
            lbl = self.current_labels[row]
            comment = lbl.comment if lbl.comment else ""
            dlg = CommentDialog(comment)
            dlg.exec()

            # store the dialog result
            text = "Details" if dlg.comment else "Add comment"
            item = self.itemFromIndex(idx)
            item.setText(column, text)
            self.current_labels[row].comment = dlg.comment
            self.sUpdateLabels.emit(self.current_labels)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super(TreeWidget, self).mousePressEvent(event)
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            if item:
                # set corresponding item in display selected
                root = self.invisibleRootItem()
                idx = root.indexOfChild(item)
                self.sItemClicked.emit(idx)

                # open context menu
                pos = event.globalPos()
                menu = QMenu()
                action = QAction("Delete")
                action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(action)
                menu.exec(pos)

    def shape_selected(self, idx: int):
        """selects the item with the corresponding index in the poly list"""
        for item in self.selectedItems():
            item.setSelected(False)

        root = self.invisibleRootItem()
        select_item = root.child(idx)
        select_item.setSelected(True)

    def update_polygons(self, current_labels: List[Shape]):
        """updates the treeWidget with the specified labels"""
        self.current_labels = current_labels

        self.clear()
        for lbl in current_labels:
            txt = lbl.label
            txt2 = "Details" if lbl.comment else "Add comment"
            col = lbl.line_color
            icon = create_square_icon(col)

            item = QTreeWidgetItem([txt, txt2])
            item.setIcon(0, icon)
            self.addTopLevelItem(item)


def create_square_icon(color: QColor, size: int = 10) -> QIcon:
    pixmap = QPixmap(size, size)
    painter = QPainter()
    painter.begin(pixmap)
    painter.setPen(color)
    painter.setBrush(color)
    painter.drawRect(QRect(0, 0, size, size))
    icon = QIcon(pixmap)
    painter.end()
    return icon

