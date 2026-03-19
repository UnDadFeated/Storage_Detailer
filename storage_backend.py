import subprocess
import json
import logging
import urllib.request
import urllib.parse
import re
import ssl

def format_bytes(n):
    if n is None or n == "":
        return "N/A"
    try:
        # Handles strings cleanly
        if isinstance(n, str) and not n.isdigit() and not n.replace('.','',1).isdigit():
            # Already formatted or non-numeric
            return str(n)
        
        val = float(n)
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if val < 1024.0:
                return f"{val:.2f} {unit}" if unit != "B" else f"{int(val)} B"
            val /= 1024.0
        return f"{val:.2f} EB"
    except (ValueError, TypeError):
        return str(n)

def validate_drive_name(drive_name):
    if not re.match(r"^[a-zA-Z0-9]+$", str(drive_name)):
        raise ValueError("Invalid drive name format")

def get_physical_drives():
    try:
        cmd = ["lsblk", "-J", "-d", "-b", "-o", "NAME,MODEL,VENDOR,REV,SERIAL,WWN,SIZE,TRAN,ROTA,SCHED,PATH,RQ-SIZE,LOG-SEC,PHY-SEC,MIN-IO,OPT-IO,DISC-GRAN,DISC-MAX,DISC-ZERO,TYPE"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        devices = data.get("blockdevices", [])
        physical_drives = [d for d in devices if str(d.get("type", "")).lower() == "disk" and not str(d.get("name", "")).startswith("zram")]
        return physical_drives
    except Exception as e:
        logging.error(f"Failed to scan drives: {e}")
        return []

def get_drive_details(drive_name):
    try:
        validate_drive_name(drive_name)
        cmd = ["lsblk", "-p", "-J", "-b", "-o", "NAME,MODEL,VENDOR,REV,SERIAL,WWN,SIZE,TRAN,ROTA,SCHED,PATH,RQ-SIZE,LOG-SEC,PHY-SEC,MIN-IO,OPT-IO,DISC-GRAN,DISC-MAX,DISC-ZERO", f"/dev/{drive_name}"]
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
    try:
        validate_drive_name(drive_name)
        cmd = ["smartctl", "-a", "-j", f"/dev/{drive_name}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode & 1:
            return {"status": "Fatal Error", "error": "Command failed"}

        if not result.stdout.strip():
            return {"status": "Unavailable"}
            
        data = json.loads(result.stdout)
        
        messages = data.get("smartctl", {}).get("messages", [])
        for msg in messages:
            if "Permission denied" in msg.get("string", ""):
                return {"status": "Perm Denied"}

        status = data.get("smart_status", {}).get("passed")
        if status is True:
            status_str = "PASSED"
        elif status is False:
            status_str = "FAILED"
        else:
            status_str = "UNKNOWN"
            
        temp = data.get("temperature", {}).get("current", "N/A")
        power_on = data.get("power_on_time", {}).get("hours", "N/A")
        
        tbw = "N/A"
        pct_used = "N/A"
        avail_spare = "N/A"
        pwr_cycles = data.get("power_cycle_count", "N/A") 
        if pwr_cycles == "N/A": 
             pwr_cycles = data.get("nvme_smart_health_information_log", {}).get("power_cycles", "N/A")
        
        nvme_log = data.get("nvme_smart_health_information_log", {})
        if "data_units_written" in nvme_log:
            tbw = format_bytes(nvme_log["data_units_written"] * 1000 * 512)
        if "percentage_used" in nvme_log:
            pct_used = f"{nvme_log['percentage_used']}"
        if "available_spare" in nvme_log:
            avail_spare = f"{nvme_log['available_spare']}"

        ata_attrs = data.get("ata_smart_attributes", {}).get("table", [])
        reallocated = "N/A"
        pending = "N/A"
        uncorrectable = "N/A"
        wear_leveling = "N/A"

        for attr in ata_attrs:
            name = attr.get("name", "").lower()
            raw_val = attr.get("raw", {}).get("value", 0)
            attr_id = attr.get("id")
            if "total_lbas_written" in name and tbw == "N/A":
                tbw = format_bytes(raw_val * 512)
            elif "host_writes_32mib" in name and tbw == "N/A":
                tbw = format_bytes(raw_val * 32 * 1024 * 1024)
            if attr_id == 5:
                reallocated = str(raw_val)
            if attr_id == 197:
                pending = str(raw_val)
            if attr_id == 198:
                uncorrectable = str(raw_val)
            if attr_id in (173, 177):
                wear_leveling = str(raw_val)
            if attr_id == 12 and pwr_cycles == "N/A":
                pwr_cycles = str(raw_val)
                
        form_factor = data.get("form_factor", {}).get("name", "N/A")
        rpm = data.get("rotation_rate", "N/A")
        if str(rpm) == "0":
            rpm = "Solid State"

        return {
            "status": status_str,
            "temp": f"{temp}°C" if temp != "N/A" else "N/A",
            "power_on_hours": str(power_on),
            "tbw": str(tbw),
            "pct_used": str(pct_used),
            "avail_spare": str(avail_spare),
            "pwr_cycles": str(pwr_cycles),
            "reallocated": str(reallocated),
            "pending": str(pending),
            "uncorrectable": str(uncorrectable),
            "wear_leveling": str(wear_leveling),
            "form_factor": str(form_factor),
            "rpm": str(rpm)
        }
    except Exception as e:
        logging.error(f"SMART command failed for {drive_name}: {e}")
        return {"status": "Error"}

def get_web_info(model, serial):
    if not model or str(model).strip() in ["", "N/A", "Unknown", "null"]:
        return "Not enough info to search web."
        
    query = f"{model} ssd hdd specs"
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            html = response.read().decode('utf-8')
            match = re.search(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            if match:
                snippet = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                snippet = snippet.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
                if len(snippet) > 130:
                    snippet = snippet[:127] + "..."
                return snippet
            return "No obvious specs found."
    except Exception as e:
        logging.error(f"Web scan failed: {e}")
        return "Web scan failed or timed out."
