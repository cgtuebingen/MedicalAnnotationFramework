from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs_new import CommentDialog

from typing import List


class PolyFrame(QWidget):
    """
    This class is used to build up the part in the right menu of the GUI
    where the currently created Polygons are displayed.

    Provides a clickable "Add comment" text next to each polygon item.
    """

    sUpdateLabels = pyqtSignal(list)
    itemClicked = pyqtSignal(int)
    itemDeleted = pyqtSignal()

    def __init__(self, *args):
        super(PolyFrame, self).__init__(*args)
        self.setMinimumSize(QSize(0, 300))
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.current_labels = []

        # header line for the polyFrame
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.label.setText("Polygons")
        self.label.setAlignment(Qt.AlignCenter)

        # QTreeWidget for displaying annotations and comments
        self.polygons = QTreeWidget()
        self.polygons.setColumnCount(2)
        self.polygons.setFrameShape(QFrame.NoFrame)
        self.polygons.setCursor((QCursor(Qt.PointingHandCursor)))
        self.polygons.setHeaderLabels(["Annotation", "Your notes"])
        self.polygons.clicked.connect(self.handle_click)

        self.layout().addWidget(self.label)
        self.layout().addWidget(self.polygons)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        pos = event.pos()
        menu = QMenu()

        action = QAction("Delete")
        action.triggered.connect(self.itemDeleted.emit)
        menu.addAction(action)

        menu.exec(pos)

    def handle_click(self, idx: QModelIndex):
        """handles an item click in the QTreeWidget, if user clicked at the right part, open up a comment dialog"""
        row, column = idx.row(), idx.column()

        if column == 0:
            self.itemClicked.emit(row)
        elif column == 1:
            lbl = self.current_labels[row]
            comment = lbl.comment if lbl.comment else ""
            dlg = CommentDialog(comment)
            dlg.exec()

            # store the dialog result
            text = "Details" if dlg.comment else "Add comment"
            item = self.polygons.itemFromIndex(idx)
            item.setText(column, text)
            self.current_labels[row].comment = dlg.comment
            self.sUpdateLabels.emit(self.current_labels)

    def shape_selected(self, idx: int):
        """selects the item with the corresponding index in the poly list"""
        # TODO: Does not work yet, find out how items in qtreewidget can be indexed
        model_idx = QModelIndex()
        item = self.polygons.itemFromIndex(model_idx)
        # item.setSelected(True)

    def update_frame(self, current_labels: List[Shape]):
        """updates the treeWidget with the specified labels"""
        self.current_labels = current_labels

        self.polygons.clear()
        for lbl in current_labels:
            txt = lbl.label
            txt2 = "Details" if lbl.comment else "Add comment"
            col = lbl.line_color
            icon = create_square_icon(col)

            item = QTreeWidgetItem([txt, txt2])
            item.setIcon(0, icon)
            self.polygons.addTopLevelItem(item)


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
