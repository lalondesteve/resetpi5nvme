#!/usr/bin/env python3
"""
Raspberry Pi 5 NVMe Ubuntu Installation Script
Automates wiping NVMe drive and installing Ubuntu Server with unattended setup.
"""

import os
import sys
import subprocess
import shutil
import hashlib
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Configuration
NVME_DEVICE = "/dev/nvme0n1"
UBUNTU_VERSION = "24.04.1"
UBUNTU_ARCH = "arm64"
DOWNLOAD_DIR = Path("./downloads")
TEMP_DIR = Path("./temp")

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_status(message):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command with proper error handling."""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e}")
            sys.exit(1)
        return False

def check_root():
    """Check if running as root."""
    if os.geteuid() != 0:
        print_error("This script must be run as root (use sudo)")
        sys.exit(1)

def load_credentials():
    """Load credentials from .env file."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print_error(".env file not found!")
        print_error("Please run ./setup.py first to create credentials.")
        sys.exit(1)
    
    print_status("Loading credentials from .env file...")
    
    credentials = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    credentials[key] = value
    except Exception as e:
        print_error(f"Failed to read .env file: {e}")
        sys.exit(1)
    
    if 'USERNAME' not in credentials or 'PASSWORD' not in credentials:
        print_error("USERNAME and PASSWORD must be set in .env file")
        sys.exit(1)
    
    ssh_key = credentials.get('SSH_PUBLIC_KEY', '')
    ubuntu_pro_token = credentials.get('UBUNTU_PRO_TOKEN', '')
    
    return credentials['USERNAME'], credentials['PASSWORD'], ssh_key, ubuntu_pro_token

def confirm_wipe():
    """Confirm wipe operation."""
    print()
    print_warning(f"WARNING: This will COMPLETELY WIPE {NVME_DEVICE}")
    print_warning("All data on this drive will be permanently destroyed!")
    print()
    
    confirm = input("Are you sure you want to continue? Type 'WIPE' to confirm: ").strip()
    
    if confirm != "WIPE":
        print_error("Wipe cancelled by user")
        sys.exit(1)

def download_ubuntu():
    """Download Ubuntu image for Raspberry Pi."""
    print_status(f"Downloading Ubuntu Server {UBUNTU_VERSION} for Raspberry Pi...")
    
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    # Ubuntu Server for Raspberry Pi ARM64
    ubuntu_url = f"https://cdimage.ubuntu.com/ubuntu-server/raspberry-pi/releases/{UBUNTU_VERSION}/release/ubuntu-{UBUNTU_VERSION}-preinstalled-server-arm64+raspi.img.xz"
    ubuntu_xz = DOWNLOAD_DIR / f"ubuntu-{UBUNTU_VERSION}-server-arm64.img.xz"
    ubuntu_img = DOWNLOAD_DIR / f"ubuntu-{UBUNTU_VERSION}-server-arm64.img"
    
    if ubuntu_img.exists():
        print_status("Ubuntu image already exists, skipping download...")
        return ubuntu_img
    
    print_status(f"Downloading from: {ubuntu_url}")
    
    try:
        # Download with progress
        print_status("Starting download...")
        run_command(f"wget -O '{ubuntu_xz}' '{ubuntu_url}'", check=True)
        
        print_status("Extracting image...")
        run_command(f"xz -d '{ubuntu_xz}'", check=True)
        
        print_status("Download and extraction complete!")
        return ubuntu_img
        
    except Exception as e:
        print_error(f"Failed to download or extract Ubuntu image: {e}")
        sys.exit(1)

def wipe_drive():
    """Wipe the NVMe drive."""
    print_status(f"Wiping {NVME_DEVICE}...")
    
    # Unmount any mounted partitions
    run_command(f"umount {NVME_DEVICE}* 2>/dev/null || true", check=False)
    
    # Wipe the partition table
    run_command(f"wipefs -a '{NVME_DEVICE}'", check=True)
    
    # Get drive size for calculating seek position
    try:
        size_output = run_command(f"blockdev --getsz '{NVME_DEVICE}'", 
                                 capture_output=True)
        drive_sectors = int(size_output)
        seek_position = drive_sectors // 2048 - 10  # Last 10MB in MB blocks
    except:
        seek_position = 0
    
    # Clear the first 10MB
    print_status("Clearing beginning of drive...")
    run_command(f"dd if=/dev/zero of='{NVME_DEVICE}' bs=1M count=10 status=progress", 
                check=True)
    
    # Clear the last 10MB if we can calculate the position
    if seek_position > 20:  # Make sure drive is big enough
        print_status("Clearing end of drive...")
        run_command(f"dd if=/dev/zero of='{NVME_DEVICE}' bs=1M count=10 "
                   f"seek={seek_position} status=progress", check=True)
    
    # Sync to ensure writes complete
    run_command("sync", check=True)
    
    print_status("Drive wipe complete!")

