from PyQt5.QtWidgets import QMenuBar, QFileDialog, QMessageBox
from PyQt5.QtCore import QRect, pyqtSignal

from pathlib import Path

from seg_utils.src.actions import Action
from seg_utils.ui.dialogs_new import ProjectHandlerDialog
from seg_utils.utils.project_structure import Structure, check_environment


class MenuBar(QMenuBar):

    sCreateNewProject = pyqtSignal(str, dict)
    sOpenProject = pyqtSignal(str)
    sRequestImport = pyqtSignal()
    sRequestSave = pyqtSignal()

    def __init__(self):
        super(MenuBar, self).__init__()
        self.setGeometry(QRect(0, 0, 1276, 22))

        self.file = self.addMenu("File")
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

        self.file.addActions((action_new_project,
                              action_open_project,
                              action_save,
                              action_import))

    def new_project(self):
        """executes a dialog prompting the user to enter information about the new project"""
        dlg = ProjectHandlerDialog()
        dlg.exec()
        if dlg.project_path:
            database_path = dlg.project_path + Structure.DATABASE_DEFAULT_NAME
            self.sCreateNewProject.emit(database_path, dlg.files)

    def open_project(self):
        """executes a dialog prompting the user to select a database"""
        database, _ = QFileDialog.getOpenFileName(self,
                                                  caption="Select Database",
                                                  directory=str(Path.home()),
                                                  filter="Database (*.db)",
                                                  options=QFileDialog.DontUseNativeDialog)
        if database:

            # make sure the database is inside a project environment
            if check_environment(str(Path(database).parents[0])):
                self.sOpenProject.emit(database)
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Invalid Project Location")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()