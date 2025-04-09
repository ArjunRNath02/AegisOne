# 🛡️ AegisOne: AI-driven Cybersecurity Threat Detection and Mitigation System

AegisOne is a robust AI-powered cybersecurity solution designed to detect, analyze, and mitigate potential threats in real time. It leverages machine learning and intelligent automation to safeguard systems from malware, unauthorized intrusions, and system vulnerabilities, offering users a comprehensive security and performance toolkit with a modern GUI.

## 🚀 Features

### 🔍 Threat Detection

- AI-powered malware detection using Random Forest Classifier
- Static feature extraction from files
- Directory scanning with real-time analysis
- Customizable scan options
  
### 🧠 Machine Learning Integration

- Classifies files as malicious or benign
- Extensible to support new models and datasets

### 📊 GUI Dashboard (PySide6)

- Tab-based interface for Scan, Home, Performance, and Update
- Real-time scan statistics
- Donut and bar charts for threat visualization (Matplotlib)
- Theme customization (Light/Dark Mode)
- System health reporting and scan history logs

### 🧰 System Utilities (PC Optimization)

- One-click system cleanup (temp/cache/registry)
- Monitor System Resources
  
---

## 🏗️ Tech Stack

- **Programming Language**: Python
- **GUI Framework**: PySide6 (CustomWidgets**)
- **ML Library**: Scikit-learn
- **Data Visualization**: Matplotlib
- **Packet/File Analysis**: Scapy, Pefile, OS, Custom Feature Extractors
- **System Operations**: psutil, subprocess, shutil

---

## 📦 Installation

### Requirements

- Python 3.8 or higher
- OS: Windows 10/11

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```plaintext
AegisOne/
├── main.py                            # Entry point for the application
└── src/
    ├── function.py                    # Common utility functions
    ├── ui_interface.py               # PySide6 GUI interface and layout manager

    ├── dataset/                      # Datasets used for training/testing
    │   └── av.csv                    # Antivirus dataset with 54 static features

    ├── db/                           # Database storage
    │   └── antivirus.sqlite          # SQLite database for scan history & quarantine

    ├── extensions/                   # Core logic and backend modules
    │   ├── db_handler.py             # Handles SQLite operations
    │   ├── ml_model.py               # Machine learning model & prediction
    │   ├── scan_function.py          # File scanning and logging
    │   └── file_manip.py             # File operations and feature extraction

    ├── frames/                       # GUI navigation frames
    │   ├── home.py                   # Home/Dashboard screen
    │   ├── performance.py            # PC optimization & performance tools
    │   ├── scan.py                   # Scan interface and results
    │   └── update.py                 # Updates & version checker

    └── windows/                      # Functional popup windows and tools
        ├── add_malwaretypes.py      # Add custom malware signatures
        ├── custom_scan.py           # Custom file/folder scan
        ├── full_scan.py             # Full system scan
        ├── quick_scan.py            # Quick scan (select folders)
        ├── usb_scan.py              # USB device scan
        ├── scan_log.py              # Scan history and log viewer
        └── system_healthreport.py   # System health and status report
```

---

**Special Credits to KhamisiKibet for 24-Modern_Desktop-GUI (CustomWidgets) for inspiration and template.
<https://github.com/KhamisiKibet/24-Modern-Desktop-GUI>

---
