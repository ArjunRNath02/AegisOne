from pathlib import Path
import sys
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QSizePolicy
from PySide6.QtGui import QPixmap, QFont, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QSettings, QTimer, Signal
import numpy as np
import re
import os
import json
import mplcursors
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from src.windows.quick_scan import QuickScanWindow
from src.windows.custom_scan import CustomScanWindow
from src.windows.full_scan import FullScanWindow
from src.extensions.db_handler import get_all_scan_log, get_all_type_master


if getattr(sys, 'frozen', False):  # If running as an exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    
class ScanUI(QWidget):
    theme_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_changed.connect(self.apply_theme) 
        self.load_theme_colors()
        self.setup_ui()
        self.apply_theme()

        self.quick_scan_window = None
        self.custom_scan_window = None
        self.full_scan_window = None

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
        for frame in [self.frame1, self.frame2, self.frame3, self.frame4, self.barGraphFrame, self.donutGraphFrame]:
            frame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px;")
            for label in frame.findChildren(QLabel):
                label.setStyleSheet(f"color: {self.text_color};")
                label.setFont(QFont("Arial", 12, QFont.Bold))
        for button in self.buttons:
            button.setStyleSheet(f"background-color: {self.accent_color}; color: white; border-radius: 20px;")
        self.update_bar_graph()
        self.update_donut_graph()
        self.update()

    def get_scan_stats(self):
        logs = get_all_scan_log()  # Fetch scan logs from database
        
        if logs:
            last_scan = logs[-1]  # Get the most recent scan
            scan_date = last_scan.get('dt', 'No Data')
            scan_desc = last_scan.get('descp', 'No Data')
            scan_duration = last_scan.get('duration',"00:00:00")

            # Extract numerical values using regex
            files_scanned_match = re.search(r"Total Files Scanned\s*:(\d+)", scan_desc)
            threats_found_match = re.search(r"Total Anomalies\s*:(\d+)", scan_desc)

            files_scanned = int(files_scanned_match.group(1)) if files_scanned_match else 0
            threats_found = int(threats_found_match.group(1)) if threats_found_match else 0

            return scan_date, files_scanned, threats_found, scan_duration
        
        return "No Scans Yet", 0, 0, "00:00:00"  # Default values

    def setup_ui(self):
        self.setObjectName("scanPage")

        # Main Layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)
        self.mainLayout.setSpacing(20)

        # Top Frames
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(30)

        # Fetch latest scan data
        last_scan_date, files_scanned, threats_found, scan_duration = self.get_scan_stats()

        self.frame1 = self.create_frame("Files Scanned", str(files_scanned))
        self.frame2 = self.create_frame("Threats Found", str(threats_found))
        self.frame3 = self.create_frame("Last Scan", last_scan_date)
        self.frame4 = self.create_frame("Scan Duration", scan_duration)

        self.topLayout.addWidget(self.frame1)
        self.topLayout.addWidget(self.frame2)
        self.topLayout.addWidget(self.frame3)
        self.topLayout.addWidget(self.frame4)

        self.mainLayout.addLayout(self.topLayout)

        # Middle Buttons
        self.middleLayout = QHBoxLayout()
        self.middleLayout.setSpacing(30)
        quick_logo = BASE_DIR / "assets" / "images" / "quickscan.png"
        custom_logo = BASE_DIR / "assets" / "images" / "folderscan.png"
        full_logo = BASE_DIR / "assets" / "images" / "fullscan.png"

        button_info = [
            ("Quick Scan", str(quick_logo), self.open_quick_scan),
            ("Custom Scan", str(custom_logo), self.open_custom_scan),
            ("Full Scan", str(full_logo), self.open_full_scan),
        ]

        self.buttons = []
        for text, icon_path, function in button_info:
            button = self.create_button(text, icon_path, function)
            self.middleLayout.addWidget(button)
            self.buttons.append(button)

        self.mainLayout.addLayout(self.middleLayout)

        # Bottom Graphs
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setSpacing(30)

        self.barGraphFrame = self.create_frame("Scan Summary")
        self.donutGraphFrame = self.create_frame("Threat Breakdown")

        self.bottomLayout.addWidget(self.barGraphFrame, stretch=2)
        self.bottomLayout.addWidget(self.donutGraphFrame, stretch=1)
        
        self.mainLayout.addLayout(self.bottomLayout)

        # Create Graphs
        self.create_bar_graph()
        self.create_donut_graph()

        self.resizeEvent(None)

    def create_frame(self, title, value=None):
        frame = QFrame(self)
        frame.setStyleSheet(f"background-color: {self.frame_color}; border-radius: 20px;")
        layout = QVBoxLayout(frame)
        frame.setLayout(layout)
        title_label = QLabel(title, frame)
        title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.text_color};")
        layout.addWidget(title_label)

        if value is not None:
            value_label = QLabel(value, frame)
            value_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            value_label.setFont(QFont("Arial", 18, QFont.Bold))
            value_label.setStyleSheet("color: lightgreen;")
            layout.addWidget(value_label)

        return frame

    def create_button(self, text, icon_path, function=None):
        buttonWidget = QPushButton()
        buttonLayout = QVBoxLayout(buttonWidget)
        buttonWidget.setFixedSize(120, 50)
        buttonLayout.setAlignment(Qt.AlignCenter)

        # --- Button Icon ---
        iconLabel = QLabel()
        iconLabel.setPixmap(QPixmap(icon_path))
        iconLabel.setScaledContents(True)

        # Store reference to dynamically resize later
        buttonWidget.iconLabel = iconLabel

        # --- Button Text ---
        textLabel = QLabel(text)
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setObjectName("buttonText")

        # Store reference to dynamically resize later
        buttonWidget.textLabel = textLabel

        buttonLayout.addWidget(iconLabel, alignment=Qt.AlignCenter)
        buttonLayout.addWidget(textLabel, alignment=Qt.AlignCenter)

        if function:
            buttonWidget.clicked.connect(function)

        buttonWidget.setStyleSheet("background-color: {self.accent_color}; border-radius: 20px;")

        return buttonWidget

    def create_bar_graph(self):
        self.figure1, self.ax1 = plt.subplots(figsize=(4, 2), dpi=100)
        self.figure1.patch.set_alpha(0)
        self.canvas1 = FigureCanvas(self.figure1)
        self.barGraphFrame.layout().addWidget(self.canvas1)
        self.update_bar_graph()

    def update_bar_graph(self):
        logs = get_all_scan_log()  # Fetch scan logs from database

        if not logs:
            self.ax1.clear()
            self.ax1.set_facecolor("none")
            self.ax1.text(0.5, 0.5, "No Scan Data Available", fontsize=14, ha='center', va='center', color=self.text_color)
            self.canvas1.draw()
            return

        # Extract scan data
        dt_list = []  # Store scan dates (unique)
        v_list = []   # Store threat counts
        full_dates = []  # Full datetime for tooltip
        
        for log in logs:
            scan_date = log.get('dt', 'Unknown')
            scan_time = log.get('tm', '--:--')
            scan_desc = log.get('descp', '')

            match = re.search(r"Total Anomalies\s*:(\d+)", scan_desc)
            threats = int(match.group(1)) if match else 0  # Extract threat count

            dt_list.append(scan_date)
            v_list.append(threats)
            full_dates.append(f"{scan_date} {scan_time}")

        # Convert to numpy arrays
        x = np.array(dt_list[-7:])  # Show last 7 scans
        y = np.array(v_list[-7:])

        self.ax1.clear()
        self.ax1.set_facecolor("none")  # Transparent background

        self.figure1.subplots_adjust(top=0.9, bottom=0.15)
        bars = self.ax1.bar(x, y, width=0.5, color=['green' if val == 0 else self.accent_color for val in y], alpha=0.8)

        # Title & Labels
        self.ax1.set_xlabel("Scan Dates", fontsize=8, color=self.text_color)
        self.ax1.set_ylabel("Threats Found", fontsize=8, color=self.text_color)

        # Format X-Axis
        self.ax1.set_xticks([])
        self.ax1.set_yticks([])
        self.ax1.spines['bottom'].set_color(self.text_color)
        self.ax1.spines['left'].set_color(self.text_color)

        # Remove top & right spines
        self.ax1.spines['top'].set_visible(False)
        self.ax1.spines['right'].set_visible(False)

        # Cursor Hover Tooltips
        cursor = mplcursors.cursor(bars, hover=True)

        @cursor.connect("add")
        def on_hover(sel):
            index = sel.index  # Get index of hovered bar
            sel.annotation.set_text(f"Date: {full_dates[index]}\nThreats: {y[index]}")
            sel.annotation.set_fontsize(10)
            sel.annotation.get_bbox_patch().set(fc='white', alpha=0.8)
            sel.annotation.get_bbox_patch().set_edgecolor('black')

        # Update canvas
        self.canvas1.draw()

    def generate_color_variations(self, base_color: str, count: int):
        if not isinstance(base_color, str):
            raise ValueError(f"Expected base_color to be a string, got {type(base_color)} instead.")
        
        base_color = base_color.lstrip("#")  # Ensure it’s in "RRGGBB" format

        # Convert HEX to RGB
        base_rgb = tuple(int(base_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

        color_variations = []
        for i in range(count):
            shift = i * 0.1  # Adjust color shade
            new_color = (
                max(0, min(1, base_rgb[0] + shift)),
                max(0, min(1, base_rgb[1] - shift)),
                max(0, min(1, base_rgb[2] + shift))
            )
            color_variations.append('#{:02X}{:02X}{:02X}'.format(
                int(new_color[0] * 255),
                int(new_color[1] * 255),
                int(new_color[2] * 255)
            ))

        return color_variations

    def create_donut_graph(self):
        self.figure2, self.ax2 = plt.subplots(figsize=(6, 6), dpi=120)  # Bigger graph
        self.figure2.patch.set_alpha(0)  # Transparent background
        self.canvas2 = FigureCanvas(self.figure2)
        self.donutGraphFrame.layout().addWidget(self.canvas2)
        self.figure2.tight_layout()
        self.update_donut_graph()

    def update_donut_graph(self):
        virus_types = get_all_type_master()  # Fetch virus type names from DB
        labels = [vt['type_name'] for vt in virus_types]  # Extract virus names
        sizes = np.random.randint(10, 50, size=len(labels))  # Placeholder for real data

        base_color = self.accent_color  # Ensure base color is a string
        colors = self.generate_color_variations(base_color, len(labels))  # Generate color variations

        self.ax2.clear()
        # Create the Pie chart
        wedges, texts, autotexts = self.ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors,
             wedgeprops={'edgecolor': self.text_color}, 
             textprops={'fontsize': 6}) 

        # Convert Pie into Donut by adding a central white circle
        centre_circle = plt.Circle((0, 0), 0.60, fc=self.frame_color)  # Adjust size/color of center
        self.figure2.gca().add_artist(centre_circle)

        # Set label text color to white
        for text in texts + autotexts:
            text.set_color(self.text_color)

        self.canvas2.draw()

    def resizeEvent(self, event):
        if event is None:
            width, height = 1010, 620
        else:
            width, height = self.width(), self.height()

        # Top Frames Scaling
        top_frame_width = int((width - 60) / 4)
        top_frame_height = int(height * 0.15)
        for frame in [self.frame1, self.frame2, self.frame3, self.frame4]:
            frame.setFixedSize(top_frame_width, top_frame_height)

        # Middle Buttons Scaling
        button_width = int(width * 0.31)
        button_height = int(height * 0.31)
        icon_size = int(button_height * 0.25)  
        text_size = int(button_height * 0.12)  

        for button in self.buttons:
            button.setFixedSize(button_width, button_height)
            button.iconLabel.setFixedSize(icon_size, icon_size)
            button.textLabel.setStyleSheet(f"font-size: {text_size}px;")

        # Bottom Graphs Scaling
        graph_frame_height = int(height * 0.43)
        bar_frame_width = int(width * 0.65)
        donut_frame_width = width - (bar_frame_width + 50)
        self.barGraphFrame.setFixedSize(bar_frame_width, graph_frame_height)
        self.donutGraphFrame.setFixedSize(donut_frame_width, graph_frame_height)

        super().resizeEvent(event)

    def open_quick_scan(self):
        if self.quick_scan_window is None or not self.quick_scan_window.isVisible():
            self.quick_scan_window = QuickScanWindow()
            self.quick_scan_window.show()

    def open_custom_scan(self):
        if self.custom_scan_window is None or not self.custom_scan_window.isVisible():
            self.custom_scan_window = CustomScanWindow()
            self.custom_scan_window.show()

    def open_full_scan(self):
        if self.full_scan_window is None or not self.full_scan_window.isVisible():
            self.full_scan_window = FullScanWindow()
            self.full_scan_window.show()
