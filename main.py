import sys
from PyQt6.QtWidgets import QApplication
from ui import StorageDetailer

def main():
    app = QApplication(sys.argv)
    window = StorageDetailer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
