from PySide6.QtCore import *

from taplt.macros.macros_dialogs import ExampleProjectDialog, ExampleProjectMessageBox

from pathlib import Path
import os


class Macros(QObject):
    sNewProject = Signal(str, dict)
    sEnableTools = Signal(list)
    sSetWelcomeScreen = Signal(bool)

    def __init__(self):
        super(Macros, self).__init__()

    def example_project(self):
        """lets the user choose a directory containing some images and creates a project with them"""
        dlg = ExampleProjectDialog()
        dlg.exec()
        if dlg.accepted:
            database_path = str(Path.home()) + "/ExampleProject/database.db"

            # collect all example files and assign a patient name
            examples_path = os.path.dirname(__file__) + "/examples/images/"
            files = os.listdir(examples_path)
            files = [examples_path + file for file in files if not file.startswith(".")]
            files_dict = dict()
            for i in range(len(files)):
                patient = "Patient {}".format(str(i))
                files_dict[files[i]] = patient

            # create a project with limited functions
            self.sSetWelcomeScreen.emit(False)
            self.sNewProject.emit(database_path, files_dict)
            self.sEnableTools.emit(["Quit Program", "Preferences",
                                    "Close Project", "Save",
                                    "Annotations", "Images",
                                    "Patients", "Labels"])

            project_path = str(Path(database_path).parents[0])
            msg = ExampleProjectMessageBox(project_path)
            msg.exec()