def hash_password(password):
    """Hash password using SHA-512 for cloud-init."""
    import secrets
    import string
    
    # Generate a random salt (16 characters)
    salt_chars = string.ascii_letters + string.digits + './'
    salt = ''.join(secrets.choice(salt_chars) for _ in range(16))
    
    # Use openssl to create the hash (more reliable than Python crypt module)
    try:
        result = subprocess.run(
            ['openssl', 'passwd', '-6', '-salt', salt, password],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Fallback: use mkpasswd if available, otherwise use a placeholder
        try:
            result = subprocess.run(
                ['mkpasswd', '--method=sha-512', '--salt=' + salt, password],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            print_error("Failed to hash password. Ensure openssl or mkpasswd is installed.")
            sys.exit(1)

def load_custom_scripts():
    """Load custom scripts from custom-scripts/ directory."""
    custom_scripts_dir = Path("custom-scripts")
    scripts = []
    
    if not custom_scripts_dir.exists():
        return scripts
    
    # Find all .sh files and sort them
    script_files = sorted(custom_scripts_dir.glob("*.sh"))
    
    for script_file in script_files:
        if script_file.name == "README.md":
            continue
        try:
            content = script_file.read_text()
            scripts.append({
                'name': script_file.name,
                'content': content,
                'path': f'/opt/setup-scripts/{script_file.name}'
            })
        except Exception as e:
            print_warning(f"Could not read script {script_file}: {e}")
    
    return scripts

def create_cloud_init(username, password, ssh_key='', ubuntu_pro_token=''):
    """Create cloud-init configuration files."""
    print_status("Creating cloud-init configuration...")
    
    TEMP_DIR.mkdir(exist_ok=True)
    
    password_hash = hash_password(password)
    
    # Load custom scripts
    custom_scripts = load_custom_scripts()
    if custom_scripts:
        print_status(f"Found {len(custom_scripts)} custom script(s) to include")
    
    # Build SSH authorized keys section
    ssh_keys_section = ""
    if ssh_key:
        print_status("Adding SSH public key to authorized_keys")
        ssh_keys_section = f"    ssh_authorized_keys:\n      - {ssh_key}"
    else:
        ssh_keys_section = "    ssh_authorized_keys: []"
    
    # Build write_files section for custom scripts
    write_files_section = ""
    if custom_scripts:
        write_files_section = "write_files:\n"
        for script in custom_scripts:
            # Encode script content with proper YAML multiline
            write_files_section += f"  - path: {script['path']}\n"
            write_files_section += f"    permissions: '0755'\n"
            write_files_section += f"    content: |\n"
            # Indent content
            for line in script['content'].split('\n'):
                write_files_section += f"      {line}\n"
    
    # Build runcmd section
    runcmd_list = [
        'echo "Ubuntu Server installation complete!" > /var/log/setup-complete.log',
        'mkdir -p /opt/setup-scripts',
        'sed -i \'s/^#*PermitRootLogin.*/PermitRootLogin no/\' /etc/ssh/sshd_config',
        'sed -i \'s/^#*PasswordAuthentication.*/PasswordAuthentication yes/\' /etc/ssh/sshd_config',
        'systemctl enable ssh',
        'systemctl start ssh',
        'systemctl restart sshd'
    ]

    # Export Ubuntu Pro token for custom scripts if provided
    if ubuntu_pro_token:
        runcmd_list.insert(0, f'export UBUNTU_PRO_TOKEN="{ubuntu_pro_token}"')
    
    # Add custom script execution commands
    if custom_scripts:
        runcmd_list.append('echo "Running custom setup scripts..." >> /var/log/setup-complete.log')
        for script in custom_scripts:
            runcmd_list.append(f'bash {script["path"]} || echo "Script {script["name"]} failed" >> /var/log/setup-complete.log')
        runcmd_list.append('echo "Custom scripts complete" >> /var/log/setup-complete.log')
    
    # Format runcmd as YAML
    runcmd_section = "runcmd:\n"
    for cmd in runcmd_list:
        runcmd_section += f"  - {cmd}\n"
    
    # Create user-data file
    user_data = f"""#cloud-config
hostname: raspberrypi
manage_etc_hosts: true

users:
  - name: {username}
    groups: sudo, adm
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    passwd: {password_hash}
    lock_passwd: false
{ssh_keys_section}

chpasswd:
  expire: false

packages:
  - ubuntu-server
  - openssh-server
  - net-tools
  - vim
  - curl
  - wget
  - htop
  - iotop
  - nvme-cli
  - linux-raspi
  - git
  - build-essential
  - tcpdump
  - neovim
  - podman
  - zip
  - unzip
  - rsync
  - bc
  - bison
  - flex
  - libssl-dev
  - libncurses-dev
  - pkg-config
  - dwarves
  - zstd

package_update: true
package_upgrade: true

{write_files_section}
{runcmd_section}
power_state:
  mode: reboot
  message: Installation complete, rebooting...
  timeout: 30
"""
    
    # Create meta-data file
    meta_data = """instance-id: raspberrypi-ubuntu
local-hostname: raspberrypi
"""
    
    # Create network-config file
    network_config = """version: 2
ethernets:
  eth0:
    dhcp4: true
    optional: true
  enx*:
    dhcp4: true
    optional: true
"""
    
    # Write files
    (TEMP_DIR / 'user-data').write_text(user_data)
    (TEMP_DIR / 'meta-data').write_text(meta_data)
    (TEMP_DIR / 'network-config').write_text(network_config)
    
    print_status("Cloud-init configuration created!")

def write_image(ubuntu_img):
    """Write Ubuntu image to NVMe drive with cloud-init."""
    print_status(f"Writing Ubuntu image to {NVME_DEVICE}...")
    
    if not ubuntu_img.exists():
        print_error(f"Ubuntu image not found at {ubuntu_img}")
        sys.exit(1)
    
    # Write the image to the drive
    print_status("Writing image (this may take several minutes)...")
    run_command(f"dd if='{ubuntu_img}' of='{NVME_DEVICE}' bs=4M status=progress conv=fsync", 
                check=True)
    
    # Sync to ensure all writes complete
    run_command("sync", check=True)
    
    print_status("Base image written successfully!")
    
    # Mount the boot partition and add cloud-init files
    print_status("Setting up cloud-init configuration...")
    
    boot_mount = TEMP_DIR / 'boot'
    boot_mount.mkdir(exist_ok=True)
    
    try:
        # Mount the boot partition (first partition)
        boot_partition = f"{NVME_DEVICE}p1"
        run_command(f"mount '{boot_partition}' '{boot_mount}'", check=True)
        
        # Copy cloud-init files to boot partition
        # Ubuntu Server uses cloud-init which reads these files on first boot
        # Files must be in the root of the boot partition (FAT32)
        shutil.copy(TEMP_DIR / 'user-data', boot_mount / 'user-data')
        shutil.copy(TEMP_DIR / 'meta-data', boot_mount / 'meta-data')
        shutil.copy(TEMP_DIR / 'network-config', boot_mount / 'network-config')
        
        # Create marker file to ensure cloud-init runs
        # This tells cloud-init to process the user-data on next boot
        (boot_mount / 'user-data').touch()
        
        # Unmount
        run_command("sync", check=True)
        run_command(f"umount '{boot_mount}'", check=True)
        
        print_status("Cloud-init configuration installed on boot partition!")
        
    except Exception as e:
        print_error(f"Failed to setup cloud-init: {e}")
        # Try to unmount even if there was an error
        run_command(f"umount '{boot_mount}' 2>/dev/null || true", check=False)
        sys.exit(1)

def verify_installation():
    """Verify the installation."""
    print_status("Verifying installation...")
    
    # Check partitions were created
    try:
        output = run_command(f"fdisk -l '{NVME_DEVICE}'", capture_output=True)
        if output and isinstance(output, str) and 'Linux' in output:
            print_status("Linux partitions found on NVMe drive")
        else:
            print_warning("No Linux partitions detected - installation may have failed")
    except:
        print_warning("Could not verify partitions")
    
    print_status("Installation complete!")
    print_status("The Raspberry Pi will boot from NVMe on next restart.")
    print_status("")
    print_status("IMPORTANT: Remove the SD card before rebooting to boot from NVMe!")

def main():
    print_status("=" * 50)
    print_status("Raspberry Pi 5 NVMe Ubuntu Setup Script")
    print_status("=" * 50)
    print()

    try:
        check_root()
        username, password, ssh_key, ubuntu_pro_token = load_credentials()

        # Export Ubuntu Pro token so custom scripts can use it
        if ubuntu_pro_token:
            os.environ['UBUNTU_PRO_TOKEN'] = ubuntu_pro_token
            print_status("Ubuntu Pro token configured for real-time kernel")

        confirm_wipe()
        ubuntu_img = download_ubuntu()
        create_cloud_init(username, password, ssh_key, ubuntu_pro_token)
        wipe_drive()
        write_image(ubuntu_img)
        verify_installation()

        print_status("")
        print_status("Setup complete! You can now:")
        print_status("1. Shutdown the Pi: sudo shutdown now")
        print_status("2. Remove the SD card")
        print_status("3. Power on to boot from NVMe")
        print_status(f"4. Login with username: {username}")
        
    except KeyboardInterrupt:
        print("\n")
        print_error("Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
