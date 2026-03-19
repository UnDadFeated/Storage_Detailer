import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from storage_backend import get_physical_drives, get_drive_details

# "google antigravity style grey shades theme with 1px silver lines, modern"
# Compact, fixed size, no scroll bars.

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
"""

class StorageDetailer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storage Detailer v1.0")
        self.setFixedSize(480, 260) # Compact and fixed size
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(6)
        
        self.setup_top_bar()
        self.setup_data_area()
        
        self.setStyleSheet(STYLE_SHEET)
        
        self.refresh_drives()
        
    def setup_top_bar(self):
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)
        
        self.drive_combo = QComboBox()
        self.drive_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        top_layout.addWidget(self.drive_combo, stretch=1)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        top_layout.addWidget(self.scan_btn)
        
        self.layout.addLayout(top_layout)
        
    def setup_data_area(self):
        self.data_frame = QFrame()
        self.data_frame.setObjectName("DataBox")
        
        self.data_layout = QGridLayout(self.data_frame)
        self.data_layout.setContentsMargins(8, 8, 8, 8)
        self.data_layout.setHorizontalSpacing(15)
        self.data_layout.setVerticalSpacing(4)
        
        self.layout.addWidget(self.data_frame)
        
        self.labels = {}
        
        fields = [
            ("Model:", "model", 0, 0),
            ("Vendor:", "vendor", 0, 2),
            ("Capacity:", "size", 1, 0),
            ("Transport:", "tran", 1, 2),
            ("Revision:", "rev", 2, 0),
            ("Serial:", "serial", 2, 2),
            ("Logical Sector:", "log-sec", 3, 0),
            ("Physical Sector:", "phy-sec", 3, 2),
            ("State:", "state", 4, 0),
            ("WWN:", "wwn", 4, 2),
            ("Rotational:", "rota", 5, 0),
            ("Path:", "path", 5, 2),
        ]
        
        for name, key, row, col in fields:
            lbl_title = QLabel(name)
            lbl_title.setObjectName("HeaderLabel")
            lbl_val = QLabel("N/A")
            lbl_val.setObjectName("ValueLabel")
            
            self.data_layout.addWidget(lbl_title, row, col)
            self.data_layout.addWidget(lbl_val, row, col+1)
            
            self.labels[key] = lbl_val
            
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
        self.labels["state"].setText(_get("state", "live"))
        self.labels["wwn"].setText(_get("wwn"))
        self.labels["path"].setText(_get("path"))
        
        rota = "HDD" if str(_get("rota")) == "1" else "SSD/NVMe"
        if not details.get("rota"):
            rota = "Unknown"
        elif str(_get("rota")) == "0":
            rota = "SSD/Flash"
        self.labels["rota"].setText(rota)

if __name__ == "__main__":
    app = QApplication(sys.sys.argv)
    window = StorageDetailer()
    window.show()
    sys.exit(app.exec())
