from PyQt5.QtWidgets import *


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