"""Disk cloning and raw image backup/restore wrapper.

This module executes `dd` as a subprocess with root privileges using `pkexec`
to clone physical block devices or save/restore them from raw file images.
It monitors the progress feedback written to the subprocess's stderr stream.
"""

import subprocess  # nosec B404
import shutil
import logging
import os

def clone_drive(source_path: str, dest_path: str, update_callback=None):
    """Clones a source block device or image to a destination device or image.

    This function executes `dd` with `status=progress` and `conv=fsync`. Since
    writing to physical block devices requires root permissions, the command is
    run via `pkexec`.

    Args:
        source_path: Absolute path to the source device or raw disk image.
        dest_path: Absolute path to the destination device or target raw image.
        update_callback: Optional callable accepting a string to receive live status updates.

    Raises:
        ValueError: If source or destination path is invalid, or if they point to the same device.
        RuntimeError: If pkexec or dd is missing from PATH, or if the subprocess fails.
    """
    if not os.path.exists(source_path):
        raise ValueError(f"Source {source_path} does not exist")
    if not os.path.exists(dest_path):
        raise ValueError(f"Destination {dest_path} does not exist")
        
    # Basic protection: Ensure we are not writing to the same drive
    if os.path.realpath(source_path) == os.path.realpath(dest_path):
        raise ValueError("Source and Destination cannot be the same")

    logging.info(f"Starting clone from {source_path} to {dest_path}...")
    
    # Using dd with status=progress for now as it doesn't require extra packages like partclone yet.
    # In the future, we should look into partclone for efficiency (only copying used blocks).
    pkexec_path = shutil.which('pkexec')
    dd_path = shutil.which('dd')
    if not pkexec_path or not dd_path:
        raise RuntimeError("Required binaries (pkexec, dd) not found in PATH")

    cmd = [
        pkexec_path, # We need root privileges for block device access
        dd_path,
        f'if={source_path}',
        f'of={dest_path}',
        'bs=4M',
        'status=progress',
        'conv=fsync'
    ]
    
    try:
        process = subprocess.Popen(  # nosec B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # dd outputs progress information to stderr
            text=True
        )
        
        # We process stderr line by line to capture progress
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                if update_callback:
                    update_callback(line.strip())
                else:
                    logging.info(line.strip())
                    
        if process.returncode != 0:
            raise RuntimeError("Clone process failed")
            
        logging.info("Cloning completed successfully.")
        
    except Exception as e:
        logging.error(f"Cloning failed: {e}")
        raise

def backup_to_image(source_device: str, image_path: str, update_callback=None):
    """Backs up a physical source device into a raw disk image file.

    Args:
        source_device: Absolute path to the source block device (e.g., /dev/sda).
        image_path: Absolute path to the destination image file (e.g., /path/to/backup.img).
        update_callback: Optional status callback to report live progress.
    """
    clone_drive(source_device, image_path, update_callback)

def restore_from_image(image_path: str, dest_device: str, update_callback=None):
    """Restores a raw disk image file back into a physical destination device.

    Args:
        image_path: Absolute path to the source raw disk image.
        dest_device: Absolute path to the target block device (e.g., /dev/sdb).
        update_callback: Optional status callback to report live progress.

    Raises:
        ValueError: If the input image file does not exist.
    """
    if not os.path.exists(image_path):
        raise ValueError(f"Image file {image_path} does not exist")
    
    clone_drive(image_path, dest_device, update_callback)

if __name__ == "__main__":
    # Test stub - DO NOT RUN without valid args
    logging.warning("This module provides cloning functionality. Import it to use.")

