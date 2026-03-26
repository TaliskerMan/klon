#!/bin/bash
set -e

# Configuration
VM_MEMORY="4G"
VM_CORES="2"
DISK_SIZE="10G"
TEST_WORKING_DIR="$(pwd)/tests/vm_data"
SOURCE_CODE_DIR="$(pwd)"

# Helper function for printing
print_step() {
    echo -e "\n\033[1;36m==> $1\033[0m"
}

print_error() {
    echo -e "\n\033[1;31mERROR: $1\033[0m"
}

# Check for QEMU dependencies
if ! command -v qemu-system-x86_64 &> /dev/null; then
    print_error "qemu-system-x86_64 could not be found. Please install qemu-kvm."
    exit 1
fi

if ! command -v qemu-img &> /dev/null; then
    print_error "qemu-img could not be found. Please install qemu-utils."
    exit 1
fi

# Usage
usage() {
    echo "Usage: $0 --iso <path_to_iso> [options]"
    echo ""
    echo "Options:"
    echo "  --iso <path>    Path to the bootable ISO image (Required)"
    echo "  --clean         Clean up old disk images before starting"
    echo "  --help          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --iso ~/Downloads/pop-os_22.04_amd64_intel_34.iso"
    exit 1
}

# Parse arguments
ISO_PATH=""
CLEAN=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --iso) ISO_PATH="$2"; shift ;;
        --clean) CLEAN=true ;;
        --help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

if [ -z "$ISO_PATH" ]; then
    print_error "ISO path is required."
    usage
fi

if [ ! -f "$ISO_PATH" ]; then
    print_error "ISO file not found at: $ISO_PATH"
    exit 1
fi

# Prepare environment
mkdir -p "$TEST_WORKING_DIR"

if [ "$CLEAN" = true ]; then
    print_step "Cleaning up old disk images..."
    rm -f "$TEST_WORKING_DIR/target_drive_1.qcow2"
    rm -f "$TEST_WORKING_DIR/target_drive_2.qcow2"
fi

# Create virtual drives if they don't exist
create_drive() {
    local name=$1
    local path="$TEST_WORKING_DIR/$name"
    if [ ! -f "$path" ]; then
        print_step "Creating virtual drive: $name ($DISK_SIZE)"
        qemu-img create -f qcow2 "$path" "$DISK_SIZE"
    else
        echo "Using existing drive: $name"
    fi
}

create_drive "target_drive_1.qcow2"
create_drive "target_drive_2.qcow2"

print_step "Starting QEMU VM..."
print_step "Once inside the VM, mount the source code with:"
echo "  sudo mkdir -p /mnt/klon"
echo "  sudo mount -t 9p -o trans=virtio,version=9p2000.L,msize=512000 host0 /mnt/klon"
echo "  python3 /mnt/klon/src/klon/main.py"
echo ""

# Launch QEMU
# -enable-kvm: Use KVM acceleration
# -m: Memory
# -smp: CPU cores
# -cdrom: Boot ISO
# -drive: Attach virtual drives
# -virtfs: Share local source code directory
qemu-system-x86_64 \
    -enable-kvm \
    -m "$VM_MEMORY" \
    -smp "$VM_CORES" \
    -cdrom "$ISO_PATH" \
    -boot d \
    -drive file="$TEST_WORKING_DIR/target_drive_1.qcow2",if=virtio,format=qcow2 \
    -drive file="$TEST_WORKING_DIR/target_drive_2.qcow2",if=virtio,format=qcow2 \
    -virtfs local,path="$SOURCE_CODE_DIR",mount_tag=host0,security_model=mapped,id=host0 \
    -net nic -net user \
    -vga virtio \
    -display gtk,gl=on \
    -name "Klon Test VM"

print_step "VM Shutdown."
