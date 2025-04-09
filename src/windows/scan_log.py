import sys
import psutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QListWidget, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.extensions.db_handler import get_scan_log, get_all_scan_log


class ScanLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Logs")
        self.setGeometry(100, 100, 750, 550)
        self.setStyleSheet("background-color: #333; color: white; border-radius: 10px;")

        # Main Layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)
        self.mainLayout.setSpacing(15)

        # Title Label
        title_label = QLabel("SCAN LOGS", self)
        title_label.setFont(QFont("Verdana", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(title_label)

        # Scan Log List Frame
        self.scanListFrame = QFrame(self)
        self.scanListFrame.setStyleSheet("background-color: #444; border-radius: 10px; padding: 10px;")
        self.scanListLayout = QVBoxLayout(self.scanListFrame)

        self.file_listbox = QListWidget(self.scanListFrame)
        self.file_listbox.setStyleSheet("background-color: #222; color: white; border-radius: 5px; padding: 5px;")
        self.scanListLayout.addWidget(self.file_listbox)

        self.mainLayout.addWidget(self.scanListFrame)

        # Buttons Frame
        self.buttonFrame = QFrame(self)
        self.buttonLayout = QHBoxLayout(self.buttonFrame)
        self.buttonLayout.setSpacing(10)

        self.detailsButton = self.create_button("Details", self.open_scan_details)
        self.refreshButton = self.create_button("Refresh", self.load_scan_log)
        self.closeButton = self.create_button("Close", self.close)

        self.buttonLayout.addWidget(self.detailsButton)
        self.buttonLayout.addWidget(self.refreshButton)
        self.buttonLayout.addWidget(self.closeButton)

        self.buttonFrame.setLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.buttonFrame)

        # Load scan logs
        self.load_scan_log()

    def create_button(self, text, function):
        """Helper function to create styled buttons."""
        button = QPushButton(text, self)
        button.setStyleSheet("background-color: #555; color: white; border-radius: 10px; padding: 10px; font-size: 14px;")
        button.clicked.connect(function)
        return button

    def load_scan_log(self):
        """Fetch scan logs from database and display in listbox."""
        self.file_listbox.clear()
        logs = get_scan_log()

        if not logs:
            self.file_listbox.addItem("No scan logs available")
            return

        for log in logs:
            log_text = f"ID: {log.get('scan_id', 'N/A')} | {log.get('date', 'Unknown')} | {log.get('summary', 'No Summary')}"
            self.file_listbox.addItem(log_text)

    def open_scan_details(self):
        """Open details of the selected scan log."""
        try:
            selected_item = self.file_listbox.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "No Selection", "Please select a scan log first!")
                return

            # Extract selected scan ID
            selected_text = selected_item.text()
            scan_id = selected_text.split("ID: ")[1].split(" | ")[0]

            # Fetch all scan logs from database
            all_logs = get_all_scan_log()
            selected_log = next((log for log in all_logs if str(log["id"]) == scan_id), None)

            if not selected_log:
                QMessageBox.information(self, "No Details", f"No details found for Scan ID {scan_id}.")
                return

            # Create a new window for scan details
            details_window = QDialog(self)
            details_window.setWindowTitle("Scan Details")
            details_window.setGeometry(200, 200, 500, 400)
            details_window.setStyleSheet("background-color: #333; color: white; border-radius: 10px;")

            details_layout = QVBoxLayout(details_window)

            label = QLabel(f"Scan Details - ID: {scan_id}", details_window)
            label.setFont(QFont("Verdana", 18, QFont.Bold))
            label.setAlignment(Qt.AlignCenter)
            details_layout.addWidget(label)

            details_text = (
                f"Title: {selected_log.get('title', 'N/A')}\n"
                f"Description: {selected_log.get('descp', 'No Description')}\n"
                f"Date: {selected_log.get('dt', 'Unknown')} {selected_log.get('tm', 'Unknown')}\n"
                f"Status: {selected_log.get('status', 'N/A')}\n"
                f"Duration: {selected_log.get('duration', 'N/A')}\n"
                f"{'-'*30}"
            )

            text_box = QTextEdit(details_window)
            text_box.setText(details_text)
            text_box.setStyleSheet("background-color: #222; color: white; border-radius: 5px; padding: 5px; font-size: 14px;")
            text_box.setReadOnly(True)
            details_layout.addWidget(text_box)

            close_btn = self.create_button("Close", details_window.close)
            details_layout.addWidget(close_btn)

            details_window.setLayout(details_layout)
            details_window.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


def display_scan_logs(parent_window):
    """Function to open the ScanLogDialog."""
    scan_log_window = ScanLogDialog(parent_window)
    scan_log_window.exec_()
