#!/usr/bin/env python3
"""
Setup script for Raspberry Pi 5 NVMe Ubuntu installation.
This script asks for credentials and stores them securely (not in git).
"""

import os
import sys
import stat
import re
from getpass import getpass

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

def validate_username(username):
    """Validate username format."""
    if not username:
        return False, "Username cannot be empty"
    if not re.match(r'^[a-z][a-z0-9_-]*$', username):
        return False, "Username must start with a letter and can only contain lowercase letters, numbers, hyphens, and underscores"
    if len(username) > 32:
        return False, "Username must be 32 characters or less"
    return True, "Valid"

def validate_ssh_key(key):
    """Validate SSH public key format."""
    if not key:
        return True, "Empty (will be skipped)"
    
    # Common SSH key types
    valid_types = ['ssh-rsa', 'ssh-ed25519', 'ssh-dss', 'ecdsa-sha2-nistp256', 
                   'ecdsa-sha2-nistp384', 'ecdsa-sha2-nistp521', 'sk-ssh-ed25519',
                   'sk-ecdsa-sha2-nistp256']
    
    key_parts = key.strip().split()
    if len(key_parts) < 2:
        return False, "Invalid SSH key format. Expected: 'type key_data [comment]'"
    
    if key_parts[0] not in valid_types:
        return False, f"Unknown SSH key type. Valid types: {', '.join(valid_types)}"
    
    return True, "Valid"

def main():
    print_status("=" * 50)
    print_status("Raspberry Pi 5 NVMe Setup Configuration")
    print_status("=" * 50)
    print()
    
    env_file = '.env'
    
    # Check if .env already exists
    if os.path.exists(env_file):
        print_warning(".env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print_status("Keeping existing .env file.")
            sys.exit(0)
    
    # Get username
    while True:
        username = input("Enter username for Ubuntu installation: ").strip()
        valid, message = validate_username(username)
        if valid:
            break
        print_error(message)
    
    # Get password
    while True:
        password = getpass("Enter password for user '{}': ".format(username))
        if not password:
            print_error("Password cannot be empty")
            continue
        
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print_error("Passwords do not match!")
            continue
        
        # Check password length
        if len(password) < 8:
            print_warning("Password is less than 8 characters.")
            continue_anyway = input("Continue anyway? (y/N): ").strip().lower()
            if continue_anyway not in ['y', 'yes']:
                continue
        
        break
    
    # Get SSH public key
    print()
    print_status("SSH Public Key Configuration")
    print("Paste your SSH public key for passwordless SSH access.")
    print("Supported formats: ssh-rsa, ssh-ed25519, ecdsa-sha2-*")
    print("Leave empty to skip (you'll use password authentication)")
    print()
    
    while True:
        ssh_key = input("SSH Public Key: ").strip()
        valid, message = validate_ssh_key(ssh_key)
        if valid:
            break
        print_error(message)
    
    # Get Ubuntu Pro token for real-time kernel
    print()
    print_status("Ubuntu Pro Real-Time Kernel (Optional)")
    print("Ubuntu Pro provides an official PREEMPT_RT kernel for Raspberry Pi.")
    print("This enables real-time performance for robotics, audio processing, etc.")
    print()
    print("To enable:")
    print("  1. Get a free Ubuntu Pro token at: https://ubuntu.com/pro")
    print("  2. Paste the token below")
    print("  3. The real-time kernel will be installed automatically")
    print()
    print("Leave empty to skip (standard kernel will be used)")
    print()
    
    ubuntu_pro_token = input("Ubuntu Pro Token: ").strip()
    
    # Create .env file
    try:
        with open(env_file, 'w') as f:
            f.write("# Ubuntu Installation Credentials\n")
            f.write("# This file is gitignored and should NEVER be committed!\n")
            f.write(f'USERNAME="{username}"\n')
            f.write(f'PASSWORD="{password}"\n')
            if ssh_key:
                f.write(f'SSH_PUBLIC_KEY="{ssh_key}"\n')
            if ubuntu_pro_token:
                f.write(f'UBUNTU_PRO_TOKEN="{ubuntu_pro_token}"\n')
        
        # Set restrictive permissions (600 - owner read/write only)
        os.chmod(env_file, stat.S_IRUSR | stat.S_IWUSR)
        
        print_status("")
        print_status("Configuration saved to .env file")
        print_status("File permissions set to 600 (owner read/write only)")
        print_status("")
        print_status("You can now run: sudo python3 install_ubuntu.py")
        
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Setup cancelled by user")
        sys.exit(1)
