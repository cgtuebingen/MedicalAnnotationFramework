import pickle
import os
import pathlib
import shutil

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from typing import Tuple, List, Union

from seg_utils.utils.database import SQLiteDatabase
from seg_utils.utils import qt
from seg_utils.utils.project_structure import Structure, create_project_structure, check_environment, modality
from seg_utils.src.actions import Action
from seg_utils.ui.main_window import LabelingMainWindow
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs import (NewLabelDialog, ForgotToSaveMessageBox, DeleteShapeMessageBox,
                                  CloseMessageBox, SelectPatientDialog, ProjectHandlerDialog, DeleteClassMessageBox)
from seg_utils.config import VERTEX_SIZE


class MainLogic(LabelingMainWindow):
    """
    TODO: This logic should be made more modularized and not wrap the GUI.
    """
    sLabelSelected = pyqtSignal(int, int, int)
    CREATE, EDIT = 0, 1

    def __init__(self):
        super(MainLogic, self).__init__()

        # placeholder variables that can be used later
        self.database = None  # type: SQLiteDatabase
        self.project_location = None  # type: str
        self.images = []
        self.current_labels = []
        self.classes = {}
        self.isLabeled = None
        self.img_idx = 0
        self.b_autoSave = True
        self.context_menu = QMenu(self)
        self._selection_idx = -1  # helpful for contextmenu references
        self.image_size = QSize()

        # color stuff
        self._num_colors = 25  # number of colors
        self.colorMap = None  # type: List[QColor]

        self._FD_Dir = '../examples'
        self._FD_Opt = QFileDialog.DontUseNativeDialog

        self.connect_events()
        self.init_context_menu()
        self.tool_bar.disable_drawing(True)

        self.vertex_size = VERTEX_SIZE

    def add_file(self, filepath: str, patient: str):
        """ This method copies a selected file to the project environment and updates the database """

        # copy file
        dest = self.project_location + Structure.IMAGES_DIR
        shutil.copy(filepath, dest)

        # add the filename to database
        filename = os.path.basename(filepath)
        mod = modality(filepath)
        self.database.add_file(filename, mod, patient)

    def check_for_changes(self, quit_program: bool = True) -> int:
        r"""Check for changes with the database and display dialogs if necessary
            :returns: 0 if accepted or no changes, 1 if cancelled and 2 if dismissed
        """
        if self.images:
            sql_labels = self.database.get_label_from_imagepath(self.images[self.img_idx])
            sql_labels = [Shape(image_size=self.image_size,
                                label_dict=_label,
                                color=self.get_color_for_label(_label['label']))
                          for _label in sql_labels]

            if sql_labels == self.current_labels:
                if not quit_program:
                    return 0
                else:
                    d = CloseMessageBox(self)
            else:
                d = ForgotToSaveMessageBox(self)
        else:
            d = CloseMessageBox(self)
        d.exec()
        return d.result()

    def class_is_used(self, class_name: str) -> bool:
        """This function checks for a given label class
        whether there are annotations of that class in any of the current files"""
        for i in range(len(self.images)):
            if i != self.img_idx:
                labels = self.database.get_label_from_imagepath(self.images[i])
                for lbl in labels:
                    if lbl['label'] == class_name:
                        return True
        return False

    def closeEvent(self, event) -> None:
        dlg_result = self.check_for_changes()
        if dlg_result == QMessageBox.AcceptRole or dlg_result == QMessageBox.DestructiveRole:
            if dlg_result == QMessageBox.AcceptRole:
                self.on_save()
        else:
            event.ignore()

    def connect_events(self):
        """ this method comprises the connect statements for functionality of the GUI parts"""
        # TODO: A lot of these should be handled within their owning widgets.
        self.file_list.itemClicked.connect(self.handle_file_list_item_clicked)
        self.file_list.search_text_changed.connect(self.handle_file_list_search)
        self.poly_frame.polygon_list.itemClicked.connect(self.handle_poly_list_selection)
        self.image_display.sRequestLabelListUpdate.connect(self.handle_update_poly_list)

        # toolbar actions
        self.tool_bar.get_action("NewProject").triggered.connect(self.on_new_project)
        self.tool_bar.get_action("OpenProject").triggered.connect(lambda: self.on_open_project(self._FD_Dir,
                                                                                               self._FD_Opt))
        self.tool_bar.get_action("Save").triggered.connect(self.on_save)
        self.tool_bar.get_action("Import").triggered.connect(lambda: self.on_import(self._FD_Dir, self._FD_Opt))
        self.tool_bar.get_action("NextImage").triggered.connect(lambda: self.on_next_image(True))
        self.tool_bar.get_action("PreviousImage").triggered.connect(lambda: self.on_next_image(False))
        self.tool_bar.get_action("DrawTrace").toggled.connect(lambda: self.on_draw_start('tempTrace'))
        self.tool_bar.get_action("DrawPolygon").toggled.connect(lambda: self.on_draw_start('tempPolygon'))
        self.tool_bar.get_action("DrawCircle").toggled.connect(lambda: self.on_draw_start('circle'))
        self.tool_bar.get_action("DrawRectangle").toggled.connect(lambda: self.on_draw_start('rectangle'))
        self.tool_bar.get_action("QuitProgram").triggered.connect(self.close)

        # ContextMenu
        self.image_display.scene.sRequestContextMenu.connect(self.on_request_shape_menu)
        self.poly_frame.polygon_list.sRequestContextMenu.connect(self.on_request_shape_menu)
        self.labels_list.label_list.sRequestContextMenu.connect(self.on_request_class_menu)
        self.file_list.file_list.sRequestContextMenu.connect(self.on_request_files_menu)

        # Drawing Events
        self.image_display.scene.sDrawing.connect(self.on_drawing)
        self.image_display.scene.sDrawingDone.connect(self.on_draw_end)

        # Altering Shape Events
        self.image_display.scene.sMoveVertex.connect(self.on_move_vertex)
        self.image_display.scene.sMoveShape.connect(self.on_move_shape)
        self.image_display.scene.sRequestAnchorReset.connect(self.on_anchor_rest)

    def create_annotation_entry(self, label_dict: dict, label_class: str) -> dict:
        """
        creates a dictionary that can be used as an entry for the annotations table in the database
        :param label_dict: all information regarding the Shape object of the annotation
        :param label_class: class of the label
        :return: a dictionary used as an entry to the database
        """
        filename = self.images[self.img_idx]
        modality, file = self.database.get_uids_from_filename(filename)
        label_class = self.database.get_uid_from_label(label_class)
        patient = self.database.get_patient_by_filename(filename)

        return {'modality': modality,
                'file': file,
                'patient': patient,
                'shape': pickle.dumps(label_dict),
                'label': label_class}

    def enable_actions(self, actions: List[str] = None):
        """enables the specified actions. If no actions are specified, enable all"""
        if actions:
            for act in actions:
                self.tool_bar.get_widget_for_action(act).setEnabled(True)
        else:
            self.tool_bar.disable_drawing(False)

        # TODO: this disables the Open & New Database Button as i only need it once
        #   and currently it crashes everything if clicked again
        self.tool_bar.get_widget_for_action('NewProject').setEnabled(False)
        self.tool_bar.get_widget_for_action('OpenProject').setEnabled(False)

    def get_color_for_label(self, label_name: str):
        r"""Get a Color based on a label_name"""
        if label_name not in self.classes.keys():
            return None
        label_index = self.classes[label_name]
        return self.colorMap[label_index]

    def handle_file_list_item_clicked(self):
        """Tracks the changed item in the label List"""

        # if user clicked on currently displayed file in the list, do nothing
        if self.img_idx == self.images.index(self.file_list.currentItem().text()):
            return

        # else save changes if necessary
        dlg_result = self.check_for_changes(quit_program=False)
        if dlg_result == QMessageBox.AcceptRole or dlg_result == QMessageBox.DestructiveRole:
            if dlg_result == QMessageBox.AcceptRole:
                self.on_save()
            self.img_idx = self.images.index(self.file_list.currentItem().text())
            self.init_image()
        else:
            self.file_list.setCurrentRow(self.img_idx)

    def handle_file_list_search(self):
        r"""Handles the file search. If the user types into the text box, it changes the files which are displayed"""
        text = self.file_search.toPlainText()
        for item_idx in range(self.file_list.count()):
            if text not in self.file_list.item(item_idx).text():
                self.file_list.item(item_idx).setHidden(True)
            else:
                self.file_list.item(item_idx).setHidden(False)

    def handle_poly_list_selection(self, item):
        r"""Returns the row index within the list such that the plotter in canvas can update it"""
        idx, _ = self.poly_frame.get_index_from_selected(item)
        self.sLabelSelected.emit(idx, idx, -1)

    def handle_update_poly_list(self, _item_idx):
        """ updates the polyList """
        for _idx in range(self.poly_frame.polygon_list.count()):
            self.poly_frame.polygon_list.item(_idx).setSelected(False)
        self.poly_frame.polygon_list.item(_item_idx).setSelected(True)

    def init_classes(self):
        """This function initializes the available classes in the database and updates the label list"""
        self.labels_list.label_list.clear()
        classes = self.database.get_label_classes()
        for idx, _class in enumerate(classes):
            item = qt.createListWidgetItemWithSquareIcon(_class, self.colorMap[idx], 10)
            self.labels_list.label_list.addItem(item)
            self.classes[_class] = idx

    def init_colors(self):
        r"""Initialise the colors for plotting and for the individual lists """
        self.colorMap, new_color = qt.colormap_rgb(n=self._num_colors)  # have a buffer for new classes
        self.image_display.draw_new_color = new_color

    def init_context_menu(self):
        """ Initializes the functionality of the context_menu"""
        action_edit_label = Action(self,
                                   "Edit Label Name",
                                   self.on_edit_label,
                                   icon="pen",
                                   tip="Edit Label Name")
        action_delete_label = Action(self,
                                     "Delete Label",
                                     self.on_delete_label,
                                     icon="trash",
                                     tip="Delete Label")
        action_delete_class = Action(self,
                                     "Delete Label Class",
                                     self.on_delete_class,
                                     icon="trash",
                                     tip="Delete Label Class")
        action_delete_file = Action(self,
                                    "Delete File",
                                    self.on_delete_file,
                                    icon="trash",
                                    tip="Delete file")

        self.context_menu.addActions((action_edit_label,
                                      action_delete_label,
                                      action_delete_class,
                                      action_delete_file))

    def init_file_list(self, show_check_box=False):
        r"""Initialize the file list with all the entries found in the database"""
        self.file_list.file_list.clear()
        for idx, elem in enumerate(self.images):
            if show_check_box:
                icon = qt.get_icon("checked")
                item = QListWidgetItem(icon,
                                       self.images[idx].replace(Structure.IMAGES_DIR, ""))
            else:
                item = QListWidgetItem(self.images[idx].replace(Structure.IMAGES_DIR, ""))
            self.file_list.file_list.addItem(item)
        self.file_list.file_list.setCurrentRow(self.img_idx)

    def init_image(self):
        """Initializes the displayed image and respective label/canvas"""
        image = QPixmap(self.project_location + Structure.IMAGES_DIR + self.images[self.img_idx])
        self.image_size = image.size()
        self.init_labels()
        self.image_display.init_image(image, self.current_labels)
        self.file_list.file_list.setCurrentRow(self.img_idx)

    def init_labels(self):
        r"""This function initializes the labels for the current image. Necessary to have only one call to the database
        if the image is changed"""
        labels = self.database.get_label_from_imagepath(self.images[self.img_idx]) if self.images else []
        self.current_labels = [Shape(image_size=self.image_size, label_dict=_label,
                                     color=self.get_color_for_label(_label['label']))
                               for _label in labels]
        self.poly_frame.update_frame(self.current_labels)

    def init_with_database(self, database: str, patients: list = None, files: dict = None):
        """This function is called if a correct database is selected"""
        self.database = SQLiteDatabase(database)

        # if the project was newly created, user may have specified patients & files to add
        if patients:
            for p in patients:
                self.database.add_patient(p)
        if files:
            for file, patient in files.items():
                self.add_file(file, patient)

        self.images = self.database.get_images()
        self.init_colors()
        self.init_classes()
        self.init_file_list(True)
        self.enable_actions(['Save', 'Import', 'QuitProgram'])
        self.tool_bar.disable_drawing(True)
        if self.images:
            self.image_display.set_initialized()
            self.init_image()
            self.enable_actions()

    def on_anchor_rest(self, v_shape: int):
        """Handles the reset of the anchor upon the mouse release within the respective label/shape"""
        if self.current_labels:
            self.current_labels[v_shape].reset_anchor()

    def on_delete_class(self):
        """This function is the handle for deleting a user-specified label class"""
        keys = list(self.classes.keys())
        class_name = keys[self._selection_idx]
        msg = DeleteClassMessageBox(class_name=class_name)
        msg.exec()

        # 0 cancel
        # 1 delete only the annotations of that class
        # 2 delete the whole label class
        if msg.answer in (1, 2):

            # first create a list, then remove these items to prevent indexing errors
            remove_list = [lbl for lbl in self.current_labels if lbl.label == class_name]
            for lbl in remove_list:
                self.current_labels.remove(lbl)

            if msg.answer == 2:
                # check for annotations of that class in other images
                if self.class_is_used(class_name):
                    reject = QMessageBox(QMessageBox.Information,
                                         "Deleting not possible",
                                         "This label class is used in other files.")
                    reject.exec()
                else:
                    self.classes.pop(class_name)
            self.update_labels()

    def on_delete_file(self):

        # set up a message box
        image_name = self.images[self._selection_idx]
        title = "Delete File"
        text = "You are about to delete the file {}. \n" \
               "All annotations in that image will be lost. Continue?".format(image_name)
        sb = QMessageBox.Ok | QMessageBox.Cancel
        msg = QMessageBox()
        reply = msg.information(self, title, text, sb)

        if reply == QMessageBox.Ok:

            # deleting the currently displayed file must be handled differently
            if self._selection_idx == self.img_idx:
                self.database.delete_file(image_name)
                self.images = self.database.get_images()

                # if user deleted the last file in the project, return to default state
                if not self.images:
                    self.image_display.clear()
                    self.init_labels()
                    for act in self.tool_bar.actions():
                        act.setEnabled(False)

                # else switch to the previous/next file
                else:
                    if self.img_idx != 0:
                        self.img_idx -= 1
                    self.init_image()

                self.init_file_list(True)
                self.enable_actions(['Save', 'Import', 'QuitProgram'])

            # if the file is not currently displayed, simply delete it from the database & the file_list
            else:
                cur_image = self.images[self.img_idx]
                self.database.delete_file(image_name)
                self.images = self.database.get_images()
                self.img_idx = self.images.index(cur_image)  # prevent indexing errors
                self.init_file_list(True)

    def on_delete_label(self):
        dialog = DeleteShapeMessageBox(self.current_labels[self._selection_idx].label, self)
        if dialog.answer == 1:
            # Delete the shape
            self.current_labels.pop(self._selection_idx)
            self.update_labels()

    def on_draw_end(self, points: List[QPointF], shape_type: str):
        """function to handle the end of a drawing event; let user assign a label to the annotation"""
        d = NewLabelDialog(self)
        d.exec()
        if d.class_name:
            # traces are also polygons so i am going to store them as such
            if shape_type in ['tempTrace', "tempPolygon"]:
                shape_type = 'polygon'
            shape = Shape(image_size=self.image_size,
                          label=d.class_name, points=points,
                          color=self.get_color_for_label(d.class_name),
                          shape_type=shape_type)
            self.update_labels(shape)

        self.image_display.set_temp_label()
        self.image_display.set_mode(self.EDIT)

    def on_drawing(self, points: List[QPointF], shape_type: str):
        r"""Function to handle the drawing event"""
        action = f'Draw{shape_type.replace("temp", "").capitalize()}'
        if self.tool_bar.get_widget_for_action(action).isChecked():
            if points:
                self.image_display.set_temp_label(points, shape_type)

    def on_draw_start(self, shape_type: str):
        r"""Function to enable the drawing but also uncheck all other buttons"""
        action = self.tool_bar.get_widget_for_action(f'Draw{shape_type.replace("temp", "").capitalize()}')
        if action.isChecked():
            self.image_display.set_mode(self.CREATE)
            self.image_display.set_shape_type(shape_type)
        else:
            self.image_display.set_temp_label()
            self.image_display.set_mode(self.EDIT)

    def on_edit_label(self):
        d = NewLabelDialog(self)
        d.set_text(self.current_labels[self._selection_idx].label)
        d.exec()
        if d.class_name:
            # traces are also polygons so i am going to store them as such
            shape = self.current_labels[self._selection_idx]
            shape.label = d.class_name
            shape.update_color(self.get_color_for_label(shape.label))
            self.update_labels((self._selection_idx, shape))

    def on_import(self, fd_directory, fd_options):
        """This function is the handle for importing new images/videos to the database and the current project"""

        # user first needs to specify the type of the file to be imported
        existing_patients = self.database.get_patients()
        select_patient = SelectPatientDialog(existing_patients)
        select_patient.exec()

        # add the newly created patients ot the project
        for p in select_patient.patients:
            self.database.add_patient(p)

        if select_patient.patient:
            filename, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=fd_directory,
                                                      options=fd_options)

            # get path to file and store it in the database
            if filename:
                self.add_file(filename, select_patient.patient)

                # update the GUI
                cur_image = self.images[self.img_idx] if self.images else None
                self.images = self.database.get_images()

                # initialize additional parts, if it is the first added file
                if self.image_display.is_empty():
                    self.image_display.set_initialized()
                    self.init_image()
                    self.enable_actions()
                # make sure the correct image is still selected in the file_list
                else:
                    self.img_idx = self.images.index(cur_image)
                self.init_file_list(True)

    def on_move_shape(self, h_shape: int, displacement: QPointF):
        self.current_labels[h_shape].move_shape(displacement)
        self.image_display.set_labels(self.current_labels)

    def on_move_vertex(self, v_shape: int, v_num: int, new_pos: QPointF):
        if v_shape != -1:
            if self.current_labels[v_shape].vertices.selected_vertex != -1:
                self.current_labels[v_shape].move_vertex(v_num, new_pos)
                self.image_display.set_labels(self.current_labels)

    def on_new_project(self):
        """This function is the handle for creating a new project"""

        project_handler = ProjectHandlerDialog(self)
        project_handler.exec()

        # in case user specified a valid project location, set up project structure
        if project_handler.project_path:
            self.project_location = project_handler.project_path
            create_project_structure(self.project_location)

            # call initialization function, pass the files that should be initially added
            self.init_with_database(self.project_location + Structure.DATABASE_DEFAULT_NAME,
                                    patients=project_handler.patients,
                                    files=project_handler.files)

    def on_next_image(self, forwards: bool):
        """Displays the the next image if 'forwards' is set to True, else the previous image"""
        dlg_result = self.check_for_changes(quit_program=False)
        if dlg_result == QMessageBox.AcceptRole or dlg_result == QMessageBox.DestructiveRole:
            if dlg_result == QMessageBox.AcceptRole:
                self.on_save()

        direction = 1 if forwards else -1
        self.img_idx = (self.img_idx + direction) % len(self.images)
        self.init_image()
        self.image_display.set_mode(self.EDIT)

    def on_open_project(self, fd_directory, fd_options):
        """This function is the handle for opening a project"""

        database, _ = QFileDialog.getOpenFileName(self,
                                                  caption="Select Database",
                                                  directory=fd_directory,
                                                  filter="Database (*.db)",
                                                  options=fd_options)

        # if user selected a database file
        if database:

            # make sure the database is inside a project environment
            if check_environment(str(pathlib.Path(database).parents[0])):
                self.project_location = str(pathlib.Path(database).parents[0])
                self.init_with_database(database)
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Invalid Project Location")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()

    def on_request_class_menu(self, selection_idx, contextmenu_pos):
        """Helper method to open the contextmenu with the appropriate actions"""
        actions = ["Delete Label Class"]
        self.open_context_menu(selection_idx, contextmenu_pos, actions)

    def on_request_files_menu(self, selection_idx, contextmenu_pos):
        """Helper method to open the contextmenu with the appropriate actions"""
        actions = ["Delete File"]
        self.open_context_menu(selection_idx, contextmenu_pos, actions)

    def on_request_shape_menu(self, selection_idx, contextmenu_pos):
        """Helper method to open the contextmenu with the appropriate actions"""
        actions = ["Edit Label Name", "Delete Label"]
        self.open_context_menu(selection_idx, contextmenu_pos, actions)

    def on_save(self):
        """Save current state to database"""
        if not self.database:
            return
        self.database.update_labels(list(self.classes.keys()))
        entries = list()
        for _lbl in self.current_labels:
            label_dict, class_name = _lbl.to_dict()
            annotation_entry = self.create_annotation_entry(label_dict, class_name)
            entries.append(annotation_entry)

        if self.images:
            self.database.update_image_annotations(image_name=self.images[self.img_idx], entries=entries)

    def open_context_menu(self, selection_idx, contextmenu_pos, actions=None):
        """This opens the context menu, uses only the suitable actions
        (shape actions if menu_type == 'shape', otherwise, actions regarding the lists at the right)"""
        self._selection_idx = selection_idx
        actions = actions if actions else []

        if len(actions) > 1:
            if selection_idx != -1 and self.current_labels[selection_idx].isSelected:
                for action in self.context_menu.actions():
                    action.setEnabled(True)
            else:
                for action in self.context_menu.actions():
                    if action.text() in actions:
                        action.setEnabled(False)

        for action in self.context_menu.actions():
            if action.text() in actions:
                action.setVisible(True)
            else:
                action.setVisible(False)
        self.context_menu.exec(contextmenu_pos)

    def update_labels(self, shapes: Union[Shape, List[Shape], Tuple[int, Shape]] = None):
        """Updates the current displayed label/canvas in multiple ways. If no argument is given,
        only the labels are updated in the displaying widgets"""
        if isinstance(shapes, list):
            # Add multiple shapes
            for _shape in shapes:
                self.current_labels.append(_shape)
        elif isinstance(shapes, tuple):
            # replace a shape with a new shape
            self.current_labels[shapes[0]] = shapes[1]
        elif isinstance(shapes, Shape):
            # add one shape
            self.current_labels.append(shapes)

        self.image_display.set_labels(self.current_labels)
        self.poly_frame.update_frame(self.current_labels)

        # update labelList in case a new label class was generated
        if len(self.classes) != self.labels_list.label_list.count():
            self.labels_list.label_list.clear()
            for i, c in enumerate(self.classes):
                item = qt.createListWidgetItemWithSquareIcon(c, self.colorMap[i], 10)
                self.labels_list.label_list.addItem(item)
