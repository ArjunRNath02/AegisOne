# GUI FUNCTIONS
# Import necessary modules from PySide6 and custom widgets
from Custom_Widgets import *
from Custom_Widgets.QAppSettings import QAppSettings
from Custom_Widgets.QCustomTipOverlay import QCustomTipOverlay
from Custom_Widgets.QCustomLoadingIndicators import QCustom3CirclesLoader

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QMessageBox

import psutil
from src.extensions.scan_function import callThread


class GuiFunctions():
    def __init__(self, MainWindow):
        self.main = MainWindow  # Store the main window instance
        self.ui = MainWindow.ui  # Store the UI instance
        self.detect_usb()

        # Apply font
        self.loadProductSansFont()

        # init app theme
        self.initializeAppTheme()

        # add click event to search button
        self.ui.searchBtn.clicked.connect(self.showSearchResults)

         # connect menu btns
        self.connectMenuButtons()

    
    # connect menu buttons
    def connectMenuButtons(self):
        """Connect buttons to expand/collapse menu widgets."""
        # Expand center menu widget
        self.ui.settingsBtn.clicked.connect(lambda: self.ui.centerMenu.expandMenu())
        self.ui.infoBtn.clicked.connect(lambda: self.ui.centerMenu.expandMenu())
        self.ui.helpBtn.clicked.connect(lambda: self.ui.centerMenu.expandMenu())

        # Close center menu widget
        self.ui.closeCenterMenuBtn.clicked.connect(lambda: self.ui.centerMenu.collapseMenu())

        # Expand right menu widget
        self.ui.notificationBtn.clicked.connect(lambda: self.ui.rightMenu.expandMenu())
        self.ui.moreBtn.clicked.connect(lambda: self.ui.rightMenu.expandMenu())
        self.ui.profileBtn.clicked.connect(lambda: self.ui.rightMenu.expandMenu())

        # Close right menu widget
        self.ui.closeRightMenuBtn.clicked.connect(lambda: self.ui.rightMenu.collapseMenu())


    # create search tooltip
    def createSearchTipOverlay(self):
        """Create a search tip overlay under the search input"""
        self.searchTooltip = QCustomTipOverlay(
            title="Search results.",
            description="Searching...",
            icon=self.main.theme.PATH_RESOURCES+"feather/search.png", #icon path from theme resources
            isClosable=True,
            target=self.ui.searchInpCont,
            parent=self.main,
            deleteOnClose=True,
            duration=-1, #set duration to -1 to prevent auto-close 
            tailPosition="top-center",
            closeIcon=self.main.theme.PATH_RESOURCES+"material_design/close.png",
            toolFlag = True
        )

        # Create loader
        loader = QCustom3CirclesLoader(
            parent=self.searchTooltip,
            color=QColor(self.main.theme.COLOR_ACCENT_1), #color from theme
            penWidth=20,
            animationDuration=400
        )

        # add loader to the tipoverlay
        self.searchTooltip.addWidget(loader)


    # show tip ovelay
    def showSearchResults(self):
        # only show search container if search phrase is not empty
        searchPhrase = self.ui.searchInp.text()
        # if phrase is empty
        if not searchPhrase:
            return
        
        try:
            self.searchTooltip.show()
        except: #tooltip deleted
            # re-init
            self.createSearchTipOverlay()
            self.searchTooltip.show()

        # update search descriptions
        self.searchTooltip.setDescription("Showing search results for: "+searchPhrase)

    

    # Initialize app theme
    def initializeAppTheme(self):
        """Initialize the application theme from settings"""
        settings = QSettings()
        current_theme = settings.value("THEME")

        # Add theme to the theme list
        self.populateThemeList(current_theme)

        # Connect theme change signal to change app theme
        self.ui.themeList.currentTextChanged.connect(self.changeAppTheme)

    def populateThemeList(self, current_theme):
        """Populate the list from available app themes"""
        theme_count = -1
        for theme in self.ui.themes:
            self.ui.themeList.addItem(theme.name, theme.name)
            # check default theme/current theme
            if theme.defaultTheme or theme.name == current_theme:
                self.ui.themeList.setCurrentIndex(theme_count)

    # Change app theme
    def changeAppTheme(self):
        """Change the application theme dynamically."""
        settings = QSettings()
        selected_theme = self.ui.themeList.currentData()
        current_theme = settings.value("THEME")

        if current_theme != selected_theme:
            settings.setValue("THEME", selected_theme)
            QAppSettings.updateAppSettings(self.main, reloadJson=True)

            if hasattr(self.main.ui, "homePage") and hasattr(self.main.ui.homePage, "theme_changed"):
                print(f"🔄 Theme changed to {selected_theme}. Updating UI...")
                self.main.ui.homePage.theme_changed.emit()
            
            if hasattr(self.main.ui, "scanPage") and hasattr(self.main.ui.scanPage, "theme_changed"):
                print(f"🔄 Theme changed to {selected_theme}. Updating UI...")
                self.main.ui.scanPage.theme_changed.emit()

            if hasattr(self.main.ui, "updatePage") and hasattr(self.main.ui.updatePage, "theme_changed"):
                print(f"🔄 Theme changed to {selected_theme}. Updating UI...")
                self.main.ui.updatePage.theme_changed.emit()
            
            if hasattr(self.main.ui, "performancePage") and hasattr(self.main.ui.performancePage, "theme_changed"):
                print(f"🔄 Theme changed to {selected_theme}. Updating UI...")
                self.main.ui.performancePage.theme_changed.emit()


    # Apply custom font
    def loadProductSansFont(self):
        """Load and apply Product Sans font"""
        font_id = QFontDatabase.addApplicationFont(
            "./fonts/google-sans-cufonfonts/Product Sans-Regular.ttf"
        )

        # If font not loaded
        if font_id == -1:
            print("Failed to load Product Sans font")
            return

        # Apply font
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            product_sans = QFont(font_family[0])
        else:
            product_sans = QFont("Sans Serif")

        # Apply to main window
        self.main.setFont(product_sans)

    
    def detect_usb(self):
        """ Continuously monitor for USB insertion """
        self.previous_devices = set(psutil.disk_partitions())
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_usb)
        self.timer.start(5000)  # Check every 5 seconds

    def check_usb(self):
        current_devices = set(psutil.disk_partitions())
        new_devices = current_devices - self.previous_devices

        for device in new_devices:
            if 'removable' in device.opts:
                usb_path = device.device
                self.ask_usb_scan(usb_path)

        self.previous_devices = current_devices

    def ask_usb_scan(self, usb_path):
        """ Prompt the user to scan the USB """
        reply = QMessageBox.question(
            self.main,
            "USB Detected",
            f"A new USB device was detected at {usb_path}. Do you want to scan it?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            scan_result = callThread("USB Scan", usb_path)
            QMessageBox.information(self.main, "Scan Complete", scan_result)
