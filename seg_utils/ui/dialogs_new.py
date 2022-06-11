from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont, QIcon, QColor

from typing import List
from pathlib import Path
import os

from seg_utils.ui.list_widgets_new import LabelList
from seg_utils.utils.qt import get_icon
from seg_utils.utils.stylesheets import BUTTON_STYLESHEET


class CloseMessageBox(QMessageBox):
    def __init__(self, *args):
        super(CloseMessageBox, self).__init__(*args)

        quit_button = QPushButton(get_icon('quit'), "Quit Program")
        cancel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")
        self.addButton(quit_button, QMessageBox.AcceptRole)
        self.addButton(cancel_button, QMessageBox.RejectRole)

        self.setWindowTitle("Quit Program")
        self.setText("Are you sure you want to quit?")
        if self.parentWidget():
            move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())


class CommentDialog(QDialog):
    """QDialog to let the user enter notes regarding a specific annotation"""

    def __init__(self, comment: str):
        super(CommentDialog, self).__init__()
        self.setWindowTitle("Notes")
        self.setFixedSize(500, 300)
        self.comment = comment

        # TextEdit where user can enter a comment
        self.enter_comment = QTextEdit(self)
        self.enter_comment.setText(self.comment)

        # Accept & cancel buttons
        self.confirmation = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirmation.accepted.connect(self.create_comment)
        self.confirmation.rejected.connect(self.close)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.enter_comment)
        self.layout.addWidget(self.confirmation)

    def create_comment(self):
        """stores the written notes in the class variable and closes the dialog"""
        self.comment = self.enter_comment.toPlainText()
        self.close()


class DeleteClassMessageBox(QMessageBox):
    """ the answer variable can be interpreted as follows:
        0 cancel
        1 delete only the annotations of that class
        2 delete the whole label class"""
    def __init__(self, class_name: str, *args):
        super(DeleteClassMessageBox, self).__init__(*args)

        self.setText("You are about to delete the '{}'-class.\nContinue?".format(class_name))
        self.setInformativeText("This will remove all occurrences of '{}' from the image.\n\n".format(class_name))
        self.setCheckBox(QCheckBox("Delete the label class from my list", self))
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        self.answer = 0
        self.accepted.connect(self.set_answer)

    def set_answer(self):
        """ sets the answer-variable """
        if self.checkBox().isChecked():
            self.answer = 2
        else:
            self.answer = 1


class DeleteShapeMessageBox(QMessageBox):
    def __init__(self, shape: str, *args):
        super(DeleteShapeMessageBox, self).__init__(*args)
        if self.parentWidget():
            move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())
        reply = self.question(self, "Deleting Shape", f"You are about to delete {shape}. Continue?",
                              QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer = 1
        else:
            self.answer = 0


class ForgotToSaveMessageBox(QMessageBox):
    def __init__(self, *args):
        super(ForgotToSaveMessageBox, self).__init__(*args)

        save_button = QPushButton(get_icon('save'), "Save Changes")
        dismiss_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogDiscardButton), "Dismiss Changes")
        cancel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")

        self.setWindowTitle("Caution: Unsaved Changes")
        self.setText("Unsaved Changes: How do you want to progress?")

        # NOTE FOR SOME REASON THE ORDER IS IMPORTANT DESPITE THE ROLE - IDK WHY
        self.addButton(save_button, QMessageBox.AcceptRole)
        self.addButton(cancel_button, QMessageBox.RejectRole)
        self.addButton(dismiss_button, QMessageBox.DestructiveRole)

        if self.parentWidget():
            move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())


