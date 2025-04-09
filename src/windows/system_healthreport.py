from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QFileDialog, QApplication
)
from PySide6.QtCore import Qt
import sys
import psutil
import platform
import subprocess
import time

class SystemHealthReport(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("System Health Check Report")
        self.setGeometry(300, 200, 900, 600)
        self.setFixedSize(900, 600)

        self.parent_window = parent
        if self.parent_window:
            self.parent_window.destroyed.connect(self.close)


        # --- Central Widget ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- Main Layout ---
        self.mainLayout = QVBoxLayout(self.central_widget)
        self.mainLayout.setSpacing(15)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)

        # --- Title Label ---
        self.title_label = QLabel("System Health Check Report")
        self.title_label.setObjectName("homeLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.title_label)

        # --- System Info Frame ---
        self.system_info_frame = self.create_frame("System Information")
        self.mainLayout.addWidget(self.system_info_frame)

        # --- CPU, RAM, Network Stats Frame ---
        self.stats_layout = QHBoxLayout()
        self.cpu_frame = self.create_frame("CPU Usage")
        self.ram_frame = self.create_frame("RAM & Swap")
        self.network_frame = self.create_frame("Network & Disk I/O")
        self.stats_layout.addWidget(self.cpu_frame)
        self.stats_layout.addWidget(self.ram_frame)
        self.stats_layout.addWidget(self.network_frame)
        self.mainLayout.addLayout(self.stats_layout)

        # --- Storage and Battery Layout ---
        self.storage_layout = QHBoxLayout()
        self.disk_frame = self.create_frame("Storage Information")
        self.battery_frame = self.create_frame("Battery & Uptime")
        self.storage_layout.addWidget(self.disk_frame)
        self.storage_layout.addWidget(self.battery_frame)
        self.mainLayout.addLayout(self.storage_layout)

        # --- Print Report Button ---
        self.print_button = QPushButton("Print")
        self.print_button.setStyleSheet("background-color: #27ae60; color: white; font-size: 14px;")
        self.print_button.clicked.connect(self.print_report)
        self.mainLayout.addWidget(self.print_button, alignment=Qt.AlignRight)

        # --- Get System Data ---
        self.populate_data()

    def create_frame(self, title=""):
        frame = QFrame()
        frame.setStyleSheet("background-color: #333; border-radius: 20px; color: white;")
        frame.setFixedHeight(130)

        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        content_label = QLabel("")
        content_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(content_label)

        frame.setLayout(layout)
        frame.content_label = content_label
        return frame

    def get_system_info(self):
        os_version = platform.platform()
        python_version = platform.python_version()

        try:
            git_version = subprocess.check_output(['git', '--version']).decode().strip()
        except subprocess.CalledProcessError:
            git_version = "Git not installed"

        try:
            java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT).decode().splitlines()[0]
        except subprocess.CalledProcessError:
            java_version = "Java not installed"

        return {
            "Operating System": os_version,
            "Python Version": python_version,
            "Git Version": git_version,
            "Java Version": java_version,
        }

    def get_hardware_stats(self):
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_load = cpu_percent

        # RAM & Swap
        memory = psutil.virtual_memory()
        total_ram = memory.total / (1024 ** 3)
        used_ram = memory.used / (1024 ** 3)
        ram_percent = memory.percent
        swap = psutil.swap_memory()
        swap_total = swap.total / (1024 ** 3)
        swap_used = swap.used / (1024 ** 3)
        swap_percent = swap.percent

        # Network
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent / (1024 ** 2)
        bytes_recv = net_io.bytes_recv / (1024 ** 2)

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        read_bytes = disk_io.read_bytes / (1024 ** 3)
        write_bytes = disk_io.write_bytes / (1024 ** 3)

        # Battery & Uptime
        battery = psutil.sensors_battery()
        uptime_seconds = time.time() - psutil.boot_time()
        uptime = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

        if battery:
            battery_percent = battery.percent
            charging_status = "Charging" if battery.power_plugged else "Discharging"
        else:
            battery_percent = "N/A"
            charging_status = "N/A"

        return {
            "CPU Usage": f"{cpu_percent}%",
            "CPU Cores": f"{cpu_count}",
            "CPU Frequency": f"{round(cpu_freq.current / 1000, 2)} GHz",
            "CPU Load": f"{cpu_load}%",

            "RAM Total": f"{total_ram:.2f} GB",
            "RAM Used": f"{used_ram:.2f} GB",
            "RAM Usage": f"{ram_percent}%",
            "Swap Total": f"{swap_total:.2f} GB",
            "Swap Used": f"{swap_used:.2f} GB",
            "Swap Usage": f"{swap_percent}%",

            "Disk Read": f"{read_bytes:.2f} GB",
            "Disk Write": f"{write_bytes:.2f} GB",
            "Network Sent": f"{bytes_sent:.2f} MB",
            "Network Received": f"{bytes_recv:.2f} MB",

            "Battery": f"{battery_percent}%, {charging_status}",
            "Uptime": uptime,
        }

    def get_storage_info(self):
        partitions = psutil.disk_partitions()
        storage_details = []
        for partition in partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            storage_details.append(
                f"{partition.device} ({partition.fstype}) - {usage.total / (1024**3):.1f}GB "
                f"Used: {usage.used / (1024**3):.1f}GB Free: {usage.free / (1024**3):.1f}GB "
                f"Usage: {usage.percent}%"
            )
        return "\n".join(storage_details)

    def populate_data(self):
        sys_info = self.get_system_info()
        stats = self.get_hardware_stats()

        self.system_info_frame.content_label.setText("\n".join(f"{k}: {v}" for k, v in sys_info.items()))
        self.cpu_frame.content_label.setText("\n".join(f"{k}: {v}" for k, v in stats.items() if "CPU" in k))
        self.ram_frame.content_label.setText("\n".join(f"{k}: {v}" for k, v in stats.items() if "RAM" in k or "Swap" in k))
        self.network_frame.content_label.setText(f"Sent: {stats['Network Sent']}\nReceived: {stats['Network Received']}\nDisk Read: {stats['Disk Read']}\nDisk Write: {stats['Disk Write']}")
        self.disk_frame.content_label.setText(self.get_storage_info())
        self.battery_frame.content_label.setText(f"{stats['Battery']}\nUptime: {stats['Uptime']}")

    def print_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Report", "SystemHealthReport.txt", "Text Files (*.txt)")
        if filename:
            with open(filename, "w") as file:
                report_content = [
                    "==== System Health Report ====\n",
                    "System Information:\n" + self.system_info_frame.content_label.text(),
                    "\nCPU Details:\n" + self.cpu_frame.content_label.text(),
                    "\nRAM & Swap Details:\n" + self.ram_frame.content_label.text(),
                    "\nNetwork & Disk I/O:\n" + self.network_frame.content_label.text(),
                    "\nStorage Information:\n" + self.disk_frame.content_label.text(),
                    "\nBattery & Uptime:\n" + self.battery_frame.content_label.text(),
                ]
                file.write("\n\n".join(report_content))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemHealthReport()
    window.show()
    sys.exit(app.exec())
