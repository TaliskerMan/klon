"""Block device and partition scanner backend wrapper.

This module leverages `lsblk` to scan physical drives and partitions attached
to the host. It returns structured dataclass hierarchies representing disk layouts.
"""

import subprocess  # nosec B404
import shutil
import logging
import json
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Drive:
    """Dataclass representation of a physical disk drive or a logical partition.

    Attributes:
        name: Short identifier of the device (e.g., "sda" or "sda1").
        path: Path to the device node (e.g., "/dev/sda").
        size: Human-readable capacity representation (e.g., "500G").
        model: Hardware model identifier (e.g., "Samsung SSD 860").
        type: Device classification (e.g., "disk" or "part").
        mountpoint: Current filesystem path where the drive is mounted, if any.
        children: Partitions or nested structures under this block device.
    """
    name: str # e.g. "sda"
    path: str # e.g. "/dev/sda"
    size: str # e.g. "500G"
    model: str # e.g. "Samsung SSD 860"
    type: str # e.g. "disk"
    mountpoint: Optional[str] = None
    children: List['Drive'] = None

    def __post_init__(self):
        """Ensure the children array is initialized to a list if left empty."""
        if self.children is None:
            self.children = []

def list_drives() -> List[Drive]:
    """Scan and list all block devices on the system using lsblk.

    Runs `lsblk -J -o NAME,PATH,SIZE,MODEL,TYPE,MOUNTPOINT` to retrieve a JSON list
    of physical drives and partitions, parsing them into a structured hierarchy.

    Returns:
        A list of Drive dataclass structures representing base disk drives.
    """
    try:
        lsblk_path = shutil.which('lsblk')
        if not lsblk_path:
            logging.error("lsblk not found in PATH")
            return []

        # Run lsblk to get JSON output
        result = subprocess.run(  # nosec B603
            [lsblk_path, '-J', '-o', 'NAME,PATH,SIZE,MODEL,TYPE,MOUNTPOINT'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        drives = []
        for device in data.get('blockdevices', []):
            # We are primarily interested in base "disk" types
            drive = _parse_device(device)
            drives.append(drive)
            
        return drives

    except subprocess.CalledProcessError as error:
        logging.error(f"Error running lsblk: {error}")
        return []
    except json.JSONDecodeError as error:
        logging.error(f"Error parsing lsblk output: {error}")
        return []

def _parse_device(device_data: dict) -> Drive:
    """Recursively parse JSON object from lsblk output into Drive dataclasses.

    Args:
        device_data: Dictionary representing block device properties from lsblk's JSON.

    Returns:
        A Drive object populated with values and parsed children partitions.
    """
    children_data = device_data.get('children', [])
    children = [_parse_device(child) for child in children_data]
    
    return Drive(
        name=device_data.get('name'),
        path=device_data.get('path'),
        size=device_data.get('size'),
        model=device_data.get('model', 'Unknown'),
        type=device_data.get('type'),
        mountpoint=device_data.get('mountpoint'),
        children=children
    )

if __name__ == "__main__":
    drives = list_drives()
    for drive in drives:
        logging.info(f"Found Drive: {drive.model} ({drive.path}) - {drive.size}")
        for part in drive.children:
            logging.info(f"  Partition: {part.name} - {part.size} ({part.mountpoint})")

