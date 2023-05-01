from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from typing import *

from taplt.src.actions import Action


class Toolbar(QToolBar):

    sCreateNewProject = pyqtSignal(str, dict)
    sOpenProject = pyqtSignal(str)
    sRequestPatients = pyqtSignal()
    sSetDrawingMode = pyqtSignal(int)
    sSetShapeType = pyqtSignal(str)

    def __init__(self, parent):
        super(Toolbar, self).__init__(parent)
        self.actionsDict = {}  # This is a lookup table to match the buttons to the numbers they got added

        self.setMinimumSize(QSize(80, 100))
        self.setMaximumSize(QSize(80, 16777215))
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.setMovable(False)
        self.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setObjectName("toolBar")
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self.button_group.buttonToggled.connect(self.exclusive_optional)

    def disable_drawing(self, disable: bool):
        [btn.setDisabled(disable) for btn in self.button_group.buttons()]

    def exclusive_optional(self, btn: QToolButton):
        [x.setChecked(False) for x in self.button_group.buttons() if x != btn]

    def addAction(self, action: Action):
        r"""Because I want a physical button in the toolbar, i need to create a widget"""
        if isinstance(action, QWidgetAction):
            return super(Toolbar, self).addAction(action)
        btn = QToolButton()
        # btn.setAutoRaise(True)
        btn.setCheckable(action.isCheckable())
        if action.isCheckable():
            self.button_group.addButton(btn)
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        btn.setMinimumSize(80, 70)
        btn.setMaximumSize(80, 70)
        self.addWidget(btn)

        action_text = action.text().replace('\n', '')
        self.actionsDict[action_text] = len(self.actionsDict)

    def addActions(self, actions: Iterable[Action]) -> None:
        for action in actions:
            if action is None:
                self.addSeparator()
            else:
                self.addAction(action)

    def contextMenuEvent(self, event) -> None:
        if "DrawPolygon" in self.actionsDict:
            if self.actionGeometry(self.actions()[self.actionsDict["DrawPolygon"]]).contains(event.pos()):
                # TODO: raise own context menu with options for drawing a circle or a rectangle
                pass

    def init_actions(self, parent):
        """Initialise all actions present which can be connected to buttons or menu items"""
        # TODO: Figure out a more modular way to set up these actions
        action_select = Action(parent,
                               "Select",
                               lambda: self.set_draw_and_type(0, "polygon"),
                               icon="mouse",
                               tip="Select items in the image",
                               checkable=True,
                               checked=True)
        action_draw_poly = Action(parent,
                                  "Draw\nPolygon",
                                  lambda: self.set_draw_and_type(1, "polygon"),
                                  icon="polygon",
                                  tip="Draw Polygon (right click to show options)",
                                  checkable=True)
        action_trace_outline = Action(parent,
                                      "Draw\nTrace",
                                      lambda: self.set_draw_and_type(1, "tempTrace"),
                                      icon="outline",
                                      tip="Trace Outline",
                                      checkable=True)
        action_draw_circle = Action(parent,
                                    "Draw\nEllipse",
                                    lambda: self.set_draw_and_type(1, "ellipse"),
                                    icon="ellipse",
                                    tip="Draw Ellipse",
                                    checkable=True)
        action_draw_rectangle = Action(parent,
                                       "Draw\nRectangle",
                                       lambda: self.set_draw_and_type(1, "rectangle"),
                                       icon="square",
                                       tip="Draw Rectangle",
                                       checkable=True)

        actions = ((action_select,
                    action_draw_poly,
                    action_trace_outline,
                    action_draw_circle,
                    action_draw_rectangle))

        # Init Toolbar
        self.addActions(actions)

    def set_draw_and_type(self, mode, shape_type):
        """
        sets the drawing mode and drawing type of the clicked icon in the toolbar
        """
        self.sSetDrawingMode.emit(mode)
        self.sSetShapeType.emit(shape_type)


    def get_action(self, action_str: str) -> Action:
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.widgetForAction(self.actions()[self.actionsDict[action_str]]).defaultAction()

    def get_widget_for_action(self, action_str: str):
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.widgetForAction(self.actions()[self.actionsDict[action_str]])

    def init_margins(self):
        """This function is necessary because the call to addToolBar in label_ui.py alters the alignment
        for some reason. Therefore, this method will be called AFTER the toolbar is added to the main window"""
        m = (0, 0, 0, 0)
        self.setContentsMargins(*m)
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(*m)