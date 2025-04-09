from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QSizePolicy, QMessageBox
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtCore import Qt, QTimer,  QSettings, Signal

import psutil
from src.extensions.scan_function import callThread
import json
import os
import sys
from pathlib import Path
import psutil
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from src.windows.quick_scan import QuickScanWindow
from src.windows.system_healthreport import SystemHealthReport
from src.windows.scan_log import display_scan_logs
from src.windows.usb_scan import USBScanWindow


if getattr(sys, 'frozen', False):  # If running as an exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

print(f"🔍 Checking database at: {BASE_DIR}")


class CPUGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cpu_usage = 0
        self.parent_ui = parent
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cpu_usage)
        self.timer.start(500)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_cpu_usage(self):
        self.cpu_usage = psutil.cpu_percent(interval=None)
        self.update()  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width, height = self.width(), self.height()
        center_x, center_y = width // 2, height - 40
        radius = min(width, height * 2) // 2 - 20  
        start_angle = 0
        span_angle = int((self.cpu_usage / 100) * 180)

        accent_color = self.parent_ui.accent_color if hasattr(self.parent_ui, "accent_color") else "#27ae60" 
        # Background arc (Gray)
        pen_bg = QPen(QColor("#555"))
        pen_bg.setWidth(max(10, int(radius * 0.2)))  
        painter.setPen(pen_bg)
        painter.drawArc(center_x - radius, center_y - radius, 2 * radius, 2 * radius, 0 * 16, 180 * 16)

        # Foreground arc (CPU Usage) - Uses **accent color**
        pen_fg = QPen(QColor(accent_color))  
        pen_fg.setWidth(max(10, int(radius * 0.2)))
        painter.setPen(pen_fg)
        painter.drawArc(center_x - radius, center_y - radius, 2 * radius, 2 * radius, start_angle * 16, span_angle * 16)

        # CPU usage text
        font_size = max(10, int(min(width, height) * 0.1))  
        painter.setFont(QFont("Arial", font_size, QFont.Bold))
        painter.drawText(0, height - font_size - 40, width, int(height * 0.2),
                        Qt.AlignHCenter | Qt.AlignBottom, f"{self.cpu_usage:.1f}%")

        painter.end() 


