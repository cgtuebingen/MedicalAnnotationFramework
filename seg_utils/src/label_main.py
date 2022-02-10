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
from seg_utils.utils.project_structure import Structure, create_project_structure, check_environment
from seg_utils.src.actions import Action
from seg_utils.ui.label_ui import LabelUI
from seg_utils.ui.shape import Shape
from seg_utils.ui.dialogs import (NewLabelDialog, ForgotToSaveMessageBox, DeleteShapeMessageBox, CloseMessageBox,
                                  SelectFileTypeAndPatientDialog, ProjectHandlerDialog, CommentDialog)
from seg_utils.config import VERTEX_SIZE


class LabelMain(QMainWindow, LabelUI):
    sLabelSelected = pyqtSignal(int, int, int)
    sResetSelAndHigh = pyqtSignal()
    CREATE, EDIT = 0, 1

    def __init__(self):
        super(LabelMain, self).__init__()
        self.setup_ui(self)

        # placeholder variables that can be used later
        self.database = None  # type: SQLiteDatabase
        self.project_location = None  # type: str
        self.images = []
        self.current_labels = []
        self.classes = {}
        self.isLabeled = None
        self.img_idx = 0
        self.b_autoSave = True
        # self.actions = tuple()
        # self.actions_dict = {}
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

        self.vertex_size = VERTEX_SIZE

    def add_file(self, filepath: str, filetype: str, patient: str):
        """ This method copies a selected file to the project environment and updates the database """

        # TODO: right now it works only with images
        # copy file
        dest = self.project_location + Structure.IMAGES_DIR
        shutil.copy(filepath, dest)

        # add the filename to database
        filename = os.path.basename(filepath)
        self.database.add_file(filename, filetype, patient)

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

    def closeEvent(self, event) -> None:
        dlg_result = self.check_for_changes()
        if dlg_result == QMessageBox.AcceptRole or dlg_result == QMessageBox.DestructiveRole:
            if dlg_result == QMessageBox.AcceptRole:
                self.on_save()
        else:
            event.ignore()

    def connect_events(self):
        """ this method comprises the connect statements for functionality of the GUI parts"""
        self.fileList.itemClicked.connect(self.handle_file_list_item_clicked)
        self.fileSearch.textChanged.connect(self.handle_file_list_search)
        self.polyFrame.polyList.itemClicked.connect(self.handle_poly_list_selection)
        self.polyFrame.commentList.itemClicked.connect(self.handle_comment_click)
        self.imageDisplay.sRequestLabelListUpdate.connect(self.handle_update_poly_list)
        self.sLabelSelected.connect(self.imageDisplay.shape_selected)
        self.imageDisplay.image_viewer.sZoomLevelChanged.connect(self.on_zoom_level_changed)

        # toolbar actions
        self.toolBar.get_action("NewProject").triggered.connect(self.on_new_project)
        self.toolBar.get_action("OpenProject").triggered.connect(lambda: self.on_open_project(self._FD_Dir,
                                                                                              self._FD_Opt))
        self.toolBar.get_action("Save").triggered.connect(self.on_save)
        self.toolBar.get_action("Import").triggered.connect(lambda: self.on_import(self._FD_Dir, self._FD_Opt))
        self.toolBar.get_action("NextImage").triggered.connect(lambda: self.on_next_image(True))
        self.toolBar.get_action("PreviousImage").triggered.connect(lambda: self.on_next_image(False))
        self.toolBar.get_action("DrawTrace").triggered.connect(lambda: self.on_draw_start('tempTrace'))
        self.toolBar.get_action("DrawPolygon").triggered.connect(lambda: self.on_draw_start('tempPolygon'))
        self.toolBar.get_action("DrawCircle").triggered.connect(lambda: self.on_draw_start('circle'))
        self.toolBar.get_action("DrawRectangle").triggered.connect(lambda: self.on_draw_start('rectangle'))
        self.toolBar.get_action("QuitProgram").triggered.connect(self.close)

        # ContextMenu
        self.imageDisplay.scene.sRequestContextMenu.connect(self.on_request_shape_menu)
        self.polyFrame.polyList.sRequestContextMenu.connect(self.on_request_shape_menu)
        self.labelList.sRequestContextMenu.connect(self.on_request_class_menu)
        self.fileList.sRequestContextMenu.connect(self.on_request_files_menu)

        # Drawing Events
        self.imageDisplay.scene.sDrawing.connect(self.on_drawing)
        self.imageDisplay.scene.sDrawingDone.connect(self.on_draw_end)

        # Altering Shape Events
        self.sResetSelAndHigh.connect(self.imageDisplay.on_reset_sel_and_high)
        self.imageDisplay.scene.sMoveVertex.connect(self.on_move_vertex)
        self.imageDisplay.scene.sMoveShape.connect(self.on_move_shape)
        self.imageDisplay.scene.sRequestAnchorReset.connect(self.on_anchor_rest)

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
                self.toolBar.get_widget_for_action(act).setEnabled(True)
        else:
            for act in self.toolBar.actions():
                self.toolBar.widgetForAction(act).setEnabled(True)

        # TODO: this disables the Open & New Database Button as i only need it once
        #   and currently it crashes everything if clicked again
        self.toolBar.get_widget_for_action('NewProject').setEnabled(False)
        self.toolBar.get_widget_for_action('OpenProject').setEnabled(False)

    def get_color_for_label(self, label_name: str):
        r"""Get a Color based on a label_name"""
        label_index = self.classes[label_name]
        return self.colorMap[label_index]

    def handle_comment_click(self, item):
        """Either shows a blank comment window or the previously written comment for this label"""
        comment = ""
        _, idx = self.polyFrame.get_index_from_selected(item)
        self.sLabelSelected.emit(idx, idx, -1)

        # set comment window text, if there already is a comment
        for lbl in self.current_labels:
            if lbl.isSelected:
                if item.text() != "Add comment" and lbl.comment:
                    comment = lbl.comment

        dlg = CommentDialog(comment)
        dlg.exec()

        text = "Details" if dlg.comment else "Add comment"
        for item in self.polyFrame.commentList.selectedItems():
            item.setText(text)
        for lbl in self.current_labels:
            if lbl.isSelected:
                lbl.comment = dlg.comment

    def handle_file_list_item_clicked(self):
        """Tracks the changed item in the label List"""

        # if user clicked on currently displayed file in the list, do nothing
        if self.img_idx == self.images.index(self.fileList.currentItem().text()):
            return

        # else save changes if necessary
        dlg_result = self.check_for_changes(quit_program=False)
        if dlg_result == QMessageBox.AcceptRole or dlg_result == QMessageBox.DestructiveRole:
            if dlg_result == QMessageBox.AcceptRole:
                self.on_save()
            self.img_idx = self.images.index(self.fileList.currentItem().text())
            self.init_image()
        else:
            self.fileList.setCurrentRow(self.img_idx)

    def handle_file_list_search(self):
        r"""Handles the file search. If the user types into the text box, it changes the files which are displayed"""
        text = self.fileSearch.toPlainText()
        for item_idx in range(self.fileList.count()):
            if text not in self.fileList.item(item_idx).text():
                self.fileList.item(item_idx).setHidden(True)
            else:
                self.fileList.item(item_idx).setHidden(False)

    def handle_poly_list_selection(self, item):
        r"""Returns the row index within the list such that the plotter in canvas can update it"""
        idx, _ = self.polyFrame.get_index_from_selected(item)
        self.sLabelSelected.emit(idx, idx, -1)

    def handle_update_poly_list(self, _item_idx):
        """ updates the polyList """
        for _idx in range(self.polyFrame.polyList.count()):
            self.polyFrame.polyList.item(_idx).setSelected(False)
        self.polyFrame.polyList.item(_item_idx).setSelected(True)

    def init_classes(self):
        """This function initializes the available classes in the database and updates the label list"""
        self.labelList.clear()
        classes = self.database.get_label_classes()
        for idx, _class in enumerate(classes):
            item = qt.createListWidgetItemWithSquareIcon(_class, self.colorMap[idx], 10)
            self.labelList.addItem(item)
            self.classes[_class] = idx

    def init_colors(self):
        r"""Initialise the colors for plotting and for the individual lists """
        self.colorMap, new_color = qt.colormap_rgb(n=self._num_colors)  # have a buffer for new classes
        self.imageDisplay.draw_new_color = new_color

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
                                     tip="Delete Label Class",
                                     enabled=True)
        action_delete_file = Action(self,
                                    "Delete File",
                                    self.on_delete_file,
                                    icon="trash",
                                    tip="Delete file",
                                    enabled=True)

        self.context_menu.addActions((action_edit_label,
                                      action_delete_label,
                                      action_delete_class,
                                      action_delete_file))

    def init_file_list(self, show_check_box=False):
        r"""Initialize the file list with all the entries found in the database"""
        self.fileList.clear()
        for idx, elem in enumerate(self.images):
            if show_check_box:
                icon = qt.get_icon("checked")
                item = QListWidgetItem(icon,
                                       self.images[idx].replace(Structure.IMAGES_DIR, ""))
            else:
                item = QListWidgetItem(self.images[idx].replace(Structure.IMAGES_DIR, ""))
            self.fileList.addItem(item)
        self.fileList.setCurrentRow(self.img_idx)

    def init_image(self):
        """Initializes the displayed image and respective label/canvas"""
        image = QPixmap(self.project_location + Structure.IMAGES_DIR + self.images[self.img_idx])
        self.image_size = image.size()
        self.init_labels()
        self.imageDisplay.init_image(image, self.current_labels)
        self.fileList.setCurrentRow(self.img_idx)
        self.on_zoom_level_changed(1)

    def init_labels(self):
        r"""This function initializes the labels for the current image. Necessary to have only one call to the database
        if the image is changed"""
        labels = self.database.get_label_from_imagepath(self.images[self.img_idx])
        self.current_labels = [Shape(image_size=self.image_size, label_dict=_label,
                                     color=self.get_color_for_label(_label['label']))
                               for _label in labels]
        self.polyFrame.update_frame(self.current_labels)

    def init_with_database(self, database: str, patients: list = None, files: dict = None):
        """This function is called if a correct database is selected"""
        self.database = SQLiteDatabase(database)

        # if the project was newly created, user may have specified patients & files to add
        if patients:
            for p in patients:
                self.database.add_patient(p)
        if files:
            for file, patient in files.items():
                # TODO: Implement filetype distinctions, right now only images considered
                self.add_file(file, 'png', patient)

        self.images = self.database.get_images()
        self.init_colors()
        self.init_classes()
        self.init_file_list(True)
        self.enable_actions(['Save', 'Import', 'QuitProgram'])

        if self.images:
            self.imageDisplay.set_initialized()
            self.init_image()
            self.enable_actions()

    def on_anchor_rest(self, v_shape: int):
        """Handles the reset of the anchor upon the mouse release within the respective label/shape"""
        if self.current_labels:
            self.current_labels[v_shape].reset_anchor()

    def on_delete_class(self):
        # TODO: Implement
        pass

    def on_delete_file(self):
        # TODO: Implement
        pass

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

        self.imageDisplay.set_temp_label()
        self.set_buttons_unchecked()
        self.imageDisplay.set_mode(self.EDIT)

    def on_drawing(self, points: List[QPointF], shape_type: str):
        r"""Function to handle the drawing event"""
        action = f'Draw{shape_type.replace("temp", "").capitalize()}'
        if self.toolBar.get_widget_for_action(action).isChecked():
            if points:
                self.imageDisplay.set_temp_label(points, shape_type)

    def on_draw_start(self, shape_type: str):
        r"""Function to enable the drawing but also uncheck all other buttons"""
        action = self.toolBar.get_widget_for_action(f'Draw{shape_type.replace("temp", "").capitalize()}')
        self.set_other_buttons_unchecked(action)
        self.sResetSelAndHigh.emit()
        if action.isChecked():
            self.imageDisplay.set_mode(self.CREATE)
            self.imageDisplay.set_shape_type(shape_type)
        else:
            self.imageDisplay.set_temp_label()
            self.imageDisplay.set_mode(self.EDIT)

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
        select_filetype = SelectFileTypeAndPatientDialog(existing_patients)
        select_filetype.exec()
        for p in select_filetype.patients:
            self.database.add_patient(p)
        filetype, patient = select_filetype.filetype, select_filetype.patient
        if filetype:

            # TODO: implement smarter filetype recognition
            _filter = '*png *jpg *jpeg' if filetype == 'png' else filetype

            filename, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=fd_directory,
                                                      filter="File ({})".format(_filter),
                                                      options=fd_options)

            # get path to file and store it in the database
            if filename:
                self.add_file(filename, filetype, patient)

                # update the GUI
                self.images = self.database.get_images()
                self.init_file_list(True)

                # initialize additional parts, if it is the first added file
                if self.imageDisplay.is_empty():
                    self.imageDisplay.set_initialized()
                    self.init_image()
                    self.enable_actions()

    def on_move_shape(self, h_shape: int, displacement: QPointF):
        self.current_labels[h_shape].move_shape(displacement)
        self.imageDisplay.set_labels(self.current_labels)

    def on_move_vertex(self, v_shape: int, v_num: int, new_pos: QPointF):
        if v_shape != -1:
            if self.current_labels[v_shape].vertices.selected_vertex != -1:
                self.current_labels[v_shape].move_vertex(v_num, new_pos)
                self.imageDisplay.set_labels(self.current_labels)

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
        self.set_buttons_unchecked()
        self.imageDisplay.set_mode(self.EDIT)

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
        self.database.update_labels(list(self.classes.keys()))
        entries = list()
        for _lbl in self.current_labels:
            label_dict, class_name = _lbl.to_dict()
            annotation_entry = self.create_annotation_entry(label_dict, class_name)
            entries.append(annotation_entry)

        if self.images:
            self.database.update_image_annotations(image_name=self.images[self.img_idx], entries=entries)

    def on_zoom_level_changed(self, zoom: int):
        for shape in self.current_labels:
            size = self.imageDisplay.get_pixmap_dimensions()
            shape.set_scaling(zoom, size[argmax(size)])

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

    def set_other_buttons_unchecked(self, action: str):
        """Set all buttons except the button defined by the action into the unchecked state"""
        for act in self.toolBar.actions():
            if not self.toolBar.widgetForAction(act) == action:
                self.toolBar.widgetForAction(act).setChecked(Qt.Unchecked)

    def set_buttons_unchecked(self):
        """Set all Buttons into the Unchecked state"""
        for act in self.toolBar.actions():
            if self.toolBar.widgetForAction(act).isChecked():
                self.toolBar.widgetForAction(act).setChecked(Qt.Unchecked)

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

        self.imageDisplay.set_labels(self.current_labels)
        self.polyFrame.update_frame(self.current_labels)

        # update labelList in case a new label class was generated
        if len(self.classes) != self.labelList.count():
            self.labelList.clear()
            for i, c in enumerate(self.classes):
                item = qt.createListWidgetItemWithSquareIcon(c, self.colorMap[i], 10)
                self.labelList.addItem(item)
