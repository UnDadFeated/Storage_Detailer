import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QFrame, QGridLayout, QProgressBar
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl, QRect
import urllib.parse
import os
from datetime import datetime
from storage_backend import get_physical_drives, get_drive_details, get_smart_info, get_web_info, format_bytes

STYLE_SHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 11px;
}
QComboBox {
    background-color: #3b3b3b;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    padding: 2px 4px;
    min-height: 20px;
}
QComboBox::drop-down {
    border-left: 1px solid #c0c0c0;
    width: 20px;
}
QPushButton {
    background-color: #3b3b3b;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    padding: 2px 10px;
    min-height: 20px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4b4b4b;
}
QPushButton:pressed {
    background-color: #5b5b5b;
}
QPushButton:disabled {
    background-color: #2b2b2b;
    color: #666666;
    border-color: #666666;
}
QFrame#DataBox {
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    background-color: #2e2e2e;
}
QLabel {
    color: #cfcfcf;
}
QLabel#ValueLabel {
    color: #ffffff;
    font-weight: bold;
    font-family: 'Noto Mono', 'JetBrains Mono', 'Consolas', monospace;
}
QLabel#HeaderLabel {
    color: #a0a0a0;
    font-size: 10px;
    text-transform: uppercase;
}
QLabel#WebInfoLabel {
    color: #88ccff;
    font-style: italic;
    background-color: #222222;
    border: 1px solid #555555;
    padding: 6px;
    border-radius: 2px;
}
QProgressBar {
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    text-align: center;
    background-color: #333333;
    color: #ffffff;
    font-family: 'Noto Mono', 'JetBrains Mono', 'Consolas', monospace;
}
QProgressBar::chunk {
    background-color: #44ff88;
}
"""

class WorkerThread(QThread):
    result_ready = pyqtSignal(dict)
    
    def __init__(self, drive_name, parent=None):
        super().__init__(parent)
        self.drive_name = drive_name
        
    def run(self):
        details = get_drive_details(self.drive_name)
        smart = get_smart_info(self.drive_name)
        
        model_val = ""
        serial_val = ""
        if details:
             model_val = details.get("model", "")
             serial_val = details.get("serial", "")
             
        web = get_web_info(model_val, serial_val)
        
        self.result_ready.emit({
            "details": details,
            "smart": smart,
            "web": web
        })

class StorageDetailer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storage Detailer v1.2.1")
        self.setFixedSize(680, 500) 
        
        self.worker = None
        self._current_model = ""
        self._current_capacity = ""
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        
        self.setup_top_bar()
        self.setup_data_area()
        self.setup_wear_bar()
        self.setup_web_area()
        
        self.setStyleSheet(STYLE_SHEET)
        
        self.refresh_drives()
        
    def setup_top_bar(self):
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        
        self.drive_combo = QComboBox()
        self.drive_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.drive_combo.setFixedHeight(24)
        top_layout.addWidget(self.drive_combo, stretch=1)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        self.scan_btn.setFixedSize(100, 24)
        top_layout.addWidget(self.scan_btn)

        self.btn_camera = QPushButton("Snapshot")
        self.btn_camera.setToolTip("Capture Snapshot for Export")
        self.btn_camera.setFixedSize(70, 24)
        self.btn_camera.clicked.connect(self.on_camera_clicked)
        top_layout.addWidget(self.btn_camera)
        
        self.main_layout.addLayout(top_layout)
        
    def setup_data_area(self):
        self.data_frame = QFrame()
        self.data_frame.setObjectName("DataBox")
        
        self.data_layout = QGridLayout(self.data_frame)
        self.data_layout.setContentsMargins(15, 15, 15, 15)
        self.data_layout.setHorizontalSpacing(20)
        self.data_layout.setVerticalSpacing(8)
        
        self.data_layout.setColumnMinimumWidth(0, 90)
        self.data_layout.setColumnMinimumWidth(2, 90)
        self.data_layout.setColumnMinimumWidth(4, 90)
        
        self.main_layout.addWidget(self.data_frame)
        
        self.labels = {}
        
        fields = [
            ("Model:", "model", 0, 0),
            ("Vendor:", "vendor", 1, 0),
            ("Firmware Rev:", "rev", 2, 0),
            ("Serial Num:", "serial", 3, 0),
            ("WWN:", "wwn", 4, 0),
            ("Form Factor:", "form_factor", 5, 0),
            ("Transport:", "tran", 6, 0),
            ("Path:", "path", 7, 0),
            ("Capacity:", "size", 8, 0),
            ("Logical Sec:", "log-sec", 9, 0),
            ("Physical Sec:", "phy-sec", 10, 0),

            ("Type:", "rota", 0, 2),
            ("RPM:", "rpm", 1, 2),
            ("Queue Size:", "rq-size", 2, 2),
            ("Scheduler:", "sched", 3, 2),
            ("Min I/O:", "min-io", 4, 2),
            ("Opt I/O:", "opt-io", 5, 2),
            ("TRIM Granular:", "disc-gran", 6, 2),
            ("TRIM Max:", "disc-max", 7, 2),
            ("TRIM Zero:", "disc-zero", 8, 2),
            ("ATA Standard:", "ata_std", 9, 2),
            ("Protocol:", "protocol", 10, 2),
            
            ("SMART Status:", "smart_status", 0, 4),
            ("Temperature:", "smart_temp", 1, 4),
            ("Power On Hrs:", "smart_poh", 2, 4),
            ("Power Cycles:", "pwr_cycles", 3, 4),
            ("TBW (Writes):", "smart_tbw", 4, 4),
            ("Wear Lvl Count:", "wear_leveling", 5, 4),
            ("NVMe % Used:", "pct_used", 6, 4),
            ("NVMe % Spare:", "avail_spare", 7, 4),
            ("Reallocated:", "reallocated", 8, 4),
            ("Pending Secs:", "pending", 9, 4),
            ("Uncorrectable:", "uncorrectable", 10, 4)
        ]
        
        for name, key, row, col in fields:
            lbl_title = QLabel(name)
            lbl_title.setObjectName("HeaderLabel")
            lbl_val = QLabel("N/A")
            lbl_val.setObjectName("ValueLabel")
            
            self.data_layout.addWidget(lbl_title, row, col)
            self.data_layout.addWidget(lbl_val, row, col+1)
            self.labels[key] = lbl_val

    def setup_wear_bar(self):
        wear_layout = QHBoxLayout()
        wear_layout.setContentsMargins(5, 5, 5, 5)
        lbl_wear_title = QLabel("Drive Wear:")
        lbl_wear_title.setObjectName("HeaderLabel")
        wear_layout.addWidget(lbl_wear_title)
        
        self.wear_bar = QProgressBar()
        self.wear_bar.setRange(0, 100)
        self.wear_bar.setValue(0)
        self.wear_bar.setFixedHeight(14)
        self.wear_bar.setTextVisible(True)
        self.wear_bar.setFormat("Wear: %p%")
        wear_layout.addWidget(self.wear_bar, stretch=1)
        self.main_layout.addLayout(wear_layout)
            
    def setup_web_area(self):
        web_top_layout = QHBoxLayout()
        web_top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_web_title = QLabel("Web Search Intel:")
        self.lbl_web_title.setObjectName("HeaderLabel")
        web_top_layout.addWidget(self.lbl_web_title)
        
        self.btn_amazon = QPushButton("Amazon")
        self.btn_amazon.setToolTip("Buy on Amazon")
        self.btn_amazon.clicked.connect(self.on_amazon_clicked)
        self.btn_amazon.setEnabled(False)
        self.btn_amazon.setFixedHeight(24)
        self.btn_amazon.setMinimumWidth(60)
        web_top_layout.addWidget(self.btn_amazon)
        
        self.main_layout.addLayout(web_top_layout)
        
        self.web_label = QLabel("Waiting for scan...")
        self.web_label.setObjectName("WebInfoLabel")
        self.web_label.setWordWrap(True)
        self.web_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Bounded height to ensure fluid fit within windows bounds securely
        self.web_label.setMinimumHeight(40)
        self.web_label.setMaximumHeight(58)
        self.main_layout.addWidget(self.web_label)

    def refresh_drives(self):
        self.drive_combo.clear()
        drives = get_physical_drives()
        for d in drives:
            name = d.get("name", "Unknown")
            model = d.get("model", "")
            size = format_bytes(d.get("size"))
            tran = d.get("tran", "")
            
            display_text = f"/dev/{name} - {model} ({size}) [{tran}]"
            self.drive_combo.addItem(display_text, userData=name)
            
        if self.drive_combo.count() > 0:
            self.on_scan_clicked()
            
    def on_camera_clicked(self):
        pictures_dir = os.path.expanduser("~/Pictures")
        screenshots_dir = os.path.join(pictures_dir, "Screenshots")
        if not os.path.exists(screenshots_dir):
            if os.path.exists(pictures_dir):
                screenshots_dir = pictures_dir
            else:
                screenshots_dir = os.path.expanduser("~")
        os.makedirs(screenshots_dir, exist_ok=True)
                
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        model_name = self._current_model.replace(" ", "_") if self._current_model else "Drive"
        filename = f"StorageDetailer_{model_name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        crop_h = self.wear_bar.geometry().bottom() + 15
        rect = self.central_widget.rect()
        rect.setHeight(min(crop_h, rect.height()))
        
        pixmap = self.central_widget.grab(rect)
        pixmap.save(filepath, "PNG")
        
        self.web_label.setText(f"Snapshot securely saved to:\n{filepath}")

    def on_scan_clicked(self):
        current_data = self.drive_combo.currentData()
        if not current_data:
            return
            
        if self.worker and self.worker.isRunning():
            return
            
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")
        self.btn_amazon.setEnabled(False)
        self.web_label.setText("Scanning the web and polling SMART data...")
        
        self.worker = WorkerThread(current_data)
        self.worker.result_ready.connect(self.on_worker_finished, Qt.ConnectionType.UniqueConnection)
        self.worker.start()

    def on_worker_finished(self, results):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan")
        self.btn_amazon.setEnabled(True)
        
        details = results["details"]
        smart = results["smart"]
        web = results["web"]
        
        self.web_label.setText(web)
        
        if details:
            self.update_ui_with_details(details)
        
        if smart:
            self.update_ui_with_smart(smart)
            
    def on_amazon_clicked(self):
        if self._current_model:
            search_term = self._current_model.strip().strip('\x00')
            if getattr(self, "_current_capacity", ""):
                search_term += f" {self._current_capacity}"
            query = urllib.parse.quote_plus(search_term)
            url = f"https://www.amazon.com/s?k={query}&tag=mesarastarr-20"
            QDesktopServices.openUrl(QUrl(url))
            
    def update_ui_with_details(self, details):
        def _get(key, default="N/A"):
            val = details.get(key)
            return str(val).strip() if val else default
            
        model_str = _get("model")
        self.labels["model"].setText(model_str)
        self._current_model = model_str
        
        try:
            b = float(details.get("size", 0))
            gb = b / 1_000_000_000
            if gb >= 1000:
                self._current_capacity = f"{round(gb/1000)}TB"
            elif gb >= 1:
                self._current_capacity = f"{round(gb)}GB"
            else:
                self._current_capacity = ""
        except (ValueError, TypeError):
            self._current_capacity = ""
        
        self.labels["vendor"].setText(_get("vendor"))
        self.labels["size"].setText(format_bytes(details.get("size")))
        self.labels["tran"].setText(str(_get("tran")).upper())
        self.labels["rev"].setText(_get("rev"))
        self.labels["serial"].setText(_get("serial"))
        
        self.labels["log-sec"].setText(format_bytes(details.get("log-sec")))
        self.labels["phy-sec"].setText(format_bytes(details.get("phy-sec")))
        
        self.labels["wwn"].setText(_get("wwn"))
        self.labels["path"].setText(_get("path"))
        
        self.labels["sched"].setText(_get("sched").upper())
        self.labels["rq-size"].setText(_get("rq-size"))
        
        self.labels["min-io"].setText(format_bytes(details.get("min-io")))
        self.labels["opt-io"].setText(format_bytes(details.get("opt-io")))
        
        trim_zero = "Yes" if str(_get("disc-zero")) == "True" else "No"
        self.labels["disc-gran"].setText(format_bytes(details.get("disc-gran", 0)))
        self.labels["disc-max"].setText(format_bytes(details.get("disc-max", 0)))
        self.labels["disc-zero"].setText(trim_zero)
        
        rota_val = str(_get("rota", ""))
        rota = "HDD" if rota_val == "1" else ("SSD/Flash" if rota_val == "0" else "Unknown")
        self.labels["rota"].setText(rota)

    def update_ui_with_smart(self, smart):
        status = smart.get("status", "Unknown")
        self.labels["smart_status"].setText(status)
        if status == "PASSED":
            self.labels["smart_status"].setStyleSheet("color: #44ff88;")
        elif status == "FAILED":
            self.labels["smart_status"].setStyleSheet("color: #ff4444;")
        else:
            self.labels["smart_status"].setStyleSheet("color: #ffaa44;")
            
        self.labels["smart_temp"].setText(smart.get("temp", "N/A"))
        self.labels["smart_poh"].setText(smart.get("power_on_hours", "N/A"))
        self.labels["smart_tbw"].setText(smart.get("tbw", "N/A"))
        self.labels["pwr_cycles"].setText(smart.get("pwr_cycles", "N/A"))
        self.labels["reallocated"].setText(smart.get("reallocated", "N/A"))
        self.labels["pending"].setText(smart.get("pending", "N/A"))
        self.labels["uncorrectable"].setText(smart.get("uncorrectable", "N/A"))
        self.labels["wear_leveling"].setText(smart.get("wear_leveling", "N/A"))
        self.labels["pct_used"].setText(smart.get("pct_used", "N/A"))
        self.labels["avail_spare"].setText(smart.get("avail_spare", "N/A"))
        self.labels["form_factor"].setText(smart.get("form_factor", "N/A"))
        self.labels["rpm"].setText(smart.get("rpm", "N/A"))
        self.labels["ata_std"].setText(smart.get("ata_std", "N/A"))
        self.labels["protocol"].setText(smart.get("protocol", "N/A"))
        
        # Wear bar logic (NVMe % used usually)
        pct = smart.get("pct_used", "N/A")
        if pct != "N/A":
            try:
                val = max(0, min(100, int(float(pct.replace("%","").strip()))))
                self.wear_bar.setValue(val)
                # Color code inverse to health (high pct used is bad)
                if val < 70:
                    self.wear_bar.setStyleSheet("QProgressBar::chunk { background-color: #44ff88; }")
                elif val < 90:
                    self.wear_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffaa44; }")
                else:
                    self.wear_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            except (ValueError, TypeError):
                self.wear_bar.setValue(0)
        else:
            self.wear_bar.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StorageDetailer()
    window.show()
    sys.exit(app.exec())
