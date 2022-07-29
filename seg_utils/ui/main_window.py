from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from pathlib import Path

from seg_utils.ui.image_display import CenterDisplayWidget
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.dialogs import SelectPatientDialog, CloseMessageBox, DeleteFileMessageBox
from seg_utils.ui.menu_bar import MenuBar
from seg_utils.ui.list_widgets import FileViewingWidget, LabelsViewingWidget
from seg_utils.ui.tree_widget import TreeWidget
from seg_utils.utils.qt import colormap_rgb, get_icon

NUM_COLORS = 25


class LabelingMainWindow(QMainWindow):
    """The main window for the application"""

    sAddPatient = pyqtSignal(str)
    sAddFile = pyqtSignal(str, str)
    sRequestUpdate = pyqtSignal(int)
    sRequestCheckForChanges = pyqtSignal(int, int)
    sSaveToDatabase = pyqtSignal(list, int)#
    sDeleteFile = pyqtSignal(str, int)

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

        # default widget while no project has been loaded
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

        # the label, polygons and file lists
        self.labels_list = LabelsViewingWidget()
        self.polygons = TreeWidget()
        self.file_list = FileViewingWidget()

        # widget for the polygons
        self.poly_widget = QWidget()
        self.poly_widget.setMinimumSize(QSize(0, 300))
        self.poly_widget.setLayout(QVBoxLayout())
        self.poly_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.poly_widget.layout().setSpacing(0)
        self.poly_label = QLabel(self)
        self.poly_label.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.poly_label.setText("Polygons")
        self.poly_label.setAlignment(Qt.AlignCenter)
        self.poly_widget.layout().addWidget(self.poly_label)
        self.poly_widget.layout().addWidget(self.polygons)

        self.right_menu_widget.layout().addWidget(self.labels_list)
        self.right_menu_widget.layout().addWidget(self.poly_widget)
        self.right_menu_widget.layout().addWidget(self.file_list)

        self.main_widget.layout().addWidget(self.center_frame)
        self.main_widget.layout().addWidget(self.right_menu_widget)
        self.setCentralWidget(self.main_widget)

        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.toolBar = Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.init_margins()
        self.toolBar.init_actions(self)
        self.toolBar.setHidden(True)

        # TODO: if possible, get rid of such variables
        self.img_idx = 0
        self.closeMe = False

        # connect signals
        self.image_display.sRequestSave.connect(self.save_to_database)
        self.image_display.sChangeFile.connect(self.change_file)
        self.image_display.image_viewer.sNextFile.connect(self.next_image)
        self.image_display.annotations.updateShapes.connect(self.polygons.update_polygons)
        self.image_display.annotations.shapeSelected.connect(self.polygons.shape_selected)
        self.file_list.sDeleteFile.connect(self.delete_file)
        self.file_list.sRequestFileChange.connect(self.file_list_item_clicked)
        self.polygons.sItemsDeleted.connect(self.image_display.annotations.remove_shapes)
        self.polygons.sDeselectAll.connect(self.image_display.annotations.deselect_all)
        self.menubar.sRequestSave.connect(self.save_to_database)
        self.toolBar.sSetDrawingMode.connect(self.image_display.annotations.set_mode)

    def change_file(self, img_idx: int):
        """changes the displayed file to the file with the specified index
        a img_idx of -1 indicates a closing request"""
        if img_idx == -1:
            dlg = CloseMessageBox()
            dlg.exec()
            if dlg.result() == QMessageBox.AcceptRole:
                self.closeMe = True
        else:
            self.img_idx = img_idx
            self.sRequestUpdate.emit(img_idx)

    def closeEvent(self, event, final_close: bool = False):
        self.sRequestCheckForChanges.emit(self.img_idx, -1)
        if self.closeMe:
            event.accept()
        else:
            event.ignore()

    def delete_file(self, filename):
        dlg = DeleteFileMessageBox(filename)
        dlg.exec()

        if dlg.result() == QMessageBox.Ok:
            self.sDeleteFile.emit(filename, self.img_idx)

    def file_list_item_clicked(self, new_img_idx: int):
        self.sRequestCheckForChanges.emit(self.img_idx, new_img_idx)

    def hide_toolbar(self):
        """hides or shows the toolbar"""
        if self.toolBar.isHidden():
            self.toolBar.setHidden(False)
            self.image_display.hide_button.setIcon(get_icon("prev"))
        else:
            self.toolBar.setHidden(True)
            self.image_display.hide_button.setIcon(get_icon("next"))

    def import_file(self, existing_patients: list):
        """executes a dialog to let the user enter all information regarding file import"""
        dlg = SelectPatientDialog(existing_patients)
        dlg.exec()
        patient = dlg.result

        if patient:
            filepath, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=str(Path.home()),)
            # options = QFileDialog.DontUseNativeDialog
            if filepath:
                self.sAddFile.emit(filepath, patient)
                self.sRequestUpdate.emit(self.img_idx)

    def next_image(self, direction: int):
        if not self.image_display.is_empty():
            new_img_idx = (self.img_idx + direction) % self.file_list.image_list.count()
            self.sRequestCheckForChanges.emit(self.img_idx, new_img_idx)

    def save_to_database(self):
        annotations = list(self.image_display.annotations.annotations.values())
        self.sSaveToDatabase.emit(annotations, self.img_idx)

    def set_default(self, is_empty: bool):
        """ either hides the default label or the image display"""
        self.image_display.setHidden(is_empty)
        self.no_files.setHidden(not is_empty)

    def update_window(self, files: list, img_idx, patient: str, classes: list, labels: list):
        self.img_idx = img_idx
        color_map, new_color = colormap_rgb(n=NUM_COLORS)
        self.labels_list.label_list.update_with_classes(classes, color_map)
        self.file_list.update_list(files, self.img_idx)

        if files:
            self.set_default(False)
            current_labels = self.image_display.init_image(files[self.img_idx], patient, labels, classes)
            self.polygons.update_polygons(current_labels)
        else:
            self.set_default(True)
