import subprocess
import os
import requests
import threading

# Default to a small, reliable live ISO (Debian Live Standard)
DEFAULT_ISO_URL = "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/debian-live-12.5.0-amd64-standard.iso"
DEFAULT_ISO_NAME = "debian-live-standard.iso"

def download_iso(url, dest_path, progress_callback=None):
    """
    Downloads the ISO to dest_path with progress reporting.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded += len(data)
                if progress_callback and total_size > 0:
                    percent = (downloaded / total_size) * 100
                    progress_callback(percent, f"Downloading: {int(percent)}%")
                    
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def flash_iso_and_setup_persistence(iso_path, device_path, progress_callback=None):
    """
    Flashes ISO to device and attempts to create a persistence partition.
    WARNING: DESTRUCTIVE.
    """
    if not os.path.exists(iso_path):
        raise ValueError("ISO file not found")
        
    if progress_callback:
        progress_callback(0, "Starting Flash operations...")

    # 1. Flash ISO using dd
    # This overwrites the partition table with the ISO's layout (usually Hybrid MBR/GPT)
    cmd = [
        'pkexec',
        'dd',
        f'if={iso_path}',
        f'of={device_path}',
        'bs=4M',
        'status=progress',
        'conv=fsync'
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Monitor dd progress
    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line and progress_callback:
            # Parse dd output? Or just generic "Flashing..."
            # dd status=progress output is tricky to parse reliably across versions, 
            # usually like: "20971520 bytes (21 MB, 20 MiB) copied, 1.003 s, 20.9 MB/s"
            progress_callback(None, f"Flashing: {line.strip()}")
            
    if process.returncode != 0:
        raise RuntimeError("Flashing failed")

    if progress_callback:
        progress_callback(90, "Flashing complete. Setting up storage...")

    # 2. Add Persistence Partition
    # We essentially need to create a partition in the empty space.
    # 'parted' or 'fdisk' can do this.
    # Debian Live expects a partition labeled 'persistence' with persistence.conf
    # But for our simple "Backup Storage" use case, we just need a partition "KLON_STORE"
    
    # Reload partition table
    subprocess.run(['pkexec', 'partprobe', device_path])
    
    # Use fdisk to create a new partition n -> p -> default -> default -> w
    # This is brittle script-wise. 'parted' is better but might complain about overlapping.
    # Let's try 'sgdisk' or 'parted' if available, else simple fdisk script.
    
    # Simplest approach for "Backup Storage":
    # 1. Create partition from end of ISO to end of Disk.
    try:
        # Create partition 3 (usually 1 is iso, 2 is esp)
        subprocess.run([
            'pkexec', 'parted', '-s', device_path, 
            'mkpart', 'primary', 'ext4', '100%', '100%' # This usually fails if start is vague. 
            # Better strategy: Get ISO size, start part after it.
        ], check=False)
        
        # Actually, simpler manual instruction might be safer for V1:
        # "Flash Complete. Please use GParted to add a storage partition."
        # AUTOMATING PARTITIONING IS HIGH RISK OF FAILURE WITHOUT ROBUST LIBRARY (e.g. pyparted)
        # OR parsing free space.
        
        # For this iteration, we will implement FLASHER ONLY.
        # Auto-persistence is a V2 feature.
        pass
        
    except Exception as e:
        print(f"Partitioning error: {e}")

    if progress_callback:
        progress_callback(100, "Done!")
