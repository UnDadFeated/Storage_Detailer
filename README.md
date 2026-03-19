# Storage Detailer

> A compact, information-dense drive analysis tool for Linux — built for speed, not fluff.

![Platform](https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-informational?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/version-1.2.1-orange?style=flat-square)

Storage Detailer extracts deep hardware telemetry from your connected storage devices and presents it in a dense, scrollbar-free interface. No bloat. No electron. No nonsense — just raw drive data, fast.

---

## Screenshots

> *Coming soon — snapshot your own drives using the built-in export button.*

---

## Features

- **33 data points per drive** across three columns: Hardware Identity, I/O & Transport, and SMART Health
- **Full SMART parsing** — status, temperature, power-on hours, power cycles, TBW, reallocated sectors, pending sectors, uncorrectable sectors, wear leveling count, NVMe % used, and available spare
- **NVMe & SATA support** — dedicated parsing paths for both `nvme_smart_health_information_log` and ATA attribute tables
- **Visual wear indicator** — color-coded progress bar (green → orange → red) driven by NVMe percentage used
- **Snapshot export** — one-click hardware data capture cropped to just the stats panel, saved to `~/Pictures/Screenshots` as a timestamped PNG
- **Amazon quick-search** — opens a pre-built affiliate search for the scanned drive model with base-10 capacity string appended for accuracy
- **DuckDuckGo web intel** — pulls a live spec snippet for the scanned model with resilient CSS fallback selectors
- **Threaded architecture** — all subprocess and network calls run off the main thread via `QThread`; UI never freezes
- **SMART privilege escalation** — silently attempts standard access, falls back to `sudo -n`, then `pkexec` if needed
- **Antigravity theme** — greyscale palette, 1px silver borders, monospace value labels, fixed 680×500 viewport

---

## Requirements

| Dependency | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| PyQt6 | GUI framework |
| `smartctl` (smartmontools) | SMART data extraction |
| `lsblk` (util-linux) | Block device enumeration |

Install system dependencies on Arch / CachyOS:
```bash
sudo pacman -S smartmontools util-linux python-pyqt6
```

On Debian / Ubuntu:
```bash
sudo apt install smartmontools util-linux python3-pyqt6
```

---

## Installation

```bash
git clone https://github.com/UnDadFeated/Storage_Detailer.git
cd Storage_Detailer
python main.py
```

No virtual environment required. No pip dependencies beyond PyQt6.

---

## SMART Permissions (Recommended Setup)

By default, `smartctl` requires root to read raw drive telemetry. Storage Detailer will attempt `sudo -n` and `pkexec` fallbacks automatically, but the cleanest solution is a one-time udev rule:

**1. Add your user to the `disk` group:**
```bash
sudo usermod -aG disk $USER
```

**2. Create a udev rule:**
```bash
sudo tee /etc/udev/rules.d/99-smartctl.rules <<EOF
SUBSYSTEM=="block", GROUP="disk", MODE="0660"
EOF
```

**3. Reload and re-login:**
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Then log out and back in. Storage Detailer will read SMART data without any privilege prompts.

> **Note:** If you skip this setup, Storage Detailer will fall back to `pkexec`, which spawns a standard PolKit GUI password dialog for temporary `smartctl` access.

---

## Usage

```bash
python main.py
```

1. Select a drive from the dropdown (NVMe, SATA, and USB drives are listed automatically)
2. Click **Scan** — all data populates within a few seconds
3. Click **Snapshot** to save a cropped PNG of the hardware stats panel
4. Click **Amazon** to open a pre-built search for the scanned model

---

## Data Reference

### Column 1 — Hardware Identity
| Field | Source |
|---|---|
| Model, Vendor, Firmware Rev | `lsblk` |
| Serial Number, WWN | `lsblk` |
| Form Factor | `smartctl` `form_factor.name` |
| Transport, Path, Capacity | `lsblk` |
| Logical / Physical Sector Size | `lsblk` |

### Column 2 — I/O & Transport
| Field | Source |
|---|---|
| Type (HDD/SSD), RPM | `lsblk` rota + `smartctl` rotation_rate |
| Queue Depth, I/O Scheduler | `lsblk` |
| Min I/O, Opt I/O | `lsblk` |
| TRIM Granularity, TRIM Max, TRIM Zero | `lsblk` |
| ATA Standard, Protocol | `smartctl` |

### Column 3 — SMART Health
| Field | Source |
|---|---|
| SMART Status | `smart_status.passed` |
| Temperature | `temperature.current` |
| Power On Hours | `power_on_time.hours` |
| Power Cycles | Attr 12 / `power_cycle_count` |
| TBW | NVMe `data_units_written` × 512000 or ATA attr 241/246 |
| Wear Level Count | ATA attr 173 / 177 |
| NVMe % Used, Available Spare | `nvme_smart_health_information_log` |
| Reallocated Sectors | ATA attr 5 |
| Pending Sectors | ATA attr 197 |
| Uncorrectable Sectors | ATA attr 198 |

---

## Architecture

```
main.py
└── ui.py  (StorageDetailer : QMainWindow)
    ├── WorkerThread : QThread
    │   ├── get_drive_details()   → lsblk subprocess
    │   ├── get_smart_info()      → smartctl subprocess (with privilege fallback)
    │   └── get_web_info()        → DuckDuckGo HTML fetch (SSL, threaded)
    └── storage_backend.py
        ├── format_bytes()
        ├── validate_drive_name()
        ├── get_physical_drives()
        ├── get_drive_details()
        ├── get_smart_info()
        └── get_web_info()
```

All subprocess and network I/O is isolated to `WorkerThread`. The main thread only handles UI updates via Qt signals.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## Contributing

Issues and pull requests are welcome. If you're testing on a drive type that produces unexpected SMART output (particularly UAS/USB bridges or exotic NVMe controllers), opening an issue with the raw `smartctl -j` output is the most useful contribution you can make.

---

## License

MIT — do whatever you want with it.
