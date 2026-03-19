import subprocess
import json
import logging

def get_physical_drives():
    """
    Returns a list of physical drives using lsblk.
    """
    try:
        # Use lsblk to get block devices. 
        # -J: JSON, -d: non-recursive (no partitions), -O: all columns, -b: bytes
        cmd = ["lsblk", "-J", "-d", "-b", "-O"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        devices = data.get("blockdevices", [])
        
        # Filter for actual disks/drives (ignoring loop, ram, etc)
        physical_drives = [d for d in devices if d.get("type") == "disk" and not d.get("name", "").startswith("zram")]
        return physical_drives
    except Exception as e:
        logging.error(f"Failed to scan drives: {e}")
        return []

def get_drive_details(drive_name):
    """
    Get deep details about a specific drive, including partitions, using lsblk.
    """
    try:
        # -p: full path, -J: JSON, -O: all columns, -b: bytes
        cmd = ["lsblk", "-p", "-J", "-O", "-b", f"/dev/{drive_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        devices = data.get("blockdevices", [])
        if devices:
            return devices[0] # Return the root device object
        return None
    except Exception as e:
        logging.error(f"Failed to get drive details for {drive_name}: {e}")
        return None
