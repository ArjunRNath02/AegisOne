import os
from pathlib import Path
import sys
import cv2
import json
import psutil
import sounddevice as sd
import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, QSettings
from PySide6.QtGui import QPixmap

from src.windows.scan_log import display_scan_logs
from src.windows.add_malwaretypes import MalwareTypeDialog


if getattr(sys, 'frozen', False):  # If running as an exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    
class UpdateUI(QWidget):
    theme_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_changed.connect(self.apply_theme)
        self.load_theme_colors()
        self.setup_ui()
        self.apply_theme()

        # Live updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.run_async_checks)
        self.update_timer.start(5000)  # Update every 5 seconds

    def load_theme_colors(self):
        settings = QSettings()
        self.theme_name = settings.value("THEME", "Default-theme").lower()
        theme_path = os.path.join("D:/Project/UI/json-styles", "style.json")

        if not os.path.exists(theme_path):
            print(f"⚠ Warning: Theme file {theme_path} not found! Using default colors.")
            self.background_color = "#2B2B2B"
            self.text_color = "#FFFFFF"
            self.accent_color = "#27ae60"
            self.frame_color = "#444444"
            return

        with open(theme_path, "r") as file:
            theme_data = json.load(file)

        themes = theme_data.get("QSettings", [])[0].get("ThemeSettings", [])[0].get("CustomTheme", [])

        self.background_color = "#2B2B2B"
        self.text_color = "#FFFFFF"
        self.accent_color = "#27ae60"
        self.frame_color = "#444444"

        for theme in themes:
            if theme["Theme-name"].lower() == self.theme_name:
                self.background_color = theme.get("Background-color", self.background_color)
                self.text_color = theme.get("Text-color", self.text_color)
                self.accent_color = theme.get("Accent-color", "#0000FF")
                self.frame_color = theme.get("Frame-color", "#FFFFFF" if "light" in self.theme_name else "#444444")
                break  

        print(f"🎨 Loaded Theme: {self.theme_name.upper()} | Frame Color: {self.frame_color} | Accent Color: {self.accent_color}")

    def apply_theme(self):
        self.load_theme_colors()
        self.setStyleSheet(f"background-color: {self.background_color};")

        for button in [self.scanLogButton, self.updateDatabaseButton]:
            button.setStyleSheet(f"background-color: {self.accent_color}; color: {self.text_color}; border-radius: 20px;")
        
        for frame in [self.securityFrame, self.batteryFrame, self.powerConsumptionFrame]:
            frame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px; padding: 10px;")
        
        self.repaint()
        self.update()

    def setup_ui(self):
        self.setObjectName("updatePage")
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout) 
        self.mainLayout.setContentsMargins(20, 10, 20, 10)
        self.mainLayout.setSpacing(20)

        #Left-Side Buttons (Scan Logs, Update Database)
        self.leftLayout = QVBoxLayout()
        self.leftLayout.setSpacing(10)

        log_icon = BASE_DIR / "assets" / "images" / "log.png"
        db_icon = BASE_DIR / "assets" / "images" / "refresh.png"
        self.scanLogButton = self.create_button("Scan Logs", str(log_icon), self.open_scan_logs)
        self.updateDatabaseButton = self.create_button("Update Database", str(db_icon), self.open_malware_types)

        self.leftLayout.addWidget(self.scanLogButton)
        self.leftLayout.addWidget(self.updateDatabaseButton)

        #Right-Side Layout
        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(20)

        self.securityFrame = self.create_status_frame("Camera & Microphone Check")
        self.batteryFrame = self.create_status_frame("Battery Details") 
        self.powerConsumptionFrame = self.create_status_frame("High Power Apps")

        self.rightLayout.addWidget(self.securityFrame)
        self.rightLayout.addWidget(self.batteryFrame)
        self.rightLayout.addWidget(self.powerConsumptionFrame)

        #Main Layout (Split Left & Right)
        self.mainLayout.addLayout(self.leftLayout, 1)  # Buttons (Left)
        self.mainLayout.addLayout(self.rightLayout, 2)  # Frames (Right)

        self.resizeEvent(None)

    def create_button(self, text, icon_path, function=None):
        button = QPushButton()
        layout = QVBoxLayout(button)
        layout.setAlignment(Qt.AlignCenter)

        iconLabel = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            iconLabel.setPixmap(pixmap)
            iconLabel.setScaledContents(True)
        else:
            iconLabel.setText("⚠️")  # Fallback if icon is missing

        button.iconLabel = iconLabel
        textLabel = QLabel(text)
        textLabel.setAlignment(Qt.AlignCenter)
        button.textLabel = textLabel

        layout.addWidget(iconLabel, alignment=Qt.AlignCenter)
        layout.addWidget(textLabel, alignment=Qt.AlignCenter)

        if function:
            button.clicked.connect(function)

        button.setStyleSheet("background-color: {self.accent_color}; border-radius: 20px; font-size: 14px;")
        return button

    def create_security_frame(self, title):
        """Camera & Mic Frame with Lock Icon if Active"""
        frame = QFrame(self)
        frame.setStyleSheet("background-color: {self.frame_color}; border-radius: 20px; border: 2px solid transparent;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        title_label = QLabel(title, frame)
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: {self.text_color};")
        layout.addWidget(title_label)

        # 🔒 Lock/Unlock Indicator
        self.lockIcon = QLabel(frame)
        self.lockIcon.setPixmap(QPixmap("assets/icons/lock.png"))  # Default locked icon
        self.lockIcon.setScaledContents(True)
        self.lockIcon.setFixedSize(50, 50)  # Adjust size
        layout.addWidget(self.lockIcon, alignment=Qt.AlignCenter)

        # Status Label
        self.statusLabel = QLabel("Checking...", frame)
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setStyleSheet("font-size: 14px; color: lightgreen; font-weight : bold;")
        layout.addWidget(self.statusLabel)

        frame.setLayout(layout)
        return frame

    def create_status_frame(self, title):
        frame = QFrame(self)
        frame.setStyleSheet("background-color: {self.frame_color}; border-radius: 20px;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        title_label = QLabel(title, frame)
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: {self.text_color};")
        layout.addWidget(title_label)

        self.statusLabel = QLabel("Checking...", frame)
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setStyleSheet("font-size: 14px; color: lightgreen; font-weight: bold;")
        layout.addWidget(self.statusLabel)

        frame.setLayout(layout)
        return frame

    def set_status(self, frame, status_text):
        """Update text inside a given frame"""
        widget = frame.layout().itemAt(1).widget()
        if isinstance(widget, QLabel):
            widget.setText(status_text)

    def run_async_checks(self):
        """Run security & power checks asynchronously (prevents lag)."""
        threading.Thread(target=self.update_live_stats, daemon=True).start()

    def update_live_stats(self):
        # Camera & Microphone Check
        cap = cv2.VideoCapture(0)
        cam_status = "⚠️ Camera in use!" if cap.isOpened() else "✅ Camera not in use."
        cap.release()

        devices = sd.query_devices()
        mic_status = "⚠️ Microphone in use!" if any('input' in device['name'].lower() for device in devices) else "✅ Microphone is off."

        self.set_status(self.securityFrame, f"{cam_status}\n{mic_status}")

        # Battery Details
        battery = psutil.sensors_battery()
        battery_status = f"🔋 Battery: {battery.percent}% ({'Charging' if battery.power_plugged else 'Not Charging'})"
        self.set_status(self.batteryFrame, battery_status)

        # High Power Apps
        top_apps = sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)[:3]
        power_usage = "\n".join(f"{app.info['name']} → {app.info['cpu_percent']}% CPU" for app in top_apps)
        self.set_status(self.powerConsumptionFrame, power_usage if power_usage else "No high power apps detected")

    def resizeEvent(self, event):
        width, height = self.width(), self.height()

        # Adjust Left Buttons
        button_width = int(width * 0.2) 
        button_height = int(height * 0.3)  

        for button in [self.scanLogButton, self.updateDatabaseButton]:
            button.setFixedSize(button_width, button_height)

        # Adjust Right-Side Frames
        frame_width = int(width * 0.65)  
        frame_height = int(height * 0.3)  

        self.securityFrame.setFixedSize(frame_width, frame_height)
        self.batteryFrame.setFixedSize(frame_width, frame_height)
        self.powerConsumptionFrame.setFixedSize(frame_width, frame_height)

        super().resizeEvent(event)

    def open_scan_logs(self):
            """Open Scan Log Window when button is clicked."""
            display_scan_logs(self)

    def open_malware_types(self):
        """Opens the malware types management window."""
        self.malware_window = MalwareTypeDialog(self)
        self.malware_window.exec_()