from PyQt5.QtWidgets import QMenuBar, QMessageBox, QMainWindow, QMenu
from PyQt5.QtCore import QRect, pyqtSignal

from pathlib import Path

from seg_utils.src.actions import Action
from seg_utils.ui.dialogs import ProjectHandlerDialog
from seg_utils.utils.project_structure import Structure, check_environment


class MenuBar(QMenuBar):

    sCreateNewProject = pyqtSignal(str, dict)
    sOpenProject = pyqtSignal(str)
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
                                    self.new_project,
                                    'Ctrl+N',
                                    "new",
                                    "New project")
        action_open_project = Action(self,
                                     "Open Project",
                                     self.open_project,
                                     'Ctrl+O',
                                     "open",
                                     "Open project")
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

        action_save.setEnabled(False)
        action_import.setEnabled(False)

        self.file.addActions((action_new_project,
                              action_open_project,
                              action_save,
                              action_import))
        self.maf.addActions((action_settings,
                             action_quit))

        self.addMenu(self.maf)
        self.addMenu(self.file)

    def enable_project_tools(self):
        for action in self.file.actions():
            if action.text() == "Save" or action.text() == "Import File":
                action.setEnabled(True)
            else:
                action.setEnabled(False)

    def new_project(self):
        """executes a dialog prompting the user to enter information about the new project"""
        dlg = ProjectHandlerDialog()
        dlg.exec()
        if dlg.project_path:
            database_path = dlg.project_path + Structure.DATABASE_DEFAULT_NAME
            self.sCreateNewProject.emit(database_path, dlg.files)
            self.enable_project_tools()

    def open_project(self):
        """executes a dialog prompting the user to select a database"""
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
                self.enable_project_tools()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Invalid Project Location")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
