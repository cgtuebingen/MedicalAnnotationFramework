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
        self.main_window.toolBar.sCreateNewProject.connect(self.database.initialize)
        self.main_window.toolBar.sAddFile.connect(self.database.add_file)

        self.database.sInitialized.connect(self.main_window.initialize)
