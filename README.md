# Storage Detailer v1.2

A compact, modern, lightweight storage analysis tool for Linux (CachyOS).
Designed with a clean, low-profile grey scale theme with 1px silver accents. It extracts deep telemetry from connected physical drives and displays it in a dense, scrollbar-free UI.

## Features
- Dropdown device selector (including USB drives).
- Instant Snapshot Export (📷 button) for cleanly cropped hardware stat images.
- Amazon eCommerce link generation with automated base-10 capacity string injection.
- Extensive SMART Drive Health monitoring and NVMe Wear percentage trackers.
- Highly compact 'antigravity' grey theme design.
- Low ram usage, lightweight.

## Recommended Setup (No Sudo Required)
To allow Storage Detailer to read extensive SMART data without requiring `sudo` or root privileges every launch, add your user to the standard Linux `disk` group and add a udev rule to allow group read access to disks.

*Note: If SMART metrics are locked natively, Storage Detailer will silently attempt `sudo -n` first, and intelligently fallback to `pkexec`. `pkexec` will spawn a standard PolKit GUI password dialog requesting explicit temporary permissions for `smartctl` execution if you choose to skip the recommended udev assignments natively.*

1. Add your user to the `disk` group:
   ```bash
   sudo usermod -aG disk $USER
   ```
2. Create a udev rule (e.g., `/etc/udev/rules.d/99-smartctl.rules`):
   ```bash
   SUBSYSTEM=="block", GROUP="disk", MODE="0660"
   ```
3. Reload udev rules (`sudo udevadm control --reload-rules && sudo udevadm trigger`) and log out/in.
