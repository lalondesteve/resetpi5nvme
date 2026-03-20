#!/bin/bash
# Install additional tools: nvm (Node Version Manager) and podman-compose

set -e

echo "$(date): Starting nvm and podman-compose installation..." >> /var/log/custom-setup.log

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a /var/log/custom-setup.log
}

# Install nvm (Node Version Manager)
log "Installing nvm (Node Version Manager)..."

# Create the nvm install script
cat > /tmp/install_nvm.sh << 'NVMSCRIPT'
#!/bin/bash
# Install nvm for all users or specific user

NVM_VERSION="v0.39.7"
INSTALL_USER="${1:-root}"

if [ "$INSTALL_USER" = "root" ]; then
    HOME_DIR="/root"
    BASH_RC="/root/.bashrc"
else
    HOME_DIR="/home/$INSTALL_USER"
    BASH_RC="$HOME_DIR/.bashrc"
fi

# Download and install nvm
curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" | bash

# Add nvm to shell configuration
if ! grep -q "NVM_DIR" "$BASH_RC" 2>/dev/null; then
    echo "" >> "$BASH_RC"
    echo "# NVM configuration" >> "$BASH_RC"
    echo 'export NVM_DIR="$HOME/.nvm"' >> "$BASH_RC"
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> "$BASH_RC"
    echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> "$BASH_RC"
fi

# Also add to /etc/profile.d for system-wide availability
cat > /etc/profile.d/nvm.sh << 'EOF'
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF

echo "nvm $NVM_VERSION installed successfully"
NVMSCRIPT

chmod +x /tmp/install_nvm.sh

# Install nvm for root
/tmp/install_nvm.sh root

# Source nvm and install latest LTS node
export NVM_DIR="/root/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

log "Installing latest LTS Node.js version..."
nvm install --lts
nvm use --lts
nvm alias default lts/*

log "nvm and Node.js LTS installed successfully"
log "Node version: $(node --version)"
log "npm version: $(npm --version)"

# Install podman-compose
log "Installing podman-compose..."

# Method 1: Try pip3 installation (most reliable)
if command -v pip3 &> /dev/null; then
    log "Installing podman-compose via pip3..."
    pip3 install podman-compose >> /var/log/custom-setup.log 2>&1 || {
        log "pip3 install failed, trying alternative methods..."
    }
fi

# Method 2: Check if installed, if not try other methods
if ! command -v podman-compose &> /dev/null; then
    log "Trying alternative installation methods for podman-compose..."
    
    # Try installing via apt (Ubuntu 22.04+ might have it)
    apt-get install -y podman-compose >> /var/log/custom-setup.log 2>&1 || {
        log "apt install failed, trying pip..."
        
        # Install pip if not present
        apt-get install -y python3-pip >> /var/log/custom-setup.log 2>&1
        
        # Try pip installation
        pip3 install podman-compose >> /var/log/custom-setup.log 2>&1 || {
            log "WARNING: Could not install podman-compose automatically"
            log "You can manually install it later with: pip3 install podman-compose"
        }
    }
fi

# Verify podman-compose installation
if command -v podman-compose &> /dev/null; then
    log "podman-compose installed successfully"
    log "podman-compose version: $(podman-compose --version)"
else
    log "WARNING: podman-compose installation may have failed"
    log "Manual installation may be required"
fi

# Enable and verify podman
log "Configuring podman..."
systemctl enable podman.socket >> /var/log/custom-setup.log 2>&1 || true
systemctl start podman.socket >> /var/log/custom-setup.log 2>&1 || true

# Add user to podman group if needed
if [ -n "$USERNAME" ]; then
    usermod -aG podman "$USERNAME" 2>/dev/null || true
    usermod -aG users "$USERNAME" 2>/dev/null || true
fi

# Create symlink for docker compatibility (optional)
if [ ! -e /usr/local/bin/docker ]; then
    ln -s $(which podman) /usr/local/bin/docker 2>/dev/null || true
    log "Created docker symlink pointing to podman"
fi

if [ ! -e /usr/local/bin/docker-compose ]; then
    ln -s $(which podman-compose) /usr/local/bin/docker-compose 2>/dev/null || true
    log "Created docker-compose symlink pointing to podman-compose"
fi

log "podman and podman-compose setup complete"

echo "$(date): nvm and podman-compose installation complete!" >> /var/log/custom-setup.log
