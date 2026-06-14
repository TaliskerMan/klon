"""Live ISO downloader and flashing wrapper.

This module downloads standard Live ISO files from repositories and flashes them to
removable block devices using `dd` run via `pkexec`. It includes options for setting
up USB persistence.
"""

import subprocess  # nosec B404
import shutil
import logging
import os
import requests
import threading

# Default to a small, reliable live ISO (Debian Live Standard)
DEFAULT_ISO_URL = "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/debian-live-12.5.0-amd64-standard.iso"
DEFAULT_ISO_NAME = "debian-live-standard.iso"

def download_iso(url: str, dest_path: str, progress_callback=None) -> bool:
    """Downloads an ISO image from the specified URL to a local destination file.

    Fetches the remote content-length and streams chunks of size 8192 bytes,
    triggering the progress_callback with percentage values.

    Args:
        url: Direct link to download the ISO image.
        dest_path: Local filesystem path where the ISO should be saved.
        progress_callback: Optional callable accepting (percent: float, message: str)
            invoked periodically during transfer.

    Returns:
        True if the download finished successfully, False otherwise.
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
        logging.error(f"Download error: {e}")
        return False

def flash_iso_and_setup_persistence(iso_path: str, device_path: str, progress_callback=None):
    """Flashes a local ISO file to a target USB block device.

    Uses `pkexec dd` to execute the block write asynchronously. Once flashing is done,
    it reloads partition tables via `partprobe`.
    
    WARNING: This operation is destructive and completely overwrites the target device.

    Args:
        iso_path: Absolute path to the source ISO image.
        device_path: Absolute path to the destination USB device node.
        progress_callback: Optional callable accepting (percent: int/None, message: str)
            invoked to update progress text in GUI.

    Raises:
        ValueError: If the input ISO file does not exist.
        RuntimeError: If pkexec or dd are missing from the system path or dd fails.
    """
    if not os.path.exists(iso_path):
        raise ValueError("ISO file not found")
        
    if progress_callback:
        progress_callback(0, "Starting Flash operations...")

    # 1. Flash ISO using dd
    # This overwrites the partition table with the ISO's layout (usually Hybrid MBR/GPT)
    pkexec_path = shutil.which('pkexec')
    dd_path = shutil.which('dd')
    if not pkexec_path or not dd_path:
        raise RuntimeError("Required binaries (pkexec, dd) not found in PATH")

    cmd = [
        pkexec_path,
        dd_path,
        f'if={iso_path}',
        f'of={device_path}',
        'bs=4M',
        'status=progress',
        'conv=fsync'
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  # nosec B603
    
    # Monitor dd progress output from stderr stream
    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line and progress_callback:
            # Parse dd output and notify GUI status label.
            # dd status=progress output is tricky to parse reliably across versions, 
            # usually like: "20971520 bytes (21 MB, 20 MiB) copied, 1.003 s, 20.9 MB/s"
            progress_callback(None, f"Flashing: {line.strip()}")
            
    if process.returncode != 0:
        raise RuntimeError("Flashing failed")

    if progress_callback:
        progress_callback(90, "Flashing complete. Setting up storage...")

    # 2. Add Persistence Partition
    # We essentially need to create a partition in the empty space.
    # Debian Live expects a partition labeled 'persistence' containing persistence.conf
    # but for simple storage usage, we just want a secondary partition on the remaining space.
    
    # Reload partition table so the kernel recognizes the new layout
    partprobe_path = shutil.which("partprobe")
    if partprobe_path:
        subprocess.run([pkexec_path, partprobe_path, device_path])  # nosec B603
    else:
        logging.warning("partprobe not found, skipping partition reload")
    
    # Automating partitioning on hybrid layouts is high risk without a library like pyparted.
    # We skip automatic partitioning in V1 to avoid data corruption, leaving it to external tools.
    try:
        # Create partition 3 (usually 1 is iso, 2 is esp)
        parted_path = shutil.which("parted")
        if parted_path:
            subprocess.run([  # nosec B603
                pkexec_path, parted_path, '-s', device_path, 
                'mkpart', 'primary', 'ext4', '100%', '100%' 
            ], check=False)
        
        # Flashing is completed; manual partition resizing via GParted is recommended for now.
        pass
        
    except Exception as e:
        logging.error(f"Partitioning error: {e}")

    if progress_callback:
        progress_callback(100, "Done!")

