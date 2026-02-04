import subprocess
import os

def clone_drive(source_path: str, dest_path: str, update_callback=None):
    """
    Clones source drive to destination using dd with status progress.
    WARNING: This is destructive to dest_path.
    
    Args:
        source_path: Path to source device (e.g., /dev/sda)
        dest_path: Path to destination device (e.g., /dev/sdb)
        update_callback: Optional callable to report progress (not fully implemented for dd yet)
    """
    if not os.path.exists(source_path):
        raise ValueError(f"Source {source_path} does not exist")
    if not os.path.exists(dest_path):
        raise ValueError(f"Destination {dest_path} does not exist")
        
    # Basic protection: Ensure we are not writing to the same drive
    if os.path.realpath(source_path) == os.path.realpath(dest_path):
        raise ValueError("Source and Destination cannot be the same")

    print(f"Starting clone from {source_path} to {dest_path}...")
    
    # Using dd with status=progress for now as it doesn't require extra packages like partclone yet
    # In the future, we should look into partclone for efficiency (only used blocks)
    cmd = [
        'pkexec', # We need root privileges for block device access
        'dd',
        f'if={source_path}',
        f'of={dest_path}',
        'bs=4M',
        'status=progress',
        'conv=fsync'
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # dd outputs progress to stderr
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
                    print(line.strip())
                    
        if process.returncode != 0:
            raise RuntimeError("Clone process failed")
            
        print("Cloning completed successfully.")
        
    except Exception as e:
        print(f"Cloning failed: {e}")
        raise

if __name__ == "__main__":
    # Test stub - DO NOT RUN without valid args
    print("This module provides cloning functionality. Import it to use.")
