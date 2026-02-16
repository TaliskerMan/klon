# VM Testing Walkthrough

I have implemented a VM-based testing environment for Klon. This allows you to test destructive operations like disk imaging and restoration safely without risking your physical machine.

## Prerequisites

Ensure your system has QEMU and KVM installed:
```bash
sudo apt install qemu-kvm qemu-utils
```

## Running the Test VM

1.  **Download a Live ISO**: You will need a bootable Linux ISO (e.g., Pop!_OS, Ubuntu, or Debian Live).

2.  **Run the Script**:
    Execute the helper script from the project root, pointing it to your ISO:
    ```bash
    ./tests/run_vm_test.sh --iso /path/to/your/distro.iso
    ```
    This command will:
    -   Create two 10GB virtual hard drives (`target_drive_1.qcow2`, `target_drive_2.qcow2`) in `tests/vm_data/`.
    -   Launch a QEMU VM with 4GB RAM and 2 vCPUs.
    -   Mount your local `klon` directory inside the VM.

## Inside the VM

Once the VM boots:

1.  **Open a Terminal**.
2.  **Mount the Source Code**:
    Run the following commands to mount your local code:
    ```bash
    sudo mkdir -p /mnt/klon
    sudo mount -t 9p -o trans=virtio,version=9p2000.L,msize=512000 host0 /mnt/klon
    ```
3.  **Run Klon**:
    ```bash
    # You may need to install dependencies first if they aren't on the Live ISO
    # sudo apt update && sudo apt install python3-gi python3-requests ...
    
    python3 /mnt/klon/src/klon/main.py
    ```

## Testing Scenarios

-   **Backup**: Select one of the virtual drives (e.g., `/dev/vdb`) as the source and create a backup image.
-   **Restore**: Use the "Restore" tab to write a disk image to a virtual drive.
-   **Destructive Tests**: Feel free to wipe/overwrite `/dev/vdb` or `/dev/vdc`. They are just files on your host machine!

## Cleanup

To remove the virtual disk images and start fresh:
```bash
./tests/run_vm_test.sh --iso ... --clean
```
