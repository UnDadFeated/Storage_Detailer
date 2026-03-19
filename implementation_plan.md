# Implementation Plan

<!-- ANCHOR -->
## 2026-03-19 12:38 PM
- Stack: Python 3 with PySide6 (or PyQt6).
- UI: Minimalist modern "google antigravity" theme, grayscale shades, 1px silver lines.
- Fixed window size, no scrollbars, compact spacing.
- Dropdown (QComboBox) for selecting physical drives.
- Scan Button (QPushButton) to trigger drive analysis.
- Data presentation: form layout or tabular view using tight labels.
- Backend data: `lsblk --json -d` for block devices, `smartctl` or `udevadm` for more info if available, `psutil` for partitions and usage.
