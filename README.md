# Raspberry Pi 5 NVMe Ubuntu Installation

This repository contains automated Python scripts to wipe an NVMe drive and install Ubuntu Server on a Raspberry Pi 5.

## Overview

This tool automates the process of:
1. Securely wiping the NVMe drive
2. Downloading Ubuntu Server for ARM64
3. Configuring unattended installation with cloud-init
4. Writing the OS to the NVMe drive with your custom settings

## Prerequisites

- Raspberry Pi 5 with NVMe drive attached
- Running from SD card with Raspberry Pi OS
- Internet connection for downloading Ubuntu image
- Root/sudo access

## Quick Start

### 1. Setup Credentials

First, run the setup script to configure your Ubuntu login credentials:

```bash
python3 setup.py
```

This will:
- Ask for your desired username
- Ask for your password (securely, not displayed)
- Ask for your SSH public key (optional - for passwordless SSH access)
- Create a `.env` file with your credentials
- Set restrictive permissions (600) on the credentials file

### 2. Install Ubuntu

Once credentials are configured, run the installation script:

```bash
sudo python3 install_ubuntu.py
```

### 3. Boot from NVMe

After the script completes:

1. Shutdown the Raspberry Pi: `sudo shutdown now`
2. Remove the SD card
3. Power on the Pi - it will boot from NVMe
4. Wait for the initial setup to complete (cloud-init will run automatically)
5. The system will reboot when ready

## Customization

### Changing Ubuntu Version

Edit `install_ubuntu.py` and modify the `UBUNTU_VERSION` variable:

```python
UBUNTU_VERSION = "24.04.1"  # Change to desired version
```

### Adding Packages

Edit the `create_cloud_init()` function in `install_ubuntu.py` to add more packages:

```python
packages:
  - ubuntu-server
  - your-custom-package
```

### Network Configuration

The default configuration uses DHCP. To set a static IP, edit the `create_cloud_init()` function and modify the `network_config` variable.

### Custom Setup Scripts

Place shell scripts (`.sh` files) in the `custom-scripts/` directory to run them during installation:

```bash
# Create a script
cat > custom-scripts/01-install-docker.sh << 'EOF'
#!/bin/bash
apt-get update
apt-get install -y docker.io
echo "Docker installed!" >> /var/log/setup.log
EOF
```

Scripts are executed in alphabetical order on first boot. See `custom-scripts/README.md` for details.

### PREEMPT_RT (Real-Time) Kernel via Ubuntu Pro

Enable the official PREEMPT_RT kernel for Raspberry Pi using **Ubuntu Pro**:

**What is PREEMPT_RT?**
- Makes the Linux kernel fully preemptible
- Reduces latency and jitter
- Essential for real-time applications (robotics, audio processing, CNC, etc.)

**How to enable:**

1. **Get a free Ubuntu Pro token** at https://ubuntu.com/pro (personal use is free)
2. **Run setup.py** and paste your token when prompted
3. The installer will automatically:
   - Attach your Ubuntu Pro subscription
   - Enable the real-time kernel: `sudo pro enable realtime-kernel --variant=raspi`
   - Configure it to boot by default

**To skip RT kernel installation:**
Leave the Ubuntu Pro token blank during setup, or remove the script:
```bash
rm custom-scripts/50-install-rt-kernel.sh
```

**Verification after boot:**
```bash
# Check if running RT kernel (should show "rt" in the version)
uname -r

# Verify PREEMPT_RT is enabled in kernel config
grep CONFIG_PREEMPT_RT /boot/config-$(uname -r)

# Check Ubuntu Pro status
pro status
```

## Repeating on Multiple Devices

To use this on another Raspberry Pi 5:

1. Copy this repository to the new device
2. Run `python3 setup.py` to configure new credentials (or copy the `.env` file securely)
3. Run `sudo python3 install_ubuntu.py`


## License

This project is provided as-is for automating Ubuntu installation on Raspberry Pi 5.

## Contributing

Feel free to submit improvements or bug fixes via pull requests.

## Documentation

- [PREEMPT_RT Kernel Guide](docs/PREEMPT_RT.md) - Detailed information about the Real-Time kernel option, including manual compilation instructions and performance tuning
