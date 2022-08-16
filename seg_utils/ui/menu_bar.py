from PyQt5.QtWidgets import QMenuBar, QMainWindow, QMenu
from PyQt5.QtCore import QRect, pyqtSignal

from typing import List

from seg_utils.src.actions import Action


class MenuBar(QMenuBar):
    sNewProject = pyqtSignal()
    sOpenProject = pyqtSignal()
    sCloseProject = pyqtSignal()
    sRequestImport = pyqtSignal()
    sRequestSave = pyqtSignal()
    sRequestSettings = pyqtSignal()

    def __init__(self, parent: QMainWindow):
        super(MenuBar, self).__init__()
        self.setGeometry(QRect(0, 0, 1276, 22))

        self.maf = QMenu("The All-Purpose Labeling Tool")
        self.file = QMenu("File")

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
                             "Quit\nProgram",
                             parent.close,
                             icon="quit",
                             tip="Quit Program")
        action_settings = Action(self,
                                 "Preferences",
                                 self.sRequestSettings.emit,
                                 icon="settings",
                                 tip="Set your preferences for the program",)

        self.file.addActions((action_new_project,
                              action_open_project,
                              action_close_project,
                              action_save,
                              action_import))
        self.maf.addActions((action_settings,
                             action_quit))

        self.addMenu(self.maf)
        self.addMenu(self.file)

        self.enable_tools(["New Project", "Open Project"])

    def enable_tools(self, tools: List[str] = None):
        """enables the tools specified in the list; if no parameter is passed, enable all"""
        if tools:
            for action in self.file.actions():
                if action.text() in tools:
                    action.setEnabled(True)
                else:
                    action.setEnabled(False)
            for action in self.maf.actions():
                if action.text() in tools:
                    action.setEnabled(True)
                else:
                    action.setEnabled(False)
        else:
            for action in self.file.actions():
                action.setEnabled(True)
            for action in self.maf.actions():
                action.setEnabled(True)