class SelectionDialog(QDialog):
    """ a dialog that provides (a) a list with items where user can select from and search in
        and (b) the possibility to create a new item from user input

        used as scaffolding for other classes that may fill the list with items """
    def __init__(self, selection_list, *args):
        super(SelectionDialog, self).__init__(*args)
        self.result = ""

        self.setFixedSize(QSize(300, 400))
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.layout().setSpacing(5)

        # Line Edit for searching/creating classes
        self.input = QLineEdit()
        self.input.setMaximumHeight(25)

        # info label for when user is about to create a new class
        self.info = QLabel()
        self.info.setContentsMargins(0, 0, 0, 0)
        self.info.setFrameShape(QFrame.NoFrame)
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # list widget with the already existing classes
        self.selection_list = selection_list
        self.confirm = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # connect
        self.input.textChanged.connect(self.handle_shape_input)
        self.confirm.accepted.connect(self.on_close)
        self.confirm.rejected.connect(self.on_cancel)
        self.selection_list.itemClicked.connect(self.on_list_selection)

        self.layout().addWidget(self.input)
        self.layout().addWidget(self.info)
        self.layout().addWidget(self.selection_list)
        self.layout().addWidget(self.confirm)

    def handle_shape_input(self):
        """ function to filter the list according to user input """
        self.info.clear()
        self.result = ""
        text = self.input.text()
        matches = 0

        # iterate through list, display only matches
        for item_idx in range(self.selection_list.count()):
            item = self.selection_list.item(item_idx)
            item.setSelected(False)
            if text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)
                matches += 1

        # option to create a new label class
        if matches == 0 and text:
            self.info.setStyleSheet("color: green;")
            self.info.setText("Create new: {}".format(text))
            self.result = text

        # direct match: set selected
        elif matches == 1:
            for item_idx in range(self.selection_list.count()):
                item = self.selection_list.item(item_idx)
                if not item.isHidden():
                    item.setSelected(True)
                    self.on_list_selection(item)

    def on_cancel(self):
        """ ensures that the result is an empty string"""
        self.result = ""
        self.close()

    def on_close(self):
        """ prevents an empty result when user clicks Ok"""
        if self.result:
            self.close()
        else:
            self.info.setStyleSheet("color: red;")
            self.info.setText("Please select or create an item")

    def on_list_selection(self, item: QListWidgetItem):
        """ assigns the item name to the class variable"""
        self.info.clear()
        self.result = item.text()


class NewLabelDialog(SelectionDialog):
    """ inherits the SelectionDialog, uses it to display label classes"""
    def __init__(self, classes: List[str], color_map: List[QColor], *args):
        super(NewLabelDialog, self).__init__(LabelList(), *args)
        self.setWindowTitle("Select class of new shape")
        self.input.setPlaceholderText("Enter shape label")

        # fill list with the existing label classes
        self.selection_list.update_with_classes(classes, color_map)


class SelectPatientDialog(SelectionDialog):
    """ inherits the SelectionDialog, uses it to display patient names"""
    def __init__(self, existing_patients: list, *args):
        super(SelectPatientDialog, self).__init__(QListWidget(), *args)
        self.setWindowTitle("Select a patient")
        self.input.setPlaceholderText("Enter patient name")

        # fill list with existing patient names
        for patient in existing_patients:
            item = QListWidgetItem(patient)
            self.selection_list.addItem(item)


