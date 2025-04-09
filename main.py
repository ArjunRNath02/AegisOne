
import os
import sys

from src.ui_interface import *
from Custom_Widgets import *
from Custom_Widgets.QAppSettings import QAppSettings
from src.Functions import GuiFunctions 


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.orginazationName = "AegisOne"
        self.applicationName = "Cybersecurity"
        self.orginazationDomain = "aegisone.com"
        
        # Use this to specify your json file(s) path/name
        loadJsonStyle(self, self.ui, jsonFiles = {"json-styles/style.json"}) 
        
        self.show() 

        # Update app settings
        QAppSettings.updateAppSettings(self)

        # Application functions and events
        self.app_functions = GuiFunctions(self)


    # GET THE THEME CHANGE PROGRESS
    # sassCompilationProgress() is the default function that sass compiler will look for and return the progress value to 
    def sassCompilationProgress(self, n):
        # n is the percentage progress value
        self.ui.activityProgress.setValue(n)

if __name__ == "__main__":
    app = QApplication(sys.argv)
   
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
