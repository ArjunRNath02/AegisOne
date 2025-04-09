import os
import json
from pathlib import Path
import shutil
import sys
import psutil
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QListWidget, QMessageBox, QSizePolicy, QProgressBar
from PySide6.QtCore import Qt, QTimer, QSettings, Signal
from PySide6.QtGui import QPixmap

from src.windows.system_healthreport import SystemHealthReport


if getattr(sys, 'frozen', False):  # If running as an exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    

class PerformanceUI(QWidget):
    theme_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_changed.connect(self.apply_theme)
        self.load_theme_colors()
        self.setup_ui()
        self.apply_theme()
        self.health_report_window = None

        # Timer to update live stats
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_live_stats)
        self.update_timer.start(5000) 
    
    def load_theme_colors(self):
        settings = QSettings()
        self.theme_name = settings.value("THEME", "Default-theme").lower()
        theme_path = "D:/Project/UI/json-styles/style.json"
        
        self.frame_color = "#444444"
        self.accent_color = "#27ae60"
        self.text_color = "#FFFFFF"
        
        if os.path.exists(theme_path):
            with open(theme_path, "r") as file:
                theme_data = json.load(file)
            themes = theme_data.get("QSettings", [])[0].get("ThemeSettings", [])[0].get("CustomTheme", [])
            for theme in themes:
                if theme["Theme-name"].lower() == self.theme_name:
                    self.accent_color = theme.get("Accent-color", self.accent_color)
                    self.text_color = theme.get("Text-color", self.text_color)
                    self.frame_color = theme.get("Frame-color", "#FFFFFF" if "light" in self.theme_name else "#444444")
                    break
        print(f"🎨 Loaded Theme: {self.theme_name.upper()} | Frame Color: {self.frame_color} | Accent Color: {self.accent_color}")

    def apply_theme(self):
        self.load_theme_colors()
        for frame in [self.memoryFrame, self.diskFrame, self.tempCleanerFrame]:
            frame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px;")
        self.healthButton.setStyleSheet(f"background-color: {self.accent_color}; color: white; border-radius: 20px;")
        for button in self.tempCleanerFrame.findChildren(QPushButton):
            button.setStyleSheet(f"background-color: {self.accent_color}; color: white; border-radius: 10px;")
        self.update()

    def setup_ui(self):
        self.setObjectName("performancePage")

        # Main Layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 10, 20, 10) 
        self.mainLayout.setSpacing(15) 

        # Top Frames Layout (Memory, Disk, System Health)
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(20)  

        self.memoryFrame = self.create_status_frame("Memory Usage")
        self.diskFrame = self.create_status_frame("Disk Usage")
        self.healthButton = self.create_button_frame("System Health Check Report", self.open_system_healthreport)

        self.topLayout.addWidget(self.memoryFrame)
        self.topLayout.addWidget(self.diskFrame)
        self.topLayout.addWidget(self.healthButton)

        self.mainLayout.addLayout(self.topLayout)  
        self.mainLayout.addStretch(1) 

        # 🔹 Bottom Frame (Temporary File Cleaner)
        self.tempCleanerFrame = self.create_temp_cleaner_frame("Temporary Files Cleaner")
        self.mainLayout.addWidget(self.tempCleanerFrame)

        self.resizeEvent(None)

    def create_status_frame(self, title):
        frame = QFrame(self)
        frame.setStyleSheet("background-color: {self.frame_color}; border-radius: 20px;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        title_label = QLabel(title, frame)
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: {self.text_color};")
        layout.addWidget(title_label)

        # Progress bar to show percentage usage
        progress_bar = QProgressBar(frame)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("QProgressBar { background-color: {self.accent_color}; color: {self.text_color}; border-radius: 20px; }")
        layout.addWidget(progress_bar)

        value_label = QLabel("0%", frame)
        value_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        value_label.setStyleSheet("font-size: 18px; color: lightgreen;")
        layout.addWidget(value_label)

        frame.setLayout(layout)
        return frame

    def create_button_frame(self, title, function):
        buttonWidget = QPushButton(self)
        buttonLayout = QVBoxLayout(buttonWidget)
        buttonLayout.setAlignment(Qt.AlignCenter)

        # --- Button Icon ---
        iconLabel = QLabel()
        icon_path = BASE_DIR / "assets" / "images" / "report.png"
        pixmap = QPixmap(str(icon_path))

        if pixmap.isNull():
            print(f"Error: Unable to load icon from {icon_path}")  # Debug message
        else:
            iconLabel.setPixmap(pixmap)
            iconLabel.setScaledContents(True)

        # --- Button Text ---
        textLabel = QLabel(title)
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setObjectName("buttonText")

        # Store reference to dynamically resize later
        buttonWidget.iconLabel = iconLabel
        buttonWidget.textLabel = textLabel

        buttonLayout.addWidget(iconLabel, alignment=Qt.AlignCenter)
        buttonLayout.addWidget(textLabel, alignment=Qt.AlignCenter)

        if function:
            buttonWidget.clicked.connect(function)

        buttonWidget.setStyleSheet("background-color: {self.accent_color}; border-radius: 20px; color: {self.text_color};")

        self.set_button_initial_size(buttonWidget)

        return buttonWidget

    def set_button_initial_size(self, buttonWidget):
        buttonWidget.setFixedSize(120, 120)  # Default button size
        buttonWidget.iconLabel.setFixedSize(50, 50)  # Default icon size
        buttonWidget.textLabel.setStyleSheet("font-size: 14px;")  # Default text size

    def create_temp_cleaner_frame(self, title):
        frame = QFrame(self)
        frame.setStyleSheet("background-color: {self.frame_color}; border-radius: 20px;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title_label = QLabel(title, frame)
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: {self.text_color};")
        layout.addWidget(title_label)

        # File List Box
        self.file_listbox = QListWidget(frame)
        self.file_listbox.setSelectionMode(QListWidget.MultiSelection)
        self.file_listbox.setStyleSheet("background-color: {self.frame_color}; color: {self.text_color}; border-radius: 20px; padding: 5px;")
        layout.addWidget(self.file_listbox)

        self.update_temp_files_list()

        # Buttons Layout
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(15)

        buttons_info = [
            ("Delete Selected", self.delete_selected_files),
            ("Select All", lambda: self.file_listbox.selectAll()),
            ("Deselect All", lambda: self.file_listbox.clearSelection())
        ]

        for text, command in buttons_info:
            button = QPushButton(text)
            button.setStyleSheet("background-color: {self.accent_color}; color: {self.text_color}; border-radius: 20px; font-size: 14px;")
            button.clicked.connect(command)
            buttonLayout.addWidget(button)

        layout.addLayout(buttonLayout)
        frame.setLayout(layout)
        return frame

    def update_live_stats(self):
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        self.memoryFrame.layout().itemAt(1).widget().setValue(memory_usage)
        self.memoryFrame.layout().itemAt(2).widget().setText(f"{memory_usage}%")

        self.diskFrame.layout().itemAt(1).widget().setValue(disk_usage)
        self.diskFrame.layout().itemAt(2).widget().setText(f"{disk_usage}%")

    def resizeEvent(self, event):
        width = self.width()
        height = self.height()

      #Top Frame Scaling
        top_frame_width = int(width * 0.3)  
        top_frame_height = int(height * 0.2)  

        for frame in [self.memoryFrame, self.diskFrame, self.healthButton]:  
            frame.setFixedSize(top_frame_width, top_frame_height)

      #Button Scaling
        icon_size = int(top_frame_height * 0.5)  
        text_size = int(top_frame_height * 0.13)

        self.healthButton.iconLabel.setFixedSize(icon_size, icon_size)
        self.healthButton.textLabel.setStyleSheet(f"font-size: {text_size}px;")

      #Temporary File Cleaner Frame Scaling
        temp_cleaner_width = int(width * 0.95) 
        temp_cleaner_height = int(height * 0.7) 
        self.tempCleanerFrame.setFixedSize(temp_cleaner_width, temp_cleaner_height)

        button_width = int(width * 0.25)  
        button_height = int(height * 0.08)  

        for button in self.tempCleanerFrame.findChildren(QPushButton):
            button.setFixedSize(button_width, button_height)

        super().resizeEvent(event)

    def list_temp_files(self):
        temp_dir = os.getenv("TEMP")
        return [os.path.join(temp_dir, file) for file in os.listdir(temp_dir)] if temp_dir else []

    def update_temp_files_list(self):
        self.file_listbox.clear()
        temp_files = self.list_temp_files()
        self.file_listbox.addItems(temp_files)

    def delete_selected_files(self):
        selected_items = self.file_listbox.selectedItems()
        files_to_delete = [item.text() for item in selected_items]

        undeleted_files = []
        for file_path in files_to_delete:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except:
                undeleted_files.append(file_path)

        if undeleted_files:
            QMessageBox.warning(self, "Files in Use", f"Could not delete:\n\n{chr(10).join(undeleted_files)}")
        else:
            QMessageBox.information(self, "Success", "Selected files deleted successfully!")

        self.update_temp_files_list()

    def open_system_healthreport(self):
        if not self.health_report_window or not self.health_report_window.isVisible():
            self.health_report_window = SystemHealthReport(self)
            self.health_report_window.show()