class HomeUI(QWidget):
    theme_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_changed.connect(self.apply_theme) 
        self.load_theme_colors()
        
        self.setup_ui()
        self.apply_theme()
        self.quick_scan_window = None

        self.usb_path = None  # Store the detected USB path
        self.detect_usb()

    def load_theme_colors(self):
        settings = QSettings()

        self.theme_name = settings.value("THEME", "Default-theme").lower()

        theme_path = BASE_DIR / "json-styles" / "style.json"

        if not os.path.exists(theme_path):
            print(f"⚠ Warning: Theme file {theme_path} not found! Using default colors.")
            self.background_color = "#2B2B2B"
            self.text_color = "#FFFFFF"
            self.accent_color = "#27ae60"  # Default green
            self.frame_color = "#444444"  # Default gray
            return

        with open(theme_path, "r") as file:
            theme_data = json.load(file)

        themes = theme_data.get("QSettings", [])[0].get("ThemeSettings", [])[0].get("CustomTheme", [])

        # Set defaults first
        self.background_color = "#2B2B2B"
        self.text_color = "#FFFFFF"
        self.accent_color = "#27ae60"
        self.frame_color = "#444444"  # Default gray

        for theme in themes:
            if theme["Theme-name"].lower() == self.theme_name:
                self.background_color = theme.get("Background-color", self.background_color)
                self.text_color = theme.get("Text-color", self.text_color)

                if "light" in self.theme_name:
                    self.accent_color = theme.get("Accent-color", "#0000FF")  
                    self.frame_color = theme.get("Frame-color", "#FFFFFF") 
                else:
                    self.accent_color = theme.get("Accent-color", self.accent_color)  
                    self.frame_color = theme.get("Frame-color", self.frame_color) 
                break  

        print(f"🎨 Loaded Theme: {self.theme_name.upper()} | Frame Color: {self.frame_color} | Accent Color: {self.accent_color}")

    def apply_theme(self):
        self.load_theme_colors()  

        # Apply Stylesheets to Frames
        self.bannerFrame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px;")
        
        for frame in [self.cpuUsageFrame, self.usbFrame, self.threatGraphFrame]:
            frame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px;")

        # Update Text Colors
        self.bannerText.setStyleSheet(f"color: {self.text_color}; font-size: 18px;")
        self.usbStatusLabel.setStyleSheet(f"color: {self.text_color}; font-size: 14px; font-weight: bold;")

        # Update Buttons with the new accent color
        for button in self.buttons:
            button.setStyleSheet(f"background-color: {self.accent_color}; color: {self.text_color}; border-radius: 20px;")

        self.cpuGauge.update()
        self.update_threat_graph()

        self.repaint()  
        self.update()  


    def setup_ui(self):
        self.setObjectName("homePage")

     # --- Main Layout ---
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)
        self.mainLayout.setSpacing(20)

     # --- Banner Frame ---
        self.bannerFrame = QFrame(self)
        self.bannerFrame.setStyleSheet("background-color: #2B2B2B; border-radius: 20px;")

        self.bannerLayout = QHBoxLayout(self.bannerFrame)
        self.bannerLayout.setAlignment(Qt.AlignLeft)
        self.bannerLayout.setContentsMargins(20, 0, 0, 0)
        # --- Shield Icon ---
        self.shieldIcon = QLabel(self.bannerFrame)
        icon_path = BASE_DIR / "assets" / "images" / "shield.png"
        self.shieldIcon.setPixmap(QPixmap(str(icon_path)))
        self.shieldIcon.setScaledContents(True)
        # --- Banner Text ---
        self.bannerText = QLabel(self.bannerFrame)
        self.bannerText.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.bannerText.setObjectName("bannerText")

        self.bannerLayout.addWidget(self.shieldIcon)
        self.bannerLayout.addWidget(self.bannerText)
        self.mainLayout.addWidget(self.bannerFrame, alignment=Qt.AlignTop | Qt.AlignHCenter)

     # --- Middle Frames ---
        self.framesLayout = QHBoxLayout()
        self.framesLayout.setSpacing(10)

        self.cpuUsageFrame = self.create_frame("CPU Usage")
        self.usbFrame = self.create_frame("")
        self.threatGraphFrame = self.create_frame("Threat Density Over Time")


        self.framesLayout.addWidget(self.cpuUsageFrame)
        self.framesLayout.addWidget(self.usbFrame)
        self.framesLayout.addWidget(self.threatGraphFrame, stretch=1)
        self.mainLayout.addLayout(self.framesLayout)

        self.cpuUsageFrame.setFixedSize(250, 200)
        self.usbFrame.setFixedSize(230, 200)
        self.threatGraphFrame.setFixedSize(370, 200)

        # --- CPU Gauge ---
        self.cpuGauge = CPUGauge(self.cpuUsageFrame)
        self.cpuUsageFrame.layout().addWidget(self.cpuGauge, alignment=Qt.AlignCenter)
        
        # --- USB Checker ---
        usb_icon_path = BASE_DIR / "assets" / "images" / "usb.png" 
        self.usbIconLabel = QLabel(self.usbFrame)
        self.usbIconLabel.setPixmap(QPixmap(str(usb_icon_path)).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.usbIconLabel.setAlignment(Qt.AlignCenter)
        self.usbIconLabel.setStyleSheet("margin-top: 40px;")

        self.usbStatusLabel  = QLabel("No USB Connected", self.usbFrame)
        self.usbStatusLabel.setAlignment(Qt.AlignCenter)
        self.usbStatusLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        self.usbStatusLabel.setObjectName('frameTitle')

        self.usbFrame.layout().addWidget(self.usbIconLabel)
        self.usbFrame.layout().addWidget(self.usbStatusLabel)

        self.usbFrame.mousePressEvent = self.scan_usb

        # --- Threat Graph ---
        self.figure, self.ax = plt.subplots(figsize=(4, 2), dpi=60)
        self.figure.patch.set_alpha(0)  # Transparent Background
        self.canvas = FigureCanvas(self.figure)
        self.threatGraphFrame.layout().addWidget(self.canvas)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow resizing
        
        self.update_threat_graph()

        # Add Stretch to Push Buttons to Bottom
        self.mainLayout.addStretch(1)

     # --- Bottom Buttons ---
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)
        scan_logo = BASE_DIR / "assets" / "images" / "scan.png"
        logs_logo = BASE_DIR / "assets" / "images" / "log.png"
        report_logo = BASE_DIR / "assets" / "images" / "report.png"
        settings_logo = BASE_DIR / "assets" / "images" / "settings.png"
        help_logo = BASE_DIR / "assets" / "images" / "headphones.png"

        button_info = [
            ("Scan", str(scan_logo), self.open_quick_scan),
            ("Logs", str(logs_logo), self.open_scan_logs),
            ("Reports", str(report_logo), self.open_system_healthreport),
            ("Settings", str(settings_logo), None),
            ("Help", str(help_logo), None),
        ]

        self.buttons = []
        for text, icon_path, function in button_info:
            button = self.create_button(text, icon_path, function)
            self.buttonLayout.addWidget(button)
            self.buttons.append(button)

        self.mainLayout.addLayout(self.buttonLayout)

        # Apply initial scaling
        self.resizeEvent(None)

    def create_frame(self, title):
        frame = QFrame(self)
        frame.setStyleSheet("background-color: {self.frame_color}; border-radius: 20px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        frame.setLayout(layout)

        if title:  # Add label only if title exists
            title_label = QLabel(title, frame)
            title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            title_label.setObjectName('frameTitle')
            layout.addWidget(title_label)

        return frame

    def create_button(self, text, icon_path, function=None):
        buttonWidget = QPushButton()
        buttonWidget.setStyleSheet(f"background-color: {self.accent_color}; color: {self.text_color}; border-radius: 20px;")

        buttonLayout = QVBoxLayout(buttonWidget)
        buttonLayout.setAlignment(Qt.AlignCenter)

        iconLabel = QLabel()
        iconLabel.setPixmap(QPixmap(icon_path))
        iconLabel.setScaledContents(True)
        buttonWidget.iconLabel = iconLabel  # ✅ Store reference for resizing

        textLabel = QLabel(text)
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setStyleSheet(f"color: {self.text_color}; font-size: 14px;")
        buttonWidget.textLabel = textLabel  # ✅ Store reference for resizing

        buttonLayout.addWidget(iconLabel, alignment=Qt.AlignCenter)
        buttonLayout.addWidget(textLabel, alignment=Qt.AlignCenter)

        if function:
            buttonWidget.clicked.connect(function)

        return buttonWidget

    def set_button_initial_size(self, buttonWidget):
        buttonWidget.setFixedSize(120, 120)  # Default button size
        buttonWidget.iconLabel.setFixedSize(50, 50)  # Default icon size
        buttonWidget.textLabel.setStyleSheet("font-size: 14px;")  # Default text size

    def resizeEvent(self, event):
        if event is None:
            width, height = 1010, 620  # Default size when opening the window
        else:
            width, height = self.width(), self.height()  # Get current window size

      # Banner Scaling
        banner_width = int(width * 0.8)  # 80% of the window width
        banner_height = int(height * 0.2)  # 20% of the window height
        self.bannerFrame.setFixedSize(banner_width, banner_height)

      # ShieldIcon Scaling
        shield_size = int(banner_height * 0.8)
        self.shieldIcon.setFixedSize(shield_size, shield_size)

      # BannerText Scaling
        font_size_large = int(banner_height * 0.25)
        font_size_small = int(banner_height * 0.15)
        self.bannerText.setText(
            f"<b><span style='font-size:{font_size_large}px;'>You are protected</span></b><br>"
            f"<span style='font-size:{font_size_small}px;'>All shields active<br>Everything up to date</span>"
        )

      # CPU Usage Frame
        cpu_frame_width = int(width * 0.3)
        cpu_frame_height = int(height * 0.4)
        self.cpuUsageFrame.setFixedSize(cpu_frame_width, cpu_frame_height)

        self.cpuGauge.setFixedSize(cpu_frame_width - 40, cpu_frame_height - 40)
        self.cpuGauge.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

      # USB Checker Frame
        usb_frame_width = int(width * 0.2)
        usb_frame_height = cpu_frame_height
        self.usbFrame.setFixedSize(usb_frame_width, usb_frame_height)

      # Threat Graph Frame 
        threat_frame_width = int((width - (cpu_frame_width + usb_frame_width + 70)) * 1)
        threat_frame_height = int(cpu_frame_height * 1)  
        self.threatGraphFrame.setFixedSize(threat_frame_width, threat_frame_height)
        
      # Button Scaling
        button_width = int(width * 0.18)
        button_height = int(height * 0.25)  
        icon_size = int(button_height * 0.5)  
        text_size = int(button_height * 0.12)  

        for button in self.buttons:
            button.setFixedSize(button_width, button_height)
            button.iconLabel.setFixedSize(icon_size, icon_size)
            button.textLabel.setStyleSheet(f"font-size: {text_size}px;")

        super().resizeEvent(event)

    def open_quick_scan(self):
        if self.quick_scan_window is None or not self.quick_scan_window.isVisible():
            self.quick_scan_window = QuickScanWindow()
            self.quick_scan_window.show()

    def open_system_healthreport(self):
        if not hasattr(self, 'health_report_window') or not self.health_report_window.isVisible():
            self.health_report_window = SystemHealthReport(self)  # Pass main window as parent
            self.health_report_window.show()

    def update_cpu_usage(self):
            cpu_usage = psutil.cpu_percent()
            self.cpuArc.repaint()
            
            def paintEvent(event):
                painter = QPainter(self.cpuArc)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(QColor("#00bcff"), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawArc(10, 10, 130, 80, 0 * 16, int((cpu_usage / 100) * 180) * 16)
                painter.end()
            
            self.cpuArc.paintEvent = paintEvent

    def update_threat_graph(self):
        x = np.arange(1, 8)
        y = np.random.randint(0, 10, size=7)
        self.ax.clear()
        self.ax.set_facecolor("none")  # Transparent

        # ✅ Use dynamic accent color
        accent_color = self.accent_color if hasattr(self, "accent_color") else "red"

        self.ax.fill_between(x, y, color=accent_color, alpha=0.2)
        self.ax.plot(x, y, marker='o', color=accent_color, linestyle='dashed')

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(["Jan", "Feb", "Apr", "Jun", "Aug", "Oct", "Dec"])

        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.grid(False)
        self.canvas.draw()

    def open_scan_logs(self):
        """Open Scan Log Window when button is clicked."""
        display_scan_logs(self)

    def detect_usb(self):
        """ Monitor USB connection status dynamically """
        self.previous_devices = set(psutil.disk_partitions())

        self.usb_timer = QTimer()
        self.usb_timer.timeout.connect(self.update_usb_status)
        self.usb_timer.start(5000)  # Check every 5 seconds

    def update_usb_status(self):
        """ Check for USB changes and update UI """
        current_devices = set(psutil.disk_partitions())
        new_devices = current_devices - self.previous_devices

        usb_detected = False  # Track if a USB is present

        for device in current_devices:
            if 'removable' in device.opts:
                self.usb_path = device.device  # Store USB path
                usb_detected = True  # Mark that USB is present

        if usb_detected:
            self.usbStatusLabel.setText(f"USB Detected: {self.usb_path}")
            self.usbStatusLabel.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.usb_path = None  # Reset only if no USB is connected
            self.usbStatusLabel.setText("No USB Connected")
            self.usbStatusLabel.setStyleSheet("color: red; font-weight: bold;")

        self.previous_devices = current_devices  # Update tracking


    def scan_usb(self, event):
        """ Open USB Scan Window if a USB is connected """
        if self.usb_path:
            response = QMessageBox.question(
                self,
                "USB Detected",
                f"A new USB device was detected at {self.usb_path}.\nDo you want to scan it?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if response == QMessageBox.Yes:
                self.usb_scan_window = USBScanWindow(self.usb_path)
                self.usb_scan_window.show()
            else:
                # ✅ Keep the USB status unchanged
                self.usbStatusLabel.setText(f"USB Detected: {self.usb_path}")
                self.usbStatusLabel.setStyleSheet("color: green; font-weight: bold;")
        else:
            QMessageBox.warning(self, "No USB Detected", "Please insert a USB device first.")

