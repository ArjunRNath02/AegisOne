from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QProgressBar, QFileDialog, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
import sys
from src.extensions.scan_function import scan_directory
from src.extensions.file_manip import quarantine

class ScanThread(QThread):
    """ Thread for running the scan in the background """
    update_progress = Signal(int)
    scan_complete = Signal(dict)

    def __init__(self, scan_type, directory):
        super().__init__()
        self.scan_type = scan_type
        self.directory = directory

    def run(self):
        self.update_progress.emit(20)  # Start progress
        result = scan_directory(self.scan_type, self.directory)
        self.update_progress.emit(100)  # End progress
        self.scan_complete.emit(result)


class CustomScanWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Custom Scan")
        self.setGeometry(300, 200, 750, 550)
        self.setFixedSize(750, 550)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Title Label
        self.title_label = QLabel("Custom Scan - AegisOne", self)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Scan Result Output Box
        self.scan_output = QTextEdit(self)
        self.scan_output.setReadOnly(True)
        self.scan_output.setStyleSheet("background-color: #000000; padding: 8px; border-radius: 5px;")

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Buttons
        self.select_dir_btn = QPushButton("Select Directory", self)
        self.select_dir_btn.setStyleSheet("background-color: #2980b9; color: white; font-size: 14px; padding: 8px;")
        self.select_dir_btn.clicked.connect(self.select_directory)

        self.start_scan_btn = QPushButton("Start Scan", self)
        self.start_scan_btn.setStyleSheet("background-color: #27ae60; color: white; font-size: 14px; padding: 8px;")
        self.start_scan_btn.clicked.connect(self.start_scan)
        self.start_scan_btn.setEnabled(False)  # Disable until directory is selected

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setStyleSheet("background-color: #e74c3c; color: white; font-size: 14px; padding: 8px;")
        self.close_btn.clicked.connect(self.close)

        # Add Widgets to Layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.scan_output)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.select_dir_btn)
        self.layout.addWidget(self.start_scan_btn)
        self.layout.addWidget(self.close_btn)

        self.directory = None  # Placeholder for selected directory

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if dir_path:
            self.directory = dir_path
            self.scan_output.append(f"Selected Directory: {self.directory}")
            self.start_scan_btn.setEnabled(True)  # Enable Start Scan button

    def start_scan(self):
        if not self.directory:
            self.scan_output.append("⚠ Please select a directory first!")
            return

        self.scan_output.clear()
        self.progress_bar.setValue(0)
        self.scan_thread = ScanThread("Custom Scan", self.directory)
        self.scan_thread.update_progress.connect(self.progress_bar.setValue)
        self.scan_thread.scan_complete.connect(self.display_results)
        self.scan_thread.start()

    def display_results(self, result_data):
        msg = result_data["msg"]
        virus_files = result_data["file_list"]

        self.scan_output.setPlainText(msg)

        for file_info in virus_files:
            file_path = file_info["file"]
            response = QMessageBox.question(
                self,
                "ML Alert - Possible Threat Detected",
                f"Do you want to quarantine the following file?\n{file_path}",
                QMessageBox.Yes | QMessageBox.No
            )

            if response == QMessageBox.Yes:
                quarantine(file_path)
                self.scan_output.append(f"\n✅ {file_path} -- ML Alert Quarantined by user")
            else:
                self.scan_output.append(f"\n❌ {file_path} -- ML Alert Ignored by user")


# Run standalone for testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomScanWindow()
    window.show()
    sys.exit(app.exec())
