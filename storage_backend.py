import subprocess
import json
import logging
import urllib.request
import urllib.parse
import re

def get_physical_drives():
    try:
        cmd = ["lsblk", "-J", "-d", "-b", "-O"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        devices = data.get("blockdevices", [])
        physical_drives = [d for d in devices if d.get("type") == "disk" and not d.get("name", "").startswith("zram")]
        return physical_drives
    except Exception as e:
        logging.error(f"Failed to scan drives: {e}")
        return []

def get_drive_details(drive_name):
    try:
        cmd = ["lsblk", "-p", "-J", "-O", "-b", f"/dev/{drive_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        devices = data.get("blockdevices", [])
        if devices:
            return devices[0]
        return None
    except Exception as e:
        logging.error(f"Failed to get drive details for {drive_name}: {e}")
        return None

def get_smart_info(drive_name):
    """
    Returns SMART info by invoking smartctl.
    Supports parsing TBW (Total Bytes Written) for NVMe and SATA.
    """
    try:
        cmd = ["smartctl", "-a", "-j", f"/dev/{drive_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if not result.stdout.strip():
            return {"status": "Unavailable", "temp": "N/A", "power_on_hours": "N/A", "tbw": "N/A"}
            
        data = json.loads(result.stdout)
        
        messages = data.get("smartctl", {}).get("messages", [])
        for msg in messages:
            if "Permission denied" in msg.get("string", ""):
                return {"status": "Perm Denied", "temp": "N/A", "power_on_hours": "N/A", "tbw": "N/A"}

        status = data.get("smart_status", {}).get("passed")
        if status is True:
            status_str = "PASSED"
        elif status is False:
            status_str = "FAILED"
        else:
            status_str = "UNKNOWN"
            
        temp = data.get("temperature", {}).get("current", "N/A")
        power_on = data.get("power_on_time", {}).get("hours", "N/A")
        
        # Calculate TBW (Lifetime Usage)
        tbw = "N/A"
        
        # 1. Check NVMe specification for Data Units Written
        nvme_log = data.get("nvme_smart_health_information_log", {})
        if "data_units_written" in nvme_log:
            # NVMe data units are in thousands of 512-byte blocks
            # TBW = units * 1000 * 512 bytes
            units = nvme_log["data_units_written"]
            bytes_written = units * 1000 * 512
            tbw = f"{bytes_written / (1024**4):.2f} TB"
            
        # 2. Check SATA standard attributes
        if tbw == "N/A" and "ata_smart_attributes" in data:
            attributes = data["ata_smart_attributes"].get("table", [])
            for attr in attributes:
                name = attr.get("name", "").lower()
                raw_val = attr.get("raw", {}).get("value", 0)
                if "total_lbas_written" in name:
                    # 512 bytes per LBA typically
                    bytes_written = raw_val * 512
                    tbw = f"{bytes_written / (1024**4):.2f} TB"
                    break
                elif "host_writes_32mib" in name:
                    bytes_written = raw_val * 32 * 1024 * 1024
                    tbw = f"{bytes_written / (1024**4):.2f} TB"
                    break
        
        return {
            "status": status_str,
            "temp": f"{temp}°C" if temp != "N/A" else "N/A",
            "power_on_hours": str(power_on),
            "tbw": tbw
        }
    except Exception as e:
        logging.error(f"SMART command failed for {drive_name}: {e}")
        return {"status": "Error", "temp": "N/A", "power_on_hours": "N/A", "tbw": "N/A"}

def get_web_info(model, serial):
    """
    Scrapes a lightweight HTML search page (DuckDuckGo) to find context for the drive model.
    """
    if not model or str(model).strip() in ["", "N/A", "Unknown"]:
        return "Not enough info to search web."
        
    query = f"{model} ssd hdd specs"
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            
            # Simple regex parser for DDG HTML snippets
            # Extracts the first snippet
            match = re.search(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            if match:
                # Remove nested bold/italic tags
                snippet = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                # Unescape some entities
                snippet = snippet.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
                
                # Truncate string for UI fit if needed
                if len(snippet) > 130:
                    snippet = snippet[:127] + "..."
                return snippet
            
            return "No obvious specs found."
    except Exception as e:
        logging.error(f"Web scan failed: {e}")
        return "Web scan failed or timed out."
