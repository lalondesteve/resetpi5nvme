#!/bin/bash
# Example custom setup script
# This runs during the unattended installation

set -e  # Exit on error

echo "$(date): Starting custom setup..." >> /var/log/custom-setup.log

# Example: Install Docker (uncomment if needed)
# apt-get update
# apt-get install -y docker.io docker-compose
# usermod -aG docker $USERNAME

# Example: Configure timezone
timedatectl set-timezone America/New_York

# Example: Enable automatic security updates
apt-get install -y unattended-upgrades

# Example: Custom MOTD
cat > /etc/update-motd.d/99-custom << 'EOF'
#!/bin/bash
echo ""
echo "==================================="
echo "  Ubuntu Server on Raspberry Pi 5"
echo "==================================="
echo ""
EOF
chmod +x /etc/update-motd.d/99-custom

echo "$(date): Custom setup complete!" >> /var/log/custom-setup.log
