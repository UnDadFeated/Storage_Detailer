# Conversation Log

<!-- ANCHOR -->
## 2026-03-19 01:14 PM
- Evaluated `TRIM MAX` logic regarding capacity and confirmed it indicates strictly the maximum block discard size limit in cache, not disk width.
- Extracted raw `lsblk -b` byte sizing constraints inside the `ui.py` parsing function to resolve base-10 drive capacities accurately mimicking hardware manufacturer metrics via simple div ops. (E.g. ~500GB, 2TB) dynamically concatenated explicitly to the Amazon query target strings.

## 2026-03-19 01:12 PM
- Diagnosed fatal exit block from `smartctl` yielding error bitmasks corresponding to valid warnings (e.g., Code 4 Pre-fail). Dropped error threshold mask enforcement in favor of strictly validating json presence via `stdout.strip()`.
- Addressed hanging thread locks implicitly occurring when piping silent `pkexec`/`sudo` routines lacking `-n` parameter bindings.
- Fully removed the unreliable direct Amazon Product HTML scraper entirely based on extensive review identifying perpetual 503 HTTP Bot drops.
- Finalized Amazon button GUI constraints (x24y60), reissuing the `Amazon` text.

## 2026-03-19 01:08 PM
- Designed an Amazon direct-scraper inside `get_amazon_data` to bypass generalized search engines and rip live product identifiers and prices straight off the store.
- Updated UI area layout injecting bolded Amazon product names and prices next to the "buy on amazon" right-aligned text label and cart button per user request.

## 2026-03-19 01:05 PM
- Refactored SMART permission escalations natively integrating `sudo` and `pkexec` wrappers if standard `smartctl` execution rejects standard privileges. Documented `udev` solutions in README.
- Perfected Amazon URL bindings utilizing strictly cached data and `quote_plus`.
- Remodelled UI structure setting static labels stretching constraints, breaking out the Wear QProgressBar cleanly, equalizing the 3x Drive Health grid.

## 2026-03-19 01:00 PM
- Replaced the textual Amazon button with a succinct '🛒' shopping cart icon and added a localized tool-tip to keep the UI strictly minimalist.

## 2026-03-19 12:58 PM
- Removed PCPartPicker button from the UI to focus strictly on Amazon affiliate links per latest request.

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
