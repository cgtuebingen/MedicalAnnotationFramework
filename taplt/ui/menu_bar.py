from PySide6.QtWidgets import *
from PySide6.QtCore import *

from typing import List

from taplt.src.actions import Action


class MenuBar(QMenuBar):
    sNewProject = Signal()
    sOpenProject = Signal()
    sCloseProject = Signal()
    sRequestImport = Signal()
    sRequestSave = Signal()
    sRequestSettings = Signal()
    sExampleProject = Signal()
    sPreviewDatabase = Signal(str)

    def __init__(self, parent: QMainWindow):
        super(MenuBar, self).__init__()
        self.setGeometry(QRect(0, 0, 1276, 22))
        self.setNativeMenuBar(False)

        self.maf = QMenu("TAPLT")
        self.project = QMenu("Project")
        self.edit = QMenu("Edit")
        self.macros = QMenu("Macros")
        self.preview = QMenu("Preview Database")

        action_new_project = Action(self,
                                    "New Project",
                                    self.sNewProject.emit,
                                    'Ctrl+N',
                                    "new",
                                    "New project")
        action_open_project = Action(self,
                                     "Open Project",
                                     self.sOpenProject.emit,
                                     'Ctrl+O',
                                     "open",
                                     "Open project")
        action_close_project = Action(self,
                                      "Close Project",
                                      self.sCloseProject.emit,
                                      'Ctrl+C',
                                      "close",
                                      "Close Project")
        action_save = Action(self,
                             "Save",
                             self.sRequestSave.emit,
                             'Ctrl+S',
                             "save",
                             "Save current state to database")
        action_import = Action(self,
                               "Import File",
                               self.sRequestImport.emit,
                               'Ctrl+I',
                               "import",
                               "Import a new file to database")
        action_quit = Action(self,
                             "Quit Program",
                             parent.close,
                             icon="quit",
                             tip="Quit Program")
        action_settings = Action(self,
                                 "Preferences",
                                 self.sRequestSettings.emit,
                                 icon="settings",
                                 tip="Set your preferences for the program",)

        macros_example_project = Action(self,
                                        "Example Project",
                                        self.sExampleProject.emit)
        macros_preview_annotations = Action(self,
                                            "Annotations",
                                            lambda: self.sPreviewDatabase.emit("Annotations"))
        macros_preview_images = Action(self,
                                       "Images",
                                       lambda: self.sPreviewDatabase.emit("Images"))
        macros_preview_patients = Action(self,
                                         "Patients",
                                         lambda: self.sPreviewDatabase.emit("Patients"))
        macros_preview_classes = Action(self,
                                        "Labels",
                                        lambda: self.sPreviewDatabase.emit("Labels"))

        self.actions = [action_new_project,
                        action_open_project,
                        action_close_project,
                        action_save,
                        action_import,
                        action_quit,
                        action_settings,
                        macros_example_project,
                        macros_preview_annotations,
                        macros_preview_images,
                        macros_preview_patients,
                        macros_preview_classes]

        self.maf.addActions((action_settings,
                             action_quit))

        self.project.addActions((action_new_project,
                                 action_open_project,
                                 action_close_project))

        self.edit.addActions((action_save,
                              action_import))
        self.macros.addAction(macros_example_project)
        self.preview.addActions((macros_preview_annotations,
                                 macros_preview_images,
                                 macros_preview_patients,
                                 macros_preview_classes))
        self.macros.addMenu(self.preview)

        self.addMenu(self.maf)
        self.addMenu(self.project)
        self.addMenu(self.edit)
        self.addMenu(self.macros)

        self.enable_tools(["New Project", "Open Project", "Quit Program", "Example Project"])

    def enable_tools(self, tools: List[str] = None):
        """enables the tools specified in the list; if no parameter is passed, enable all"""
        if tools:
            for action in self.actions:
                if action.text() in tools:
                    action.setEnabled(True)
                else:
                    action.setEnabled(False)
        else:
            for action in self.actions:
                action.setEnabled(True)
