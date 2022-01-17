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
from seg_utils.ui.dialogs import (NewLabelDialog, ForgotToSaveMessageBox, DeleteShapeMessageBox,
                                  SelectFileTypeDialog, ProjectHandlerDialog, CommentDialog)
from seg_utils.config import VERTEX_SIZE


class LabelMain(QMainWindow, LabelUI):
    sLabelSelected = pyqtSignal(int, int, int)
    sResetSelAndHigh = pyqtSignal()
    CREATE, EDIT = 0, 1

    def __init__(self):
        super(LabelMain, self).__init__()
        self.setupUI(self)

        # placeholder variables that can be used later
        self.database = None  # type: SQLiteDatabase
        self.basedir = None  # type: str
        self.project_location = None  # type: str
        self.labeled_images = []
        self.current_labels = []
        self.classes = {}
        self.isLabeled = None
        self.img_idx = 0
        self.b_autoSave = True
        self.actions = tuple()
        self.actions_dict = {}
        self.contextMenu = QMenu(self)
        self._selectedShape = -1
        self.image_size = QSize()

        # color stuff
        self._num_colors = 25  # number of colors
        self.colorMap = None  # type: List[QColor]

        self._FD_Dir = '../examples'
        self._FD_Opt = QFileDialog.DontUseNativeDialog
        self.initActions()
        self.connectEvents()

        self.vertex_size = VERTEX_SIZE

    def initActions(self):
        """Initialise all actions present which can be connected to buttons or menu items"""
        # TODO: some shortcuts dont work
        actionNewProject = Action(self,
                                  "New\nProject",
                                  self.on_newProject,
                                  'Ctrl+N',
                                  "new",
                                  "New project",
                                  enabled=True)
        actionOpenProject = Action(self,
                                   "Open\nProject",
                                   lambda: self.on_openProject(self._FD_Dir, self._FD_Opt),
                                   'Ctrl+O',
                                   "open",
                                   "Open project",
                                   enabled=True)
        actionSave = Action(self,
                            "Save",
                            self.on_saveLabel,
                            'Ctrl+S',
                            "save",
                            "Save current state to database")
        actionImport = Action(self,
                              "Import",
                              lambda: self.on_import(self._FD_Dir, self._FD_Opt),
                              'Ctrl+I',
                              "import",
                              "Import a new file to database")
        actionNextImage = Action(self,
                                 "Next\nImage",
                                 self.on_nextImage,
                                 'Right',
                                 "next",
                                 "Go to next image")
        actionPrevImage = Action(self,
                                 "Previous\nImage",
                                 self.on_prevImag,
                                 'Left',
                                 "prev",
                                 "Go to previous image")
        actionDrawPoly = Action(self,
                                "Draw\nPolygon",
                                lambda: self.on_drawStart('tempPolygon'),
                                icon="polygon",
                                tip="Draw Polygon (right click to show options)",
                                checkable=True)
        actionTraceOutline = Action(self,
                                    "Draw\nTrace",
                                    lambda: self.on_drawStart('tempTrace'),
                                    icon="outline",
                                    tip="Trace Outline",
                                    checkable=True)
        actionDrawCircle = Action(self,
                                  "Draw\nCircle",
                                  lambda: self.on_drawStart('circle'),
                                  icon="circle",
                                  tip="Draw Circle",
                                  checkable=True)
        actionDrawRectangle = Action(self,
                                     "Draw\nRectangle",
                                     lambda: self.on_drawStart('rectangle'),
                                     icon="square",
                                     tip="Draw Rectangle",
                                     checkable=True)

        self.actions = ((actionNewProject,
                         actionOpenProject,
                         actionSave,
                         actionImport,
                         actionNextImage,
                         actionPrevImage,
                         actionDrawPoly,
                         actionTraceOutline,
                         actionDrawCircle,
                         actionDrawRectangle))
        # Init Toolbar
        self.toolBar.addActions(self.actions)

        actionEditLabel = Action(self, "Edit Label Name",
                                 self.on_editLabel,
                                 icon="pen",
                                 tip="Edit Label Name",enabled=True)
        actionDeleteLabel = Action(self, "Delete Label",
                                   self.on_deleteLabel,
                                   icon="trash",
                                   tip="Delete Label")

        self.initContextMenu((actionEditLabel, actionDeleteLabel))

    def add_file(self, filepath: str, filetype: str):
        """ This method copies a selected file to the project environment and updates the database """

        # TODO: right now it works only with images
        # copy file
        dest = self.project_location + Structure.IMAGES_DIR
        shutil.copy(filepath, dest)

        # add the filename to database
        filename = os.path.basename(filepath)
        self.database.add_file(filename, filetype)

    def connectEvents(self):
        """ this method comprises the connect statements for functionality of the GUI parts"""
        self.fileList.itemClicked.connect(self.handleFileListItemClicked)
        self.fileSearch.textChanged.connect(self.handleFileListSearch)
        self.polyFrame.polyList.itemClicked.connect(self.handlePolyListSelection)
        self.imageDisplay.canvas.sRequestLabelListUpdate.connect(self.handleUpdatePolyList)
        self.imageDisplay.canvas.sRequestFitInView.connect(self.imageDisplay.fitInView)
        self.imageDisplay.scene.sShapeHovered.connect(self.imageDisplay.canvas.handleShapeHovered)
        self.imageDisplay.scene.sShapeSelected.connect(self.imageDisplay.canvas.handleShapeSelected)
        self.sLabelSelected.connect(self.imageDisplay.canvas.handleShapeSelected)
        self.imageDisplay.sZoomLevelChanged.connect(self.on_zoomLevelChanged)
        self.polyFrame.commentList.itemClicked.connect(self.handleCommentClick)

        # ContextMenu
        self.imageDisplay.scene.sRequestContextMenu.connect(self.on_requestContextMenu)
        self.polyFrame.polyList.sRequestContextMenu.connect(self.on_requestContextMenu)

        # Drawing Events
        self.imageDisplay.scene.sDrawing.connect(self.on_Drawing)
        self.imageDisplay.scene.sDrawingDone.connect(self.on_drawEnd)

        # Altering Shape Events
        self.sResetSelAndHigh.connect(self.imageDisplay.canvas.on_ResetSelAndHigh)
        self.imageDisplay.scene.sMoveVertex.connect(self.on_moveVertex)
        self.imageDisplay.scene.sMoveShape.connect(self.on_moveShape)
        self.imageDisplay.scene.sRequestAnchorReset.connect(self.on_anchorRest)

    def initWithDatabase(self, database: str, files: list = None):
        """This function is called if a correct database is selected"""
        self.basedir = pathlib.Path(database).parents[0]
        self.database = SQLiteDatabase(database)

        # if the project was newly created, user may have specified files to add
        if files:
            for file in files:
                # TODO: Implement filetype distinctions, right now only images considered
                self.add_file(file, 'png')

        self.labeled_images = self.database.get_images()
        self.initColors()
        self.initClasses()
        self.initFileList()
        self.enable_essentials()

        if self.labeled_images:
            self.imageDisplay.setInitialized()
            self.initImage()
            self.enable_tools()

    def initClasses(self):
        """This function initializes the available classes in the database and updates the label list"""
        self.labelList.clear()
        classes = self.database.get_label_classes()
        for idx, _class in enumerate(classes):
            item = qt.createListWidgetItemWithSquareIcon(_class, self.colorMap[idx], 10)
            self.labelList.addItem(item)
            self.classes[_class] = idx

    def initColors(self):
        r"""Initialise the colors for plotting and for the individual lists """
        self.colorMap, drawNewColor = qt.colormapRGB(n=self._num_colors)  # have a buffer for new classes
        self.imageDisplay.canvas.setNewColor(drawNewColor)

    def initFileList(self, show_check_box=False):
        r"""Initialize the file list with all the entries found in the database"""
        self.fileList.clear()
        for idx, elem in enumerate(self.labeled_images):
            if show_check_box:
                # TODO: relative path doesnt work
                item = QListWidgetItem(QIcon("./icons/checked.png"),
                                       self.labeled_images[idx].replace(Structure.IMAGES_DIR, ""))
            else:
                item = QListWidgetItem(self.labeled_images[idx].replace(Structure.IMAGES_DIR, ""))
            self.fileList.addItem(item)
        self.fileList.setCurrentRow(self.img_idx)

    def initLabels(self):
        r"""This function initializes the labels for the current image. Necessary to have only one call to the database
        if the image is changed"""
        labels = self.database.get_label_from_imagepath(self.labeled_images[self.img_idx])
        self.current_labels = [Shape(image_size=self.image_size, label_dict=_label,
                                     color=self.getColorForLabel(_label['label']))
                               for _label in labels]
        self.polyFrame.polyList.updateList(self.current_labels)
        self.polyFrame.commentList.initComments(self.current_labels)

    def initImage(self):
        """Initializes the displayed image and respective label/canvas"""
        image = QPixmap(self.project_location + Structure.IMAGES_DIR + self.labeled_images[self.img_idx])
        self.image_size = image.size()
        self.initLabels()
        self.imageDisplay.canvas.setPixmap(image)
        self.imageDisplay.canvas.setLabels(self.current_labels)
        self.fileList.setCurrentRow(self.img_idx)
        self.on_zoomLevelChanged(1)

    def initContextMenu(self, actions: Tuple[Action, Action]):
        """ Initializes the functionality of the contextMenu"""
        for action in actions:
            self.contextMenu.addAction(action)
            self.polyFrame.polyList.contextMenu.addAction(action)

    def handleFileListItemClicked(self):
        """Tracks the changed item in the label List"""
        dlgResult = self.checkForChanges()
        if dlgResult == QMessageBox.AcceptRole or dlgResult == QMessageBox.DestructiveRole:
            if dlgResult == QMessageBox.AcceptRole:
                self.on_saveLabel()
            self.img_idx = self.labeled_images.index(self.fileList.currentItem().text())
            self.initImage()

    def handleFileListSearch(self):
        r"""Handles the file search. If the user types into the text box, it changes the files which are displayed"""
        text = self.fileSearch.toPlainText()
        for item_idx in range(self.fileList.count()):
            if text not in self.fileList.item(item_idx).text():
                self.fileList.item(item_idx).setHidden(True)
            else:
                self.fileList.item(item_idx).setHidden(False)

    def handleUpdatePolyList(self, _item_idx):
        """ updates the polyList """
        for _idx in range(self.polyFrame.polyList.count()):
            self.polyFrame.polyList.item(_idx).setSelected(False)
        self.polyFrame.polyList.item(_item_idx).setSelected(True)

    def handlePolyListSelection(self, item):
        r"""Returns the row index within the list such that the plotter in canvas can update it"""
        self.sLabelSelected.emit(self.polyFrame.polyList.row(item), self.polyFrame.polyList.row(item), -1)

    def getColorForLabel(self, label_name: str):
        r"""Get a Color based on a label_name"""
        label_index = self.classes[label_name]
        return self.colorMap[label_index]

    def updateLabels(self, shapes: Union[Shape, List[Shape], Tuple[int, Shape]] = None):
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
        self.imageDisplay.canvas.setLabels(self.current_labels)
        self.polyFrame.polyList.updateList(self.current_labels)
        self.polyFrame.commentList.initComments(self.current_labels)

        # update labelList in case a new label class was generated
        if len(self.classes) != self.labelList.count():
            self.labelList.clear()
            for i, c in enumerate(self.classes):
                item = qt.createListWidgetItemWithSquareIcon(c, self.colorMap[i], 10)
                self.labelList.addItem(item)

    def enable_essentials(self):
        """This function enables the Save and Import buttons when a database is opened """
        self.toolBar.getWidgetForAction('Save').setEnabled(True)
        self.toolBar.getWidgetForAction('Import').setEnabled(True)

        # TODO: this disables the Open & New Database Button as i only need it once
        #   and currently it crashes everything if clicked again
        self.toolBar.getWidgetForAction('NewProject').setEnabled(False)
        self.toolBar.getWidgetForAction('OpenProject').setEnabled(False)

    def enable_tools(self):
        """This function enables ever button in the toolBar except the Open & New Database Button"""
        for act in self.toolBar.actions():
            self.toolBar.widgetForAction(act).setEnabled(True)

        # TODO: this disables the Open & New Database Button as i only need it once
        #   and currently it crashes everything if clicked again
        self.toolBar.getWidgetForAction('NewProject').setEnabled(False)
        self.toolBar.getWidgetForAction('OpenProject').setEnabled(False)

    def setButtonsUnchecked(self):
        """Set all Buttons into the Unchecked state"""
        for act in self.toolBar.actions():
            if self.toolBar.widgetForAction(act).isChecked():
                self.toolBar.widgetForAction(act).setChecked(Qt.Unchecked)

        # TODO: not sure if here is the right call tho - could be done more nicely i think
        self.imageDisplay.scene.setMode(self.EDIT)

    def setOtherButtonsUnchecked(self, action: str):
        """Set all buttons except the button defined by the action into the unchecked state"""
        for act in self.toolBar.actions():
            if not self.toolBar.widgetForAction(act) == action:
                self.toolBar.widgetForAction(act).setChecked(Qt.Unchecked)

    def create_annotation_entry(self, label_dict: dict, label_class: str) -> dict:
        """
        creates a dictionary that can be used as an entry for the annotations table in the database
        :param label_dict: all information regarding the Shape object of the annotation
        :param label_class: class of the label
        :return: a dictionary used as an entry to the database
        """
        filename = self.labeled_images[self.img_idx]
        modality, file = self.database.get_uids_from_filename(filename)
        label_class = self.database.get_uid_from_label(label_class)
        patient = 1  # TODO: Implement patient id references

        return {'modality': modality,
                'file': file,
                'patient': patient,
                'shape': pickle.dumps(label_dict),
                'label': label_class}

    def closeEvent(self, event) -> None:
        dlgResult = self.checkForChanges()
        if dlgResult == QMessageBox.AcceptRole or dlgResult == QMessageBox.DestructiveRole:
            if dlgResult == QMessageBox.AcceptRole:
                self.on_saveLabel()

    def on_newProject(self):
        """This function is the handle for creating a new project"""

        projectHandler = ProjectHandlerDialog(self)
        projectHandler.exec()

        # in case user specified a valid project location, set up project structure
        if projectHandler.project_path:
            self.project_location = projectHandler.project_path
            create_project_structure(self.project_location)

            # call initialization function, pass the files that should be initially added
            self.initWithDatabase(self.project_location + Structure.DATABASE_DEFAULT_NAME, files=projectHandler.files)

    def on_openProject(self, fddirectory, fdoptions):
        """This function is the handle for opening a project"""

        # TODO: Implement a more intuitive solution than selecting the database within the project environment
        database, _ = QFileDialog.getOpenFileName(self,
                                                  caption="Select Database",
                                                  directory=fddirectory,
                                                  filter="Database (*.db)",
                                                  options=fdoptions)

        # if user selected a database file
        if database:

            # make sure the database is inside a project environment
            if check_environment(str(pathlib.Path(database).parents[0])):
                self.project_location = str(pathlib.Path(database).parents[0])
                self.initWithDatabase(database)
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Invalid Project Location")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()

    def on_import(self, fddirectory, fdoptions):
        """This function is the handle for importing new images/videos to the database and the current project"""

        # user first needs to specify the type of the file to be imported
        select_filetype = SelectFileTypeDialog()
        select_filetype.exec()
        if select_filetype.filetype:

            # TODO: implement smarter filetype recognition
            _filter = '*png *jpg *jpeg' if select_filetype.filetype == 'png' else select_filetype.filetype

            filename, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=fddirectory,
                                                      filter="File ({})".format(_filter),
                                                      options=fdoptions)

            # get path to file and store it in the database
            if filename:
                self.add_file(filename, select_filetype.filetype)

                # update the GUI
                self.labeled_images = self.database.get_images()
                self.initFileList()

                # initialize additional parts, if it is the first added file
                if self.imageDisplay.b_isEmpty:
                    self.imageDisplay.setInitialized()
                    self.initImage()
                    self.enable_tools()

    def on_saveLabel(self):
        """Save current state to database"""
        self.database.update_labels(self.classes.keys())
        entries = list()
        for _lbl in self.current_labels:
            label_dict, class_name = _lbl.to_dict()
            annotation_entry = self.create_annotation_entry(label_dict, class_name)
            entries.append(annotation_entry)

        if entries:
            self.database.update_image_annotations(image_name=self.labeled_images[self.img_idx], entries=entries)

    def on_nextImage(self):
        """Display the next image"""
        dlgResult = self.checkForChanges()
        if dlgResult == QMessageBox.AcceptRole or dlgResult == QMessageBox.DestructiveRole:
            if dlgResult == QMessageBox.AcceptRole:
                self.on_saveLabel()
            self.img_idx = (self.img_idx + 1) % len(self.labeled_images)
            self.initImage()
            self.setButtonsUnchecked()

    def on_prevImag(self):
        """Display the previous image"""
        dlgResult = self.checkForChanges()
        if dlgResult == QMessageBox.AcceptRole or dlgResult == QMessageBox.DestructiveRole:
            if dlgResult == QMessageBox.AcceptRole:
                self.on_saveLabel()
            self.img_idx = (self.img_idx - 1) % len(self.labeled_images)
            self.initImage()
            self.setButtonsUnchecked()

    def on_drawStart(self, shape_type: str):
        r"""Function to enable the drawing but also uncheck all other buttons"""
        action = self.toolBar.getWidgetForAction(f'Draw{shape_type.replace("temp", "").capitalize()}')
        self.setOtherButtonsUnchecked(action)
        self.sResetSelAndHigh.emit()
        if action.isChecked():
            self.imageDisplay.scene.setMode(self.CREATE)
            self.imageDisplay.scene.setShapeType(shape_type)
        else:
            self.imageDisplay.canvas.setTempLabel()
            self.imageDisplay.scene.setMode(self.EDIT)

    def on_Drawing(self, points: List[QPointF], shape_type: str):
        r"""Function to handle the drawing event"""
        action = f'Draw{shape_type.replace("temp", "").capitalize()}'
        if self.toolBar.getWidgetForAction(action).isChecked():
            if points:
                self.imageDisplay.canvas.setTempLabel(points, shape_type)

    def on_drawEnd(self, points: List[QPointF], shape_type: str):
        """function to handle the end of a drawing event; let user assign a label to the annotation"""
        d = NewLabelDialog(self)
        d.exec()
        if d.class_name:
            # traces are also polygons so i am going to store them as such
            if shape_type in ['tempTrace', "tempPolygon"]:
                shape_type = 'polygon'
            shape = Shape(image_size=self.image_size,
                          label=d.class_name, points=points,
                          color=self.getColorForLabel(d.class_name),
                          shape_type=shape_type)
            self.updateLabels(shape)
        self.imageDisplay.canvas.setTempLabel()
        self.setButtonsUnchecked()

    def on_requestContextMenu(self, shape_idx, contextmenu_pos):
        """This opens the context menu"""
        self._selectedShape = shape_idx
        if shape_idx != -1 and self.current_labels[shape_idx].isSelected:
            for action in self.contextMenu.actions():
                action.setEnabled(True)
        else:
            for action in self.contextMenu.actions():
                action.setEnabled(False)
        self.contextMenu.exec(contextmenu_pos)

    def on_editLabel(self):
        d = NewLabelDialog(self)
        d.setText(self.current_labels[self._selectedShape].label)
        d.exec()
        if d.class_name:
            # traces are also polygons so i am going to store them as such
            shape = self.current_labels[self._selectedShape]
            shape.label = d.class_name
            shape.updateColor(self.getColorForLabel(shape.label))
            self.updateLabels((self._selectedShape, shape))

    def on_deleteLabel(self):
        dialog = DeleteShapeMessageBox(self.current_labels[self._selectedShape].label, self)
        if dialog.answer == 1:
            # Delete the shape
            self.current_labels.pop(self._selectedShape)
            self.updateLabels()

    def on_moveVertex(self, vShape: int, vNum: int, newPos: QPointF):
        if vShape != -1:
            if self.current_labels[vShape].vertices.selectedVertex != -1:
                self.current_labels[vShape].moveVertex(vNum, newPos)
                self.imageDisplay.canvas.setLabels(self.current_labels)

    def on_moveShape(self, hShape: int, displacement: QPointF):
        self.current_labels[hShape].moveShape(displacement)
        self.imageDisplay.canvas.setLabels(self.current_labels)

    def on_anchorRest(self, vShape: int):
        """Handles the reset of the anchor upon the mouse release within the respective label/shape"""
        if self.current_labels:
            self.current_labels[vShape].resetAnchor()

    def on_zoomLevelChanged(self, zoom: int):
        for shape in self.current_labels:
            size = [self.imageDisplay.canvas.pixmap.width(), self.imageDisplay.canvas.pixmap.height()]
            shape.setScaling(zoom, size[argmax(size)])

    def checkForChanges(self) -> int:
        r"""Check for changes with the database

            :returns: 0 if accepted or no changes, 1 if cancelled and 2 if dismissed
        """
        if not self.labeled_images:
            return 2
        sql_labels = self.database.get_label_from_imagepath(self.labeled_images[self.img_idx])
        sql_labels = [Shape(image_size=self.image_size, label_dict=_label, color=self.getColorForLabel(_label['label']))
                      for _label in sql_labels]

        if sql_labels == self.current_labels:
            return 0
        else:
            d = ForgotToSaveMessageBox(self)
            d.exec()
            return d.result()

    def handleCommentClick(self, item):
        """Either shows a blank comment window or the previously written comment for this label"""

        comment = ""
        self.sLabelSelected.emit(self.polyFrame.commentList.row(item), self.polyFrame.commentList.row(item), -1)

        # update comment window, if needed
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
