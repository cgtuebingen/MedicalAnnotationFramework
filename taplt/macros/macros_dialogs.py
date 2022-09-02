from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont

from pathlib import Path
from taplt.utils.stylesheets import BUTTON_STYLESHEET


class ExampleProjectDialog(QDialog):
    def __init__(self):
        super(ExampleProjectDialog, self).__init__()
        self.setFixedSize(QSize(300,200))
        self.setLayout(QVBoxLayout())
        self.accepted = False

        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setText("Click the button below to create a new project with some example images \n")
        self.info.setFont(QFont("Helvetica", 15, QFont.Weight.Bold))

        self.button = QPushButton("Show me an example project")
        self.button.setStyleSheet(BUTTON_STYLESHEET)
        self.button.clicked.connect(self.finish)

        self.layout().addWidget(self.info)
        self.layout().setSpacing(10)
        self.layout().addWidget(self.button)

    def finish(self):
        """closes the dialog and accepts it"""
        self.accepted = True
        self.close()


class ExampleProjectMessageBox(QMessageBox):
    """informs the user about the example project"""

    def __init__(self, location: str):
        super(ExampleProjectMessageBox, self).__init__()

        self.setText("Welcome to your first project!\n It is stored under \n {}".format(location))
        self.setInformativeText("To your right, you can see the information displays, showing your project files. \n"
                                "To your left, you can open up the drawing tools. \n \n "
                                "Feel free to click around and see what can be done.")
        self.setIcon(QMessageBox.Icon.Information)


class PreviewDatabaseDialog(QDialog):
    """displays the content of the specified database table"""

    def __init__(self, headers: list, content: list):
        super(PreviewDatabaseDialog, self).__init__()
        self.setLayout(QVBoxLayout())

        num_rows = len(content)
        num_cols = len(headers)

        self.table = QTableWidget()
        self.table.setRowCount(num_rows)
        self.table.setColumnCount(num_cols)
        self.table.setHorizontalHeaderLabels(headers)

        for i in range(num_rows):
            row = content[i]
            for j in range(num_cols):
                cell = row[j]
                if isinstance(cell, bytes):
                    cell = "BLOB"
                else:
                    cell = str(cell)
                item = QTableWidgetItem(cell)
                self.table.setItem(i, j, item)

        self.button = QPushButton("Close")
        self.button.setStyleSheet(BUTTON_STYLESHEET)
        self.button.setFixedSize(80, 60)
        self.button.pressed.connect(self.close)

        self.layout().addWidget(self.table)
        self.layout().addWidget(self.button)
        self.layout().setAlignment(self.button, Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(self.table.size())
