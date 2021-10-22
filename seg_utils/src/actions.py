from PyQt5.QtWidgets import QAction
from seg_utils.utils.qt import getIcon


class Action(QAction):
    """Create an Action"""
    def __init__(self,
                 parent,
                 text,
                 event=None,
                 shortcut=None,
                 icon=None,
                 tip=None,
                 checkable=False,
                 enabled=False,
                 checked=False,
                 ):
        super(Action, self).__init__(text, parent)
        if icon is not None:
            self.setIconText(text.replace(" ", "\n"))
            self.setIcon(getIcon(icon))
        if shortcut is not None:
            if isinstance(shortcut, (list, tuple)):
                self.setShortcuts(shortcut)
            else:
                self.setShortcut(shortcut)
        if tip is not None:
            self.setToolTip(tip)
            self.setStatusTip(tip)
        if event is not None:
            self.triggered.connect(event)
        if checkable:
            self.setCheckable(True)
        self.setEnabled(enabled)
        self.setChecked(checked)



