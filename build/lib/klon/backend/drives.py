import subprocess
import json
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Drive:
    name: str # e.g. "sda"
    path: str # e.g. "/dev/sda"
    size: str # e.g. "500G"
    model: str # e.g. "Samsung SSD 860"
    type: str # e.g. "disk"
    mountpoint: Optional[str] = None
    children: List['Drive'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

def list_drives() -> List[Drive]:
    """
    List all block devices using lsblk.
    Returns a list of Drive objects representing physical disks and their partitions.
    """
    try:
        # Run lsblk to get JSON output
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'NAME,PATH,SIZE,MODEL,TYPE,MOUNTPOINT'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        drives = []
        for device in data.get('blockdevices', []):
            # We are primarily interested in "disk" types effectively
            drive = _parse_device(device)
            drives.append(drive)
            
        return drives

    except subprocess.CalledProcessError as e:
        print(f"Error running lsblk: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing lsblk output: {e}")
        return []

def _parse_device(device_data: dict) -> Drive:
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
        print(f"Found Drive: {drive.model} ({drive.path}) - {drive.size}")
        for part in drive.children:
            print(f"  Partition: {part.name} - {part.size} ({part.mountpoint})")
