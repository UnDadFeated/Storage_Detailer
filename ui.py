import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from storage_backend import get_physical_drives, get_drive_details, get_smart_info, get_web_info

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
"""

class StorageDetailer(QMainWindow):
    web_intel_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storage Detailer v1.0")
        self.setFixedSize(620, 430) 
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        
        self.setup_top_bar()
        self.setup_data_area()
        self.setup_web_area()
        
        self.setStyleSheet(STYLE_SHEET)
        
        self.web_intel_ready.connect(self.on_web_intel_ready)
        
        self.refresh_drives()
        
    def setup_top_bar(self):
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        
        self.drive_combo = QComboBox()
        self.drive_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        top_layout.addWidget(self.drive_combo, stretch=1)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        self.scan_btn.setFixedWidth(80)
        top_layout.addWidget(self.scan_btn)
        
        self.layout.addLayout(top_layout)
        
    def setup_data_area(self):
        self.data_frame = QFrame()
        self.data_frame.setObjectName("DataBox")
        
        self.data_layout = QGridLayout(self.data_frame)
        self.data_layout.setContentsMargins(15, 15, 15, 15)
        self.data_layout.setHorizontalSpacing(25)
        self.data_layout.setVerticalSpacing(8)
        
        self.layout.addWidget(self.data_frame)
        
        self.labels = {}
        
        fields = [
            # Left Columns (Hardware/Identity)
            ("Model:", "model", 0, 0),
            ("Vendor:", "vendor", 1, 0),
            ("Firmware Rev:", "rev", 2, 0),
            ("Serial Num:", "serial", 3, 0),
            ("WWN:", "wwn", 4, 0),
            ("Capacity:", "size", 5, 0),
            ("Transport:", "tran", 6, 0),
            ("Type:", "rota", 7, 0),
            ("Scheduler:", "sched", 8, 0),
            ("Path:", "path", 9, 0),
            ("Queue Size:", "rq-size", 10, 0),

            # Right Columns (Telemetry/Technical/SMART)
            ("SMART Status:", "smart_status", 0, 2),
            ("Temperature:", "smart_temp", 1, 2),
            ("Power On Hrs:", "smart_poh", 2, 2),
            ("Lifetime Writes:", "smart_tbw", 3, 2),
            ("Logical Sec:", "log-sec", 4, 2),
            ("Physical Sec:", "phy-sec", 5, 2),
            ("Min I/O:", "min-io", 6, 2),
            ("Opt I/O:", "opt-io", 7, 2),
            ("TRIM Granular:", "disc-gran", 8, 2),
            ("TRIM Max:", "disc-max", 9, 2),
            ("TRIM Zero:", "disc-zero", 10, 2),
        ]
        
        for name, key, row, col in fields:
            lbl_title = QLabel(name)
            lbl_title.setObjectName("HeaderLabel")
            lbl_val = QLabel("N/A")
            lbl_val.setObjectName("ValueLabel")
            
            self.data_layout.addWidget(lbl_title, row, col)
            self.data_layout.addWidget(lbl_val, row, col+1)
            
            self.labels[key] = lbl_val
            
    def setup_web_area(self):
        lbl_title = QLabel("Web Search Intel:")
        lbl_title.setObjectName("HeaderLabel")
        self.layout.addWidget(lbl_title)
        
        self.web_label = QLabel("Waiting for scan...")
        self.web_label.setObjectName("WebInfoLabel")
        self.web_label.setWordWrap(True)
        self.web_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Fixed height to prevent resizing
        self.web_label.setFixedHeight(45)
        self.layout.addWidget(self.web_label)

    def refresh_drives(self):
        self.drive_combo.clear()
        drives = get_physical_drives()
        for d in drives:
            name = d.get("name", "Unknown")
            model = d.get("model", "")
            size = d.get("size", "")
            tran = d.get("tran", "")
            
            display_text = f"/dev/{name} - {model} ({size}) [{tran}]"
            self.drive_combo.addItem(display_text, userData=name)
            
        if self.drive_combo.count() > 0:
            self.on_scan_clicked()
            
    def on_scan_clicked(self):
        current_data = self.drive_combo.currentData()
        if not current_data:
            return
            
        details = get_drive_details(current_data)
        if details:
            self.update_ui_with_details(details)
            
        # Grab SMART info
        smart = get_smart_info(current_data)
        self.labels["smart_status"].setText(smart["status"])
        self.labels["smart_temp"].setText(smart["temp"])
        self.labels["smart_poh"].setText(smart["power_on_hours"])
        self.labels["smart_tbw"].setText(smart["tbw"])
        
        # Web Intel
        self.web_label.setText("Scanning the web for drive intelligence...")
        model = self.labels["model"].text()
        serial = self.labels["serial"].text()
        threading.Thread(target=self.do_web_scan, args=(model, serial), daemon=True).start()
        
    def do_web_scan(self, model, serial):
        intel = get_web_info(model, serial)
        self.web_intel_ready.emit(intel)

    def on_web_intel_ready(self, intel):
        self.web_label.setText(intel)
            
    def update_ui_with_details(self, details):
        def _get(key, default="N/A"):
            val = details.get(key)
            return str(val).strip() if val else default
            
        self.labels["model"].setText(_get("model"))
        self.labels["vendor"].setText(_get("vendor"))
        self.labels["size"].setText(_get("size"))
        self.labels["tran"].setText(str(_get("tran")).upper())
        self.labels["rev"].setText(_get("rev"))
        self.labels["serial"].setText(_get("serial"))
        self.labels["log-sec"].setText(_get("log-sec") + " B")
        self.labels["phy-sec"].setText(_get("phy-sec") + " B")
        self.labels["wwn"].setText(_get("wwn"))
        self.labels["path"].setText(_get("path"))
        
        self.labels["sched"].setText(_get("sched").upper())
        self.labels["rq-size"].setText(_get("rq-size"))
        self.labels["min-io"].setText(_get("min-io") + " B")
        self.labels["opt-io"].setText(_get("opt-io") + " B")
        
        trim_zero = "Yes" if _get("disc-zero") == "True" else "No"
        self.labels["disc-gran"].setText(_get("disc-gran", "0B"))
        self.labels["disc-max"].setText(_get("disc-max", "0B"))
        self.labels["disc-zero"].setText(trim_zero)
        
        rota = "HDD" if str(_get("rota")) == "1" else "SSD/NVMe"
        if not details.get("rota") and str(_get("rota")) != "0":
            rota = "Unknown"
        elif str(_get("rota")) == "0":
            rota = "SSD/Flash"
        self.labels["rota"].setText(rota)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StorageDetailer()
    window.show()
    sys.exit(app.exec())
