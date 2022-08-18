from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from seg_utils.ui.dialogs import CommentDialog, DeleteAllMessageBox, DeleteClassMessageBox, DeleteShapeMessageBox
from seg_utils.ui.shape import Shape

from typing import List


class TreeWidgetItem(QTreeWidgetItem):
    def __init__(self, *args, shape: Shape = None):
        super(TreeWidgetItem, self).__init__(*args)
        self.pointer = shape
        self.setFlags(self.flags() | Qt.ItemIsTristate)
        self.setCheckState(0, Qt.Checked)

    def shape(self) -> Shape:
        return self.pointer


class TreeWidget(QTreeWidget):
    """tree widget to display annotations in a list (all at top level)
    second column is used to let user enter or view comments"""
    sItemsDeleted = pyqtSignal(list)
    sDeselectAll = pyqtSignal()
    sChange = pyqtSignal(int)

    def __init__(self):
        super(TreeWidget, self).__init__()

        self.setColumnCount(2)
        self.setFrameShape(QFrame.NoFrame)
        self.setHeaderLabels(["Annotation", "Your notes"])

        self.top = TreeWidgetItem(["Annotations", ""])
        self.addTopLevelItem(self.top)
        self.clicked.connect(self.handle_click)
        self.itemChanged.connect(self.handle_item_changed)
        self.ignore_selection = False

    def delete_item(self, item: QTreeWidgetItem):
        """deletes the given item and all items below its place in the hierarchy"""

        # select the correct MessageBox
        level = self.level_of(item)
        if level == 1:
            dlg = DeleteAllMessageBox()
        elif level == 2:
            dlg = DeleteClassMessageBox(item.text(0))
        elif level == 3:
            dlg = DeleteShapeMessageBox(item.text(0))
        else:
            return
        dlg.exec()

        # emit deletion signal
        if dlg.result() == QMessageBox.Ok:
            self.sChange.emit(1)
            shapes = self.gather_shapes(item)
            self.sItemsDeleted.emit(shapes)

    def gather_shapes(self, cur_item: QTreeWidgetItem) -> List[Shape]:
        """helper method to collect all shapes belonging to the item"""
        shapes = [cur_item.shape()] if cur_item.shape() else list()
        for i in range(cur_item.childCount()):
            shapes += self.gather_shapes(cur_item.child(i))
        return shapes

    def get_item_by_shape(self, shape: Shape) -> QTreeWidgetItem:
        """returns the item in the tree with the corresponding shape reference"""

        def get_item_helper(node: QTreeWidgetItem):
            """helper method to iterate the tree"""
            if node.shape() == shape:
                return node
            else:
                for i in range(node.childCount()):
                    item = get_item_helper(node.child(i))
                    if item:
                        return item
            return None

        return get_item_helper(self.top)

    def handle_click(self, idx: QModelIndex):
        """handles an item click in the QTreeWidget, if user clicked at the right part, open up a comment dialog"""

        # if this function was triggered by a check box, skip
        if self.ignore_selection:
            self.ignore_selection = False
            return
        item = self.itemFromIndex(idx)
        self.sDeselectAll.emit()
        self.set_shapes_selected(item)

        # open comment dialog if necessary
        shape = item.shape()
        if shape and idx.column() == 1:
            comment = shape.comment if shape.comment else ""
            dlg = CommentDialog(comment)
            dlg.exec()

            # detect possible change
            if shape.comment != dlg.comment:
                self.sChange.emit(3)
            # store the dialog result
            text = "Details" if dlg.comment else "Add comment"
            item.setText(1, text)
            shape.comment = dlg.comment

    def handle_item_changed(self, item: QTreeWidgetItem, column: int):
        """this function gets triggered when user clicks the checkbox; set corresponding shapes visible/hidden"""
        # ignore changes on the comment section
        if column == 1:
            return

        state = item.checkState(column)
        if state == Qt.Checked:
            visible = True
        elif state == Qt.Unchecked:
            visible = False
        else:  # intermediate State - not done by user
            return
        for shape in self.gather_shapes(item):
            shape.setVisible(visible)
        self.ignore_selection = True

    def level_of(self, item: QTreeWidgetItem) -> int:
        """returns the level of the given item in the tree"""

        def level_helper(node: QTreeWidgetItem) -> int:
            """recursive helper method to retrieve the level of an item based on 'node' as starting point"""
            if node == item:
                return 1
            for i in range(node.childCount()):
                level = level_helper(node.child(i))
                if level != 0:
                    return 1 + level
            return 0

        return level_helper(self.top)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super(TreeWidget, self).mousePressEvent(event)
        if event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            if item:
                self.sDeselectAll.emit()
                self.set_shapes_selected(item)

                # open context menu
                pos = event.globalPos()
                menu = QMenu()
                action = QAction("Delete")
                action.triggered.connect(lambda: self.delete_item(item))
                menu.addAction(action)
                menu.exec(pos)

    def set_shapes_selected(self, item: QTreeWidgetItem):
        """sets all shapes belonging to this item selected"""
        shape = item.shape()
        if shape:
            shape.setSelected(True)
        else:
            for i in range(item.childCount()):
                self.set_shapes_selected(item.child(i))

    def shape_selected(self, shape: Shape):
        """selects the item with the corresponding index in the poly list"""
        for item in self.selectedItems():
            item.setSelected(False)
        item = self.get_item_by_shape(shape)
        item.setSelected(True)

    def update_polygons(self, current_labels: List[Shape]):
        """updates the treeWidget with the specified labels"""

        # memorize which items were expanded before updating
        expanded_items = list()
        if self.top.isExpanded():
            for i in range(self.top.childCount()):
                child = self.top.child(i)
                if child.isExpanded():
                    expanded_items.append(child.text(0))

        for i in reversed(range(self.top.childCount())):
            self.top.removeChild(self.top.child(i))

        # add the label classes as intermediate level
        label_classes = list()
        for lbl in current_labels:
            txt = lbl.label
            if txt not in label_classes:
                label_classes.append(txt)
                item = TreeWidgetItem([txt, ""])
                self.top.addChild(item)
                if txt in expanded_items:
                    item.setExpanded(True)

        # add the annotations to their label classes
        for lbl in current_labels:
            txt = lbl.label
            txt2 = "Details" if lbl.comment else "Add comment"
            col = lbl.line_color
            icon = create_square_icon(col)

            item = TreeWidgetItem([txt, txt2], shape=lbl)
            item.setIcon(0, icon)
            for i in range(self.top.childCount()):
                child = self.top.child(i)
                if child.text(0) == txt:
                    if not lbl.isVisible():
                        item.setCheckState(0, Qt.Unchecked)
                    child.addChild(item)


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