class ProjectHandlerDialog(QDialog):
    """ provides a dialog for the user to enter a project location and add initial files, if desired"""
    def __init__(self):
        super(ProjectHandlerDialog, self).__init__()
        self.setFixedSize(800, 500)
        self.setWindowTitle('Create new Project')

        self.project_path = ""
        self.files = dict()
        self.patients = list()

        # Header for LineEdit
        self.header = QLabel()
        self.header.setStyleSheet("font: bold 12px")
        self.header.setText("Choose Project Location")

        # LineEdit where user can enter a path
        self.enter_path = QLineEdit(self)
        self.enter_path.setFixedHeight(30)

        # suggestion for a project location
        suggestion = f"{Path.home()}{os.path.sep}AnnotationProjects{os.path.sep}project"
        for i in range(1, 100):
            if not os.path.exists(suggestion + str(i)):
                suggestion = suggestion + str(i)
                break
        self.enter_path.setText(suggestion)

        # button to open up a FileDialog
        self.select_path_button = QPushButton()
        self.select_path_button.setFixedSize(QSize(40, 30))
        self.select_path_button.setStyleSheet(BUTTON_STYLESHEET)
        self.select_path_button.setText('...')
        self.select_path_button.clicked.connect(self.select_path)

        # button to add initial files
        self.add_files_button = QPushButton()
        self.add_files_button.setFixedWidth(180)
        self.add_files_button.setStyleSheet(BUTTON_STYLESHEET)
        self.add_files_button.setText("Add files to get started")
        self.add_files_button.clicked.connect(self.add_files)

        # ListWidget to display added files
        self.added_files = QListWidget()

        # Accept & cancel buttons
        self.confirmation = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirmation.button(QDialogButtonBox.Ok).setText("Create Project")
        self.confirmation.accepted.connect(self.check_path)
        self.confirmation.rejected.connect(self.close)

        # layout setup
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(10, 20, 10, 0)
        self.header_layout.addWidget(self.header)

        self.upper_row = QFrame()
        self.upper_row_layout = QHBoxLayout(self.upper_row)
        self.upper_row_layout.setContentsMargins(10, 0, 10, 0)
        self.upper_row_layout.addWidget(self.enter_path)
        self.upper_row_layout.addWidget(self.select_path_button)

        self.bottom = QFrame()
        self.bottom_layout = QVBoxLayout(self.bottom)
        self.bottom_layout.addWidget(self.add_files_button)
        self.bottom_layout.addWidget(self.added_files)
        self.bottom_layout.addWidget(self.confirmation)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.upper_row)
        self.layout.addStretch(1)
        self.layout.addWidget(self.bottom)

    def add_files(self):
        """ function to let user select a file which will be added when the project is finally created"""

        # user first needs to specify the type of the file to be imported
        dlg = SelectPatientDialog(self.patients)
        dlg.exec()
        self.patients.append(dlg.result)

        if dlg.result:
            filepath, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=str(Path.home()),
                                                      options=QFileDialog.DontUseNativeDialog)

            # only care about the filename itself (not regarding its path), to make it easier to handle
            filename = os.path.basename(filepath)
            if self.exists(filename):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("The file\n{}\nalready exists.\nOverwrite?".format(filename))
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.accepted.connect(lambda: self.overwrite(filepath, filename, dlg.result))
                msg.exec()
            elif filename:
                # TODO: Implement possibility to add several files at once
                self.files[filepath] = dlg.result
                self.added_files.addItem(QListWidgetItem(filename))

    def check_path(self):
        """ this function verifies/rejects the project path which the user entered in the LineEdit"""
        project_path = self.enter_path.text()

        # check if user entered a non-empty directory
        if os.path.exists(project_path):
            content = os.listdir(project_path)
            if len(content) != 0:

                # confirmation dialog; directory will be cleared if user proceeds
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("The directory\n{}\nis not empty.".format(project_path))
                msg.setInformativeText("All existing files in that directory will be deleted.\nProceed?")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.accepted.connect(lambda: self.create_project(project_path))
                msg.exec()
            else:
                self.project_path = project_path
                self.close()

        # if user entered a valid absolute path, create the project
        elif os.path.isabs(project_path):
            self.project_path = project_path
            self.close()

        # else do nothing
        else:
            msg = QMessageBox()
            msg.setText("Please enter a valid project location.")
            msg.exec()

    def create_project(self, project_path: str):
        """This function stores a valid path as class variable and closes the dialog"""
        self.project_path = project_path
        self.close()

    def exists(self, filename: str):
        """ check if a filename is already in the list
        also prevents name clashes when two files from different paths have the same name"""
        for i in range(self.added_files.count()):
            cur = self.added_files.item(i).text()
            if cur == filename:
                return True
        return False

    def overwrite(self, filepath: str, filename: str, patient: str):
        """overwrites an existing file in the file list"""

        # find and delete the corresponding item in the files list
        for fn in self.files.keys():
            cur = os.path.basename(fn)
            if cur == filename:
                self.files.pop(fn)
                break

        # append the new filepath
        self.files[filepath] = patient

    def select_path(self):
        """opens a dialog to let the user select a directory from its OS """

        # dialog to select a directory in the user's environment
        dialog = QFileDialog()
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setDirectory(str(Path.home()))

        # store selected path in the LineEdit
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            self.enter_path.setText(filename)


def move_to_center(widget, parent_pos: QPoint, parent_size: QSize):
    # TODO: implement move_to_center somewhere else, so the dialogs don't have to demand a parent widget
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)
