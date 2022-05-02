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
        self.database = None  # type: SQLiteDatabase
        self.images = []
        self.current_labels = []
        self.classes = {}
        self.img_idx = 0
        self.connect_events()

        self.main_window.show()

    def connect_events(self):
        self.main_window.toolBar.sCreateNewProject.connect(self.create_new_project)

    def create_new_project(self, data: list):
        """ Creates a project environment on the user's machine and initializes a database"""
        project_path, files = data[0], data[1]
        create_project_structure(project_path)
        db_path = project_path + Structure.DATABASE_DEFAULT_NAME
        self.init_with_database(db_path, files)

    def init_with_database(self, database: str, files: dict = None):
        """This function is called if a correct database is selected"""
        self.database = SQLiteDatabase(database)

        # if the project was newly created, user may have specified patients & files to add
        if files:
            for file, patient in files.items():
                self.database.add_patient(patient)
                # self.add_file(file, patient)

        self.images = self.database.get_images()
        # self.init_colors()
        # self.init_classes()
        # self.init_file_list(True)
        # self.enable_actions(['Save', 'Import', 'QuitProgram'])

        """if self.images:
            self.image_display.set_initialized()
            self.init_image()
            self.enable_actions()"""
