COMMENT_LIST = """QListWidget {
                  color: rgb(0, 102, 204);
                  selection-color: blue;
                  selection-background-color: white;
                  }
                  
                  QListWidget::item:hover {
                  color: blue;
                  } 
                  """

BUTTON_STYLESHEET = """QPushButton {
                       background-color: lightgray;
                       color: black;
                       min-height: 2em;
                       border-width: 2px;
                       border-radius: 8px;
                       border-color: black;
                       font: bold 12px;
                       padding: 2px;
                       }
                       
                       QPushButton::hover {
                       background-color: gray;
                       }
                       
                       QPushButton::pressed {
                       border-style: outset;
                       }
                       """

TAB_STYLESHEET = """ QTabWidget::pane {
                     border: 1px solid lightgray;
                     top:-1px;
                     } 
                     
                     QTabWidget::tab-bar {
                     left: 0px;
                     }
                     
                     QTabBar::tab {
                     background: rgb(205, 205, 212);
                     min-width: 8ex; 
                     padding: 7px;
                     } 
                     
                     QTabBar::tab:hover { 
                     background: rgb(220, 220, 220);
                     }
                     
                     QTabBar::tab:selected { 
                     background: white; 
                     border-left: 1px solid lightgray;
                     border-right: 1px solid lightgray; 
                     border-top: none;
                     border-bottom: none;
                     font: bold;
                     }
                     """
