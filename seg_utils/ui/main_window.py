from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from pathlib import Path
from dataclasses import dataclass

from seg_utils.ui.image_display import CenterDisplayWidget
from seg_utils.ui.toolbar import Toolbar
from seg_utils.ui.dialogs import (SelectPatientDialog, CloseMessageBox, DeleteFileMessageBox,
                                  ForgotToSaveMessageBox, SettingDialog, ProjectHandlerDialog)
from seg_utils.ui.menu_bar import MenuBar
from seg_utils.ui.list_widgets import FileViewingWidget, LabelsViewingWidget
from seg_utils.ui.tree_widget import TreeWidget
from seg_utils.ui.welcome_screen import WelcomeScreen
from seg_utils.utils.qt import colormap_rgb, get_icon
from seg_utils.utils.project_structure import check_environment, Structure

NUM_COLORS = 25


class LabelingMainWindow(QMainWindow):
    """The main window for the application"""

    sCreateNewProject = pyqtSignal(str, dict)
    sOpenProject = pyqtSignal(str)
    sAddPatient = pyqtSignal(str)
    sAddFile = pyqtSignal(str, str)
    sRequestUpdate = pyqtSignal(int)
    sRequestCheckForChanges = pyqtSignal(int, int)
    sSaveToDatabase = pyqtSignal(list, int)
    sDeleteFile = pyqtSignal(str, int)
    sUpdateSettings = pyqtSignal(list)
    sDisconnect = pyqtSignal()

    @dataclass
    class Changes:
        ANNOTATION_ADDED: int = 0
        ANNOTATION_DELETED: int = 1
        ANNOTATION_SHIFTED: int = 2
        COMMENT: int = 3

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

        self.welcome_screen = WelcomeScreen()
        self.image_display = CenterDisplayWidget()

        # default widget when no images exist in the project
        self.no_files = QLabel()
        self.no_files.setText("No files to display")
        self.no_files.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.center_frame.layout().addWidget(self.image_display)
        self.center_frame.layout().addWidget(self.no_files)
        self.center_frame.layout().addWidget(self.welcome_screen)

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

        # TODO: if possible, get rid of such variables
        self.img_idx = 0
        self.changes = list()
        self.autoSave = False

        self.set_welcome_screen(True)

        # connect signals
        self.image_display.sRequestSave.connect(self.save_to_database)
        self.image_display.image_viewer.sNextFile.connect(self.next_image)
        self.image_display.annotations.updateShapes.connect(self.polygons.update_polygons)
        self.image_display.annotations.shapeSelected.connect(self.polygons.shape_selected)
        self.image_display.annotations.sChange.connect(self.change_detected)
        self.file_list.sDeleteFile.connect(self.delete_file)
        self.file_list.sRequestFileChange.connect(self.file_list_item_clicked)
        self.polygons.sItemsDeleted.connect(self.image_display.annotations.remove_shapes)
        self.polygons.sDeselectAll.connect(self.image_display.annotations.deselect_all)
        self.polygons.sChange.connect(self.change_detected)
        self.menubar.sRequestSave.connect(self.save_to_database)
        self.menubar.sNewProject.connect(self.new_project)
        self.menubar.sOpenProject.connect(self.open_project)
        self.menubar.sCloseProject.connect(self.close_project)
        self.toolBar.sSetDrawingMode.connect(self.image_display.annotations.set_mode)

    def apply_settings(self, settings: list):
        """applies the settings"""
        for setting in settings:
            if setting[0] == "Autosave on file change":
                self.autoSave = setting[1]
            elif setting[0] == "Mark annotated files":
                self.file_list.show_check_box = setting[1]
                self.sRequestUpdate.emit(self.img_idx)
            elif setting[0] == "Display patient name":
                self.image_display.patient_label.setVisible(setting[1])
        self.sUpdateSettings.emit(settings)

    def change_detected(self, change: int):
        """appends the detected change to the changes list"""
        if change not in self.changes:
            self.changes.append(change)

    def check_for_changes(self) -> bool:
        """ asks whether user wants to save; returns False on cancellation"""
        if self.changes:
            dlg = ForgotToSaveMessageBox()
            dlg.exec()
            if dlg.result() == QMessageBox.AcceptRole or dlg.result() == QMessageBox.DestructiveRole:
                if dlg.result() == QMessageBox.AcceptRole:
                    self.save_to_database()
                else:
                    self.changes.clear()
                return True
            else:
                return False
        else:
            return True

    def closeEvent(self, event):
        if self.check_for_changes():
            dlg = CloseMessageBox()
            dlg.exec()
            if dlg.result() == QMessageBox.AcceptRole:
                event.accept()
            else:
                event.ignore()

    def close_project(self):
        """this function closes the project, but not the program itself - return to the welcome screen"""
        if self.check_for_changes():
            self.set_welcome_screen(True)
            self.menubar.enable_tools(["New Project", "Open Project"])
            self.sDisconnect.emit()

    def delete_file(self, filename):
        """asks for user consent, emits a signal to permanently delete a project file"""
        dlg = DeleteFileMessageBox(filename)
        dlg.exec()

        if dlg.result() == QMessageBox.Ok:
            self.sDeleteFile.emit(filename, self.img_idx)

    def file_list_item_clicked(self, new_img_idx: int):
        """switches to the image clicked by the user"""
        if self.autoSave:
            self.save_to_database()
            self.img_idx = new_img_idx
            self.sRequestUpdate.emit(new_img_idx)
        elif self.check_for_changes():
            self.img_idx = new_img_idx
            self.sRequestUpdate.emit(new_img_idx)

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
                if self.check_for_changes():
                    self.sAddFile.emit(filepath, patient)
                    self.sRequestUpdate.emit(self.img_idx)

    def new_project(self):
        """executes a dialog prompting the user to enter information about the new project"""
        if self.check_for_changes():
            dlg = ProjectHandlerDialog()
            dlg.exec()
            if dlg.project_path:
                database_path = dlg.project_path + Structure.DATABASE_DEFAULT_NAME
                self.sCreateNewProject.emit(database_path, dlg.files)
                self.menubar.enable_tools()

    def open_project(self):
        """executes a dialog prompting the user to select a database"""
        if self.check_for_changes():
            """database, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select Database",
                                                      directory=str(Path.home()),
                                                      filter="Database (*.db)",
                                                      options=QFileDialog.DontUseNativeDialog)"""
            database = '/Users/jakob/AnnotationProjects/project14/database.db'
            if database:

                # make sure the database is inside a project environment
                if check_environment(str(Path(database).parents[0])):
                    self.sOpenProject.emit(database)
                    self.menubar.enable_tools()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Invalid Project Location")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec()

    def open_settings(self, settings: list):
        """opens up the settings dialog, sends signal to save them"""
        dlg = SettingDialog(settings)
        dlg.exec()
        s = dlg.settings
        if dlg.settings:
            self.apply_settings(dlg.settings)

    def next_image(self, direction: int):
        """proceeds to the next/previous image"""
        if not self.image_display.is_empty():
            new_img_idx = (self.img_idx + direction) % self.file_list.image_list.count()
            if self.autoSave:
                self.save_to_database()
                self.img_idx = new_img_idx
                self.sRequestUpdate.emit(new_img_idx)
            elif self.check_for_changes():
                self.img_idx = new_img_idx
                self.sRequestUpdate.emit(new_img_idx)

    def save_to_database(self):
        """stores the current state of the image to the database"""
        annotations = list(self.image_display.annotations.annotations.values())
        self.changes.clear()
        self.sSaveToDatabase.emit(annotations, self.img_idx)

    def set_no_files_screen(self, b: bool):
        """ either hides the default label or the image display"""
        self.image_display.setHidden(b)
        self.no_files.setHidden(not b)

    def set_welcome_screen(self, b: bool):
        """sets or removes the welcome screen displayed when no project is opened"""
        self.image_display.setHidden(b)
        self.no_files.setHidden(b)
        self.toolBar.setHidden(b)
        self.right_menu_widget.setHidden(b)
        self.welcome_screen.setHidden(not b)

    def update_window(self, files: list, img_idx, patient: str, classes: list, labels: list):
        """main updating function: all necessary information is passed to the main window"""
        self.img_idx = img_idx
        color_map, new_color = colormap_rgb(n=NUM_COLORS)
        self.labels_list.label_list.update_with_classes(classes, color_map)
        self.file_list.update_list(files, self.img_idx)
        self.set_welcome_screen(False)
        if files:
            self.set_no_files_screen(False)
            current_labels = self.image_display.init_image(files[self.img_idx][0], patient, labels, classes)
            self.polygons.update_polygons(current_labels)
        else:
            self.set_no_files_screen(True)
