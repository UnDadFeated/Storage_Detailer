# Storage Detailer v1.0

A compact, modern, lightweight storage analysis tool for Linux (CachyOS).
Designed with a clean, low-profile grey scale theme with 1px silver accents. It extracts deep telemetry from connected physical drives and displays it in a dense, scrollbar-free UI.

## Features
- Dropdown device selector (including USB drives).
- Scan button to refresh detailed metrics.
- Highly compact 'antigravity' grey theme design.
- Low ram usage, lightweight.

## Recommended Setup (No Sudo Required)
To allow Storage Detailer to read extensive SMART data without requiring `sudo` or root privileges every launch, add your user to the standard Linux `disk` group and add a udev rule to allow group read access to disks.

1. Add your user to the `disk` group:
   ```bash
   sudo usermod -aG disk $USER
   ```
2. Create a udev rule (e.g., `/etc/udev/rules.d/99-smartctl.rules`):
   ```bash
   SUBSYSTEM=="block", GROUP="disk", MODE="0660"
   ```
3. Reload udev rules (`sudo udevadm control --reload-rules && sudo udevadm trigger`) and log out/in.
