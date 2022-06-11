import pickle
import os
import pathlib
import shutil

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from typing import Tuple, List, Union
from numpy import argmax

from seg_utils.utils.database import SQLiteDatabase
from seg_utils.utils import qt
from seg_utils.utils.project_structure import Structure, create_project_structure, check_environment, modality
from seg_utils.src.actions import Action
from seg_utils.ui.main_window_new import LabelingMainWindow
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs_new import (NewLabelDialog, ForgotToSaveMessageBox, DeleteShapeMessageBox,
                                      CloseMessageBox, SelectPatientDialog, ProjectHandlerDialog,
                                      CommentDialog, DeleteClassMessageBox)
from seg_utils.config import VERTEX_SIZE


class MainLogic:
    def __init__(self):

        # active elements
        self.main_window = LabelingMainWindow()
        self.database = SQLiteDatabase()
        self.connect_events()

        self.main_window.show()

    def connect_events(self):
        self.main_window.menubar.sCreateNewProject.connect(self.database.initialize)
        self.main_window.menubar.sOpenProject.connect(self.database.initialize)
        self.main_window.menubar.sRequestImport.connect(self.database.send_import_info)

        self.main_window.file_list.sRequestFileChange.connect(self.main_window.change_file)

        self.main_window.image_display.hide_button.clicked.connect(self.main_window.hide_toolbar)
        self.main_window.sSaveToDatabase.connect(self.database.save)

        self.main_window.sAddFile.connect(self.database.add_file)
        self.main_window.sAddPatient.connect(self.database.add_patient)
        self.main_window.sRequestUpdate.connect(self.database.update_gui)
        self.main_window.sRequestCheckForChanges.connect(self.database.send_changes_info)

        self.database.sUpdate.connect(self.main_window.update_window)
        self.database.sImportFile.connect(self.main_window.import_file)
        self.database.sCheckForChanges.connect(self.main_window.image_display.check_for_changes)
