# Conversation Log

<!-- ANCHOR -->
## 2026-03-19 12:56 PM
- Added Amazon Price check (w/ affiliate tag `mesarastarr-20`) and PCPartPicker price check buttons natively into the Web Intel UI pane to enable lightning-fast market research directly on the scanned model.
- Analyzed SMART Permission Denied root cause (kernel locking raw block ioctl to root).

## 2026-03-19 12:48 PM
- Address comprehensive user audit:
  - Addressed raw byte formatting via `format_bytes` helper.
  - Implemented QThread `WorkerThread` safely to completely decouple `lsblk` and `smartctl` subprocess executions from the Main UI Thread, dramatically improving UI responsiveness exactly as requested.
  - Mitigated thread accumulation, properly disabling the scanning button and preventing stale data.
  - Scaled window width and added a dedicated 3rd column for Hardware health tracking directly parsing ATA attributes and NVMe health logs (Reallocated, Wear Leveling, Power Cycles, NVMe Spare %).
  - Handled URLLib SSL context requirements and `drive_name` regex validation for security.

## 2026-03-19 12:43 PM
- User requested lifetime usage, web info scanning, and M.2/UAS support.
- Implemented `get_smart_info` to parse NVMe `data_units_written` and SATA `Total_LBAs_Written` / `Host_Writes_32MiB` to determine Total Bytes Written (TBW).
- Built a multi-threaded web scraper querying DDG HTML for drive models and returning an italicized info blurb.
- Updated UI grid layout to be extremely dense, fitting ~22 hardware properties without scrolling (620x430), retaining the antigravity theme.

## 2026-03-19 12:40 PM
- Added .gitignore to untrack pycache.
- Successfully implemented PyQt6 GUI (Antigravity Theme) and backend (`lsblk` JSON parsing).
- All goals met for v1.0, compact and info-heavy layout implemented.

## 2026-03-19 12:38 PM
- Started working on Storage_Detailer v1.0. 
- Created persistent tracking files following the Anchor method and Ironclad Artifact Persistence rules.
- Chose Python and PyQt6/PySide6 for the app as it's great for Linux/CachyOS.
