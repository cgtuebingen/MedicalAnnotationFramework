from PySide6.QtWidgets import *
from PySide6.QtCore import *

from pathlib import Path
from dataclasses import dataclass
from taplt.src.actions import Action

from taplt.ui.file_display import CenterDisplayWidget
from taplt.ui.toolbar import Toolbar
from taplt.ui.dialogs import (SelectPatientDialog, CloseMessageBox, DeleteFileMessageBox,
                              ForgotToSaveMessageBox, SettingDialog, ProjectHandlerDialog)
from taplt.ui.menu_bar import MenuBar
from taplt.ui.list_widgets import FileViewingWidget, LabelsViewingWidget
from taplt.ui.annotation_tree import AnnotationTree
from taplt.ui.welcome_screen import WelcomeScreen
from taplt.utils.qt import colormap_rgb, get_icon
from taplt.utils.project_structure import check_environment, Structure
from taplt.macros.macros import Macros
from taplt.macros.macros_dialogs import PreviewDatabaseDialog

NUM_COLORS = 25

class LabelingMainWindow(QMainWindow):
    """The main window for the application"""

    sCreateNewProject = Signal(str, dict)
    sOpenProject = Signal(str)
    sAddPatient = Signal(str)
    sAddFile = Signal(str, str)
    sRequestUpdate = Signal(int)
    sRequestCheckForChanges = Signal(int, int)
    sSaveToDatabase = Signal(list, int)
    sDeleteFile = Signal(str, int)
    sUpdateSettings = Signal(list)
    sDisconnect = Signal()

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
        self.setTabShape(QTabWidget.TabShape.Rounded)

        # The main widget set as focus. Based on a horizontal layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(QHBoxLayout())
        self.main_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.main_widget.layout().setSpacing(0)

        # Center Frame of the body where the image will be displayed in
        self.center_frame = QFrame()
        self.center_frame.setAutoFillBackground(False)
        self.center_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.center_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.center_frame.setLayout(QVBoxLayout())
        self.center_frame.layout().setContentsMargins(0, 0, 0, 0)
        self.center_frame.layout().setSpacing(0)

        self.welcome_screen = WelcomeScreen()
        self.file_display = CenterDisplayWidget()

        # default widget when no images exist in the project
        self.no_files = QLabel()
        self.no_files.setText("No files to display")
        self.no_files.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.center_frame.layout().addWidget(self.file_display)
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
        self.polygons = AnnotationTree()
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
        self.poly_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.menubar.setVisible(True)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.toolBar = Toolbar(self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        self.toolBar.init_margins()

        # Toolbar setup actions for images, videos and whole slides
        self.toolBar.init_actions('image', self.define_img_actions())
        self.toolBar.init_actions('slide', self.define_wsi_actions())
        self.toolBar.init_actions('video', self.define_video_actions())
        self.file_display.modalitySwitched.connect(self.toolBar.switch_modality)

        # Show tooltip while drawing
        self.file_display.sDrawingTooltip.connect(self.set_tool_tip)

        # TODO: if possible, get rid of such variables
        self.img_idx = 0
        self.changes = list()
        self.autoSave = False

        self.macros = Macros()
        self.set_welcome_screen(True)

        # connect signals
        self.file_display.sRequestSave.connect(self.save_to_database)
        self.file_display.image_viewer.sNextFile.connect(self.next_image)
        self.file_display.annotations.updateShapes.connect(self.polygons.update_polygons)
        self.file_display.annotations.shapeSelected.connect(self.polygons.shape_selected)
        self.file_display.annotations.sChange.connect(self.change_detected)
        self.file_list.sDeleteFile.connect(self.delete_file)
        self.file_list.sRequestFileChange.connect(self.file_list_item_clicked)
        self.polygons.sItemsDeleted.connect(self.file_display.annotations.remove_shapes)
        self.polygons.sDeselectAll.connect(self.file_display.annotations.deselect_all)
        self.polygons.sChange.connect(self.change_detected)
        self.macros.sEnableTools.connect(self.menubar.enable_tools)
        self.macros.sNewProject.connect(self.sCreateNewProject.emit)
        self.macros.sSetWelcomeScreen.connect(self.set_welcome_screen)

        self.menubar.sRequestSave.connect(self.save_to_database)
        self.menubar.sNewProject.connect(self.new_project)
        self.menubar.sOpenProject.connect(self.open_project)
        self.menubar.sCloseProject.connect(self.close_project)
        self.menubar.sExampleProject.connect(self.macros.example_project)

    def set_tool_tip(self, tip: str):
        # TODO: This is kind of working, but not really. You have to hover out of the display widget.
        self.main_widget.setStatusTip(tip)
        self.main_widget.setToolTip(tip)

    def apply_settings(self, settings: list):
        """applies the settings"""
        for setting in settings:
            if setting[0] == "Autosave on file change":
                self.autoSave = setting[1]
            elif setting[0] == "Mark annotated files":
                self.file_list.show_check_box = setting[1]
                self.sRequestUpdate.emit(self.img_idx)
            elif setting[0] == "Display patient name":
                self.file_display.patient_label.setVisible(setting[1])
        self.sUpdateSettings.emit(settings)

    def change_detected(self, change: int):
        """appends the detected change to the changes list"""
        if change not in self.changes:
            self.changes.append(change)

    def check_for_changes(self) -> bool:
        """ asks whether user wants to save; returns False on cancellation"""
        if self.changes:
            dlg = ForgotToSaveMessageBox()
            dlg.show()
            dlg.exec()
            if dlg.result() in {0, 2}:
                if dlg.result() == 0:
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
            if dlg.clickedButton() == dlg.quit_button:
                super(LabelingMainWindow, self).closeEvent(event)
            else:
                event.ignore()

    def close_project(self):
        """this function closes the project, but not the program itself - return to the welcome screen"""
        if self.check_for_changes():
            self.set_welcome_screen(True)
            self.menubar.enable_tools(["New Project", "Open Project", "Quit Program", "Example Project"])
            self.sDisconnect.emit()

    def delete_file(self, filename):
        """asks for user consent, emits a signal to permanently delete a project file"""
        dlg = DeleteFileMessageBox(filename)
        dlg.exec()

        if dlg.result() == QMessageBox.StandardButton.Ok:
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
            self.file_display.hide_button.setIcon(get_icon("prev"))
        else:
            self.toolBar.setHidden(True)
            self.file_display.hide_button.setIcon(get_icon("next"))

    def import_file(self, existing_patients: list):
        """executes a dialog to let the user enter all information regarding file import"""
        dlg = SelectPatientDialog(existing_patients)
        dlg.exec()
        patient = dlg.result

        if patient:
            filepath, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=str(Path.home()), )
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
                self.set_welcome_screen(False)
                self.menubar.enable_tools()

    def open_project(self):
        """executes a dialog prompting the user to select a database"""
        if self.check_for_changes():
            database, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select Database",
                                                      dir=str(Path.home()),
                                                      filter="Database (*.db)",
                                                      options=QFileDialog.Option.DontUseNativeDialog)
            if database:

                # make sure the database is inside a project environment
                if check_environment(str(Path(database).parents[0])):
                    self.sOpenProject.emit(database)
                    self.set_welcome_screen(False)
                    self.menubar.enable_tools()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setText("Invalid Project Location")
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
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
        if not self.file_display.is_empty():
            new_img_idx = (self.img_idx + direction) % self.file_list.image_list.count()
            if self.autoSave:
                self.save_to_database()
                self.img_idx = new_img_idx
                self.sRequestUpdate.emit(new_img_idx)
            elif self.check_for_changes():
                self.img_idx = new_img_idx
                self.sRequestUpdate.emit(new_img_idx)

    def preview_database(self, headers: list, content: list):
        """displays the database content of the specified table in a dialog"""
        dlg = PreviewDatabaseDialog(headers, content)
        dlg.exec()

    def save_to_database(self):
        """stores the current state of the image to the database"""
        annotations = list(self.file_display.annotations.annotations.values())
        self.changes.clear()
        self.sSaveToDatabase.emit(annotations, self.img_idx)

    def set_no_files_screen(self, b: bool):
        """ either hides the default label or the image display"""
        self.file_display.setHidden(b)
        self.no_files.setHidden(not b)

    def set_welcome_screen(self, b: bool):
        """sets or removes the welcome screen displayed when no project is opened"""
        self.file_display.setHidden(b)
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
        if files:
            self.set_no_files_screen(False)
            current_labels = self.file_display.init_image(files[self.img_idx][0], patient, labels, classes)
            self.polygons.update_polygons(current_labels)
        else:
            self.set_no_files_screen(True)

    def define_img_actions(self):
        actions = (Action(self,
                          "Select",
                          lambda: (self.file_display.annotations.set_mode(0),
                                   self.file_display.annotations.set_type('polygon')),
                          icon="mouse",
                          tip="Select items in the image",
                          checkable=True,
                          checked=True),
                   Action(self,
                          "Draw\nPolygon",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('polygon')),
                          icon="polygon",
                          tip="Draw Polygon",
                          checkable=True),
                   Action(self,
                          "Draw\nTrace",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('trace')),
                          icon="outline",
                          tip="Trace Outline",
                          checkable=True),
                   Action(self,
                          "Draw\nEllipse",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('ellipse')),
                          icon="ellipse",
                          tip="Draw Ellipse",
                          checkable=True),
                    Action(self,
                          "Draw\nCircle",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('circle')),
                          icon="circle",
                          tip="Draw Circle",
                          checkable=True),
                   Action(self,
                          "Draw\nRectangle",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('rectangle')),
                          icon="square",
                          tip="Draw Rectangle",
                          checkable=True))
        actions = list(actions)
        return actions

    def define_wsi_actions(self):
        actions = (Action(self,
                          "Select",
                          lambda: (self.file_display.annotations.set_mode(0),
                                   self.file_display.annotations.set_type('polygon'),
                                   self.file_display.slide_viewer.setAnnotationMode(False)),
                          icon="mouse",
                          tip="Select items in the image",
                          checkable=True,
                          checked=True),
                   Action(self,
                          "Draw\nPolygon",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('polygon'),
                                   self.file_display.slide_viewer.setAnnotationMode(True)),
                          icon="polygon",
                          tip="Draw Polygon",
                          checkable=True),
                   Action(self,
                          "Draw\nTrace",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('trace'),
                                   self.file_display.slide_viewer.setAnnotationMode(True)),
                          icon="outline",
                          tip="Trace Outline",
                          checkable=True),
                   Action(self,
                          "Draw\nEllipse",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('ellipse'),
                                   self.file_display.slide_viewer.setAnnotationMode(True)),
                          icon="ellipse",
                          tip="Draw Ellipse",
                          checkable=True),
                    Action(self,
                          "Draw\nCircle",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('circle'),
                                   self.file_display.slide_viewer.setAnnotationMode(True)),
                          icon="circle",
                          tip="Draw Circle",
                          checkable=True),
                   Action(self,
                          "Draw\nRectangle",
                          lambda: (self.file_display.annotations.set_mode(1),
                                   self.file_display.annotations.set_type('rectangle'),
                                   self.file_display.slide_viewer.setAnnotationMode(True)),
                          icon="square",
                          tip="Draw Rectangle",
                          checkable=True))
        actions = list(actions)
        return actions

    def define_video_actions(self):
        actions = (Action(self,
                          "Play",
                          lambda: self.file_display.video_player.play(),
                          icon="play",
                          tip="Play the video",
                          checkable=True,
                          checked=True),
                   Action(self,
                          "Pause",
                          lambda: self.file_display.video_player.pause(),
                          icon="pause",
                          tip="Pause the video",
                          checkable=True),
                   Action(self,
                          "Grab",
                          lambda: self.file_display.video_player.grab_frame(),
                          icon="magnifying_glass",
                          tip="Grab the frame",
                          checkable=True),
                   Action(self,
                          "Pause and\ngrab",
                          lambda: self.file_display.video_player.pause_and_grab(),
                          icon="image",
                          tip="Pause the video and grab the frame",
                          checkable=True)
                   )
        actions = list(actions)
        return actions
