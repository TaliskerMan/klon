# Klon - Comprehensive User Guide

> [!CAUTION]
> **CRITICAL WARNING: TESTING PHASE**
> **Klon is currently in the active testing phase and is NOT yet recommended for production use.** 
> While it is designed to be your primary emergency recovery tool, using it on production drives at this stage could result in unintended data loss or incomplete backups. Please strictly limit your use of this tool to safe, experimental, or testing environments only.

Welcome to **Klon**! Klon is a specialized system cloning and recovery utility specifically engineered for the local GNOME laptop or workstation administrator.

---

## 🚀 1. What Klon Does

Klon is built exclusively for **emergency recovery**. 

When a critical failure occurs—whether due to a physical drive dying, a catastrophic update, or severe OS corruption—you need a reliable way to get your workstation back online immediately. Klon replaces the need to memorize dangerous, complex `dd` or `rsync` terminal commands by wrapping everything in a simple, user-friendly GTK4 + Libadwaita interface.

It is used to:
* **Perform Full System Clones:** Safely back up your entire OS drive to an external disk.
* **Generate Bootable Recovery Media:** Create emergency USB drives that allow you to boot into a minimal environment and restore your cloned system from bare metal.

---

## 💾 2. Installation Instructions

Klon is distributed as a highly verifiable, signed Debian package (`.deb`). 

1. **Obtain the Package:** Download the `klon_*.deb` file and its corresponding `.sha512` file.
2. **Verify Integrity:** Before installing system-level cloning tools, you should verify the package hash:
   ```bash
   sha512sum -c klon_*.deb.sha512
   ```
3. **Install the Application:** Execute the following in your terminal:
   ```bash
   sudo dpkg -i klon_*.deb
   sudo apt-get install -f  # Resolves any missing dependencies
   ```
4. **Launch:** Open your GNOME Application menu and search for **Klon**.

---

## 🎮 3. Navigation & Usage

Klon's interface is intentionally streamlined and uncluttered, ensuring that during high-stress emergency scenarios, you cannot make a wrong click.

### Creating a System Clone
*Note: Because this is a block-level clone, your destination drive must be equal to or larger than your source OS drive.*

1. Connect your dedicated external backup drive. **Warning:** All existing data on this target drive will be completely overwritten!
2. Open Klon and navigate to the **Clone** tab.
3. Select your current primary OS drive as the **Source**.
4. Select your external drive as the **Destination**.
5. Click **Start Clone**. 
   * **Awareness:** This process will take significant time depending on your drive speed and total disk size. Do not put your laptop to sleep, close the application, or interrupt this process.

### Creating Bootable Recovery Media
To restore a dead system, you must have a way to boot the machine independently of your broken hard drive.

1. Insert a blank USB flash drive (8GB or larger).
2. Navigate to the **Recovery Media** tab in the Klon interface.
3. Select the attached USB drive.
4. Click **Create Media**. Klon will format the USB and write a minimal, bootable recovery OS to the drive.

### Emergency Bare-Metal Restoration
If your primary workstation drive fails and your machine will no longer boot:
1. Physically replace the failed drive in your laptop/workstation with a new drive.
2. Insert your **Bootable Recovery USB**.
3. Connect your external hard drive containing your **System Clone**.
4. Power on the machine and boot from the USB drive. The recovery environment will guide you through selecting your system clone and securely writing it back to the new physical drive.

---
*Klon - Emergency recovery made simple. A Nordheim Online Product.*
