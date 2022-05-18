from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from seg_utils.ui.image_display import CenterDisplayWidget
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.ui.shape import Shape
from seg_utils.src.actions import Action
from seg_utils.ui.list_widgets_new import FileViewingWidget, LabelsViewingWidget
from seg_utils.utils.qt import colormap_rgb
from seg_utils.utils.project_structure import Structure

NUM_COLORS = 25


class LabelingMainWindow(QMainWindow):
    """The main window for the application"""
    def __init__(self):
        super(LabelingMainWindow, self).__init__()
        self.setWindowTitle("The All-Purpose Labeling Tool")
        self.resize(1276, 968)
        self.setTabShape(QTabWidget.Rounded)

        # The main widget set as focus. Based on a horizontal layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(QHBoxLayout())
        self.main_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.main_widget.layout().setSpacing(0)

        # Center Frame of the body where the image will be displayed in
        self.center_frame = QFrame()
        self.center_frame.setAutoFillBackground(False)
        self.center_frame.setFrameShape(QFrame.NoFrame)
        self.center_frame.setFrameShadow(QFrame.Raised)
        self.center_frame.setLayout(QVBoxLayout())
        self.center_frame.layout().setContentsMargins(0, 0, 0, 0)
        self.center_frame.layout().setSpacing(0)

        # TODO: The center frame should be given a widget to say "No files to display". This should not be handled
        #       within the ImageDisplay widget
        self.no_files = QLabel()
        self.no_files.setText("No files to display")
        self.no_files.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display = CenterDisplayWidget()
        self.image_display.setHidden(True)

        self.center_frame.layout().addWidget(self.image_display)
        self.center_frame.layout().addWidget(self.no_files)

        # Right Menu
        self.right_menu_widget = QWidget()
        self.right_menu_widget.setMaximumWidth(200)
        self.right_menu_widget.setLayout(QVBoxLayout())
        self.right_menu_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.right_menu_widget.layout().setSpacing(0)

        # the labels, polygon and file lists
        self.labels_list = LabelsViewingWidget()
        self.poly_frame = PolyFrame()
        self.file_list = FileViewingWidget()
        self.right_menu_widget.layout().addWidget(self.labels_list)
        self.right_menu_widget.layout().addWidget(self.poly_frame)
        self.right_menu_widget.layout().addWidget(self.file_list)

        self.main_widget.layout().addWidget(self.center_frame)
        self.main_widget.layout().addWidget(self.right_menu_widget)
        self.setCentralWidget(self.main_widget)

        self.menubar = QMenuBar()
        self.menubar.setGeometry(QRect(0, 0, 1276, 22))
        self.setMenuBar(self.menubar)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.toolBar = Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.init_margins()
        self.toolBar.init_actions(self)

        # TODO: if possible, get rid of such variables
        self.img_idx = 0

    def initialize(self, files: list, classes: list, labels: list, location: str):
        color_map, new_color = colormap_rgb(n=NUM_COLORS)
        self.labels_list.label_list.update_with_classes(classes, color_map)
        if files:
            self.file_list.update_list(files, self.img_idx)
            self.image_display.set_initialized()

            filepath = location + Structure.IMAGES_DIR + files[0]
            current_labels = [Shape(image_size=self.image_size, label_dict=_label,
                                    color=self.get_color_for_label(_label['label']))
                              for _label in labels]
            self.poly_frame.update_frame(current_labels)
            self.image_display.init_image(filepath, current_labels)
            self.set_default(False)

    def set_default(self, is_empty: bool):
        """ either hides the default label or the image display"""
        self.image_display.setHidden(is_empty)
        self.no_files.setHidden(not is_empty)

