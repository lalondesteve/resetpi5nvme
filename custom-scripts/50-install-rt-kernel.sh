#!/bin/bash
# Install PREEMPT_RT (Real-Time) kernel using Ubuntu Pro
# This script runs during the unattended installation

set -e

echo "$(date): Starting PREEMPT_RT kernel installation via Ubuntu Pro..." >> /var/log/rt-kernel-setup.log

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a /var/log/rt-kernel-setup.log
}

# Check if Ubuntu Pro token is provided
if [ -z "$UBUNTU_PRO_TOKEN" ]; then
    log "Ubuntu Pro token not provided. Skipping RT kernel installation."
    log "To enable later: sudo pro enable realtime-kernel --variant=raspi"
    exit 0
fi

log "Ubuntu Pro token found. Enabling real-time kernel..."

# Install ubuntu-advantage-tools
log "Installing ubuntu-advantage-tools..."
apt-get update >> /var/log/rt-kernel-setup.log 2>&1
apt-get install -y ubuntu-advantage-tools >> /var/log/rt-kernel-setup.log 2>&1

# Attach Ubuntu Pro subscription
log "Attaching Ubuntu Pro subscription..."
pro attach "$UBUNTU_PRO_TOKEN" >> /var/log/rt-kernel-setup.log 2>&1 || {
    log "ERROR: Failed to attach Ubuntu Pro subscription"
    log "Please check your token at https://ubuntu.com/pro"
    exit 1
}

# Enable real-time kernel for Raspberry Pi
log "Enabling real-time kernel for Raspberry Pi..."
pro enable realtime-kernel --variant=raspi >> /var/log/rt-kernel-setup.log 2>&1 || {
    log "ERROR: Failed to enable real-time kernel"
    log "Your Ubuntu Pro subscription may not include real-time kernel support"
    exit 1
}

log "Real-time kernel installation initiated!"
log "The system will reboot with RT kernel after cloud-init completes"

# Verify installation
if systemctl is-active --quiet realtime-kernel 2>/dev/null || \
   apt list --installed 2>/dev/null | grep -q "linux-image.*rt"; then
    log "Real-time kernel package installed successfully"
else
    log "Note: RT kernel installation may complete after reboot"
fi

log "Ubuntu Pro real-time kernel setup complete!"
echo "$(date): PREEMPT_RT kernel installation complete!" >> /var/log/rt-kernel-setup.log
