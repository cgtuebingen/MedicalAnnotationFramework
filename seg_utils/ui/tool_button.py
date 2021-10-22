from PyQt5.QtWidgets import QToolButton
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt


class ToolbarButton(QToolButton):
    def __init__(self, *args):
        super(ToolbarButton, self).__init__(*args)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.isChecked():
            self.setChecked(Qt.Unchecked)
        else:
            self.setChecked(Qt.Checked)

        self.defaultAction().triggered.emit()