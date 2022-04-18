from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from seg_utils.ui.image_display import ImageDisplay
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.src.actions import Action
from seg_utils.ui.list_widgets import FileViewingWidget, LabelsViewingWidget


class LabelingMainWindow(QMainWindow):
    """The main window for the application"""
    def __init__(self):
        super(LabelingMainWindow, self).__init__()
        self.resize(1276, 968)
        self.setTabShape(QTabWidget.Rounded)

        # The main widget set as focus. Based on a horizontal layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(QHBoxLayout())
        self.main_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.main_widget.layout().setSpacing(0)

        self.setCentralWidget(self.main_widget)
