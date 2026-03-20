# PREEMPT_RT (Real-Time) Kernel on Raspberry Pi 5

This document explains how to enable the PREEMPT_RT kernel using Ubuntu Pro for Raspberry Pi 5.

## What is PREEMPT_RT?

PREEMPT_RT is a set of patches for the Linux kernel that make it fully preemptible. This means:

- **Lower latency**: Interrupt handlers and critical sections can be preempted
- **Better real-time performance**: More deterministic response times
- **Reduced jitter**: More consistent timing for time-sensitive tasks

## Use Cases

PREEMPT_RT is beneficial for:

- **Robotics**: Precise motor control, sensor reading
- **Audio Processing**: Low-latency audio I/O, digital audio workstations
- **Industrial Control**: PLC-like applications, CNC machines
- **Telecommunications**: Real-time packet processing
- **Scientific Instruments**: Data acquisition with precise timing

## Recommended Method: Ubuntu Pro (Official)

The **easiest and most reliable** way to get a PREEMPT_RT kernel on Raspberry Pi 5 is through **Ubuntu Pro**.

### What is Ubuntu Pro?

Ubuntu Pro is Canonical's extended security and compliance subscription. For **personal use**, it's **free** for up to 5 machines.

### Benefits of Ubuntu Pro RT Kernel:

- ✅ **Official support** from Canonical
- ✅ **Pre-built** for Raspberry Pi (`--variant=raspi`)
- ✅ **Automatic updates** and security patches
- ✅ **No compilation** required
- ✅ **Commercial support** available
- ✅ **FIPS compliance** options

### How to Enable

1. **Get a free Ubuntu Pro token:**
   - Visit: https://ubuntu.com/pro
   - Sign up for a free personal subscription
   - Copy your token

2. **During setup:**
   ```bash
   python3 setup.py
   # Paste your Ubuntu Pro token when prompted
   ```

3. **The installer will automatically:**
   - Attach your Ubuntu Pro subscription
   - Install ubuntu-advantage-tools
   - Enable the real-time kernel: `pro enable realtime-kernel --variant=raspi`
   - Configure the system to boot with the RT kernel

4. **After first boot, verify:**
   ```bash
   # Check kernel version (should contain "rt")
   uname -r
   # Output: 6.8.0-1006-raspi-realtime or similar

   # Verify PREEMPT_RT is enabled
   grep CONFIG_PREEMPT_RT /boot/config-$(uname -r)
   # Output: CONFIG_PREEMPT_RT=y

   # Check Ubuntu Pro status
   pro status
   ```

### Manual Enable (If Not Done During Install)

If you skipped the token during setup, you can enable it later:

```bash
# Attach Ubuntu Pro
sudo pro attach <your-token>

# Enable real-time kernel for Raspberry Pi
sudo pro enable realtime-kernel --variant=raspi

# Reboot to use the new kernel
sudo reboot
```

## Verification

After installation and reboot, verify the RT kernel is active:

```bash
# Check kernel version (should contain "rt" or "realtime")
$ uname -r
6.8.0-1006-raspi-realtime

# Check kernel config for PREEMPT_RT
$ grep CONFIG_PREEMPT_RT /boot/config-$(uname -r)
CONFIG_PREEMPT_RT=y

# Check preemption model
$ zcat /proc/config.gz | grep PREEMPT
CONFIG_PREEMPT_RT=y
CONFIG_PREEMPT_COUNT=y
CONFIG_PREEMPTION=y

# Check Ubuntu Pro services
$ pro status
SERVICE          ENTITLED  STATUS    DESCRIPTION
cis              yes       disabled  Security compliance and audit tools
esm-apps         yes       enabled   Expanded Security Maintenance for Applications
esm-infra        yes       enabled   Expanded Security Maintenance for Infrastructure
realtime-kernel  yes       enabled   Ubuntu kernel with PREEMPT_RT patches integrated
```

## Performance Tuning

After installing the RT kernel, you may want to tune the system for better real-time performance:

### 1. CPU Frequency Scaling

Set CPU governor to performance:

```bash
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
```

### 2. Disable Unnecessary Interrupts

```bash
# Check which interrupts are active
cat /proc/interrupts

# Disable unnecessary services
sudo systemctl disable bluetooth  # if not needed
sudo systemctl disable wifi-hotspot  # if not needed
```

### 3. Real-Time Priority for Critical Tasks

Use `chrt` to set real-time scheduling:

```bash
# Run a process with FIFO real-time priority 80
sudo chrt -f 80 ./your-realtime-app
```

### 4. CPU Isolation

Isolate CPUs for real-time tasks in `/boot/firmware/cmdline.txt`:

```
isolcpus=2,3
```

This isolates CPUs 2 and 3 from the general scheduler.

## Troubleshooting

### Ubuntu Pro Token Issues

If attachment fails:

```bash
# Check your token is valid
sudo pro attach --dry-run <your-token>

# Check service status
pro status --all

# View logs
sudo journalctl -u ubuntu-advantage
```

### System Won't Boot with RT Kernel

If the RT kernel causes boot failures:

1. Boot while holding Shift to enter GRUB menu
2. Select "Advanced options for Ubuntu"
3. Choose the standard (non-RT) kernel
4. Once booted, disable RT kernel:
   ```bash
   sudo pro disable realtime-kernel
   sudo reboot
   ```

### Real-Time Kernel Not Working

If the RT kernel is installed but not active:

```bash
# Check which kernel is currently running
uname -r

# Check installed kernels
dpkg -l | grep linux-image

# Update GRUB to ensure RT kernel is selected
sudo update-grub
```

### High Latency Despite RT Kernel

- Check for SMI (System Management Interrupts) - can only be disabled in BIOS/UEFI
- Ensure CPU governor is set to performance
- Check for competing high-priority processes
- Verify no debug features are enabled in kernel config

## Alternative: Manual Compilation

If you cannot use Ubuntu Pro, you can manually compile the RT kernel. This is **not recommended** as it's complex and requires ongoing maintenance.

See the archived instructions in this repository's git history if needed, but strongly consider using Ubuntu Pro instead.

## References

- [Ubuntu Real-Time Kernel](https://ubuntu.com/realtime-kernel)
- [Ubuntu Pro](https://ubuntu.com/pro)
- [Ubuntu Pro for Raspberry Pi](https://ubuntu.com/tutorials/how-to-enable-ubuntu-pro-on-raspberry-pi)
- [PREEMPT_RT Wiki](https://wiki.linuxfoundation.org/realtime/start)
- [Raspberry Pi Kernel Documentation](https://www.raspberrypi.com/documentation/computers/linux_kernel.html)
- [Real-Time Ubuntu Whitepaper](https://ubuntu.com/download/whitepapers)

## License and Support

- **Ubuntu Pro personal use**: Free for up to 5 machines
- **Ubuntu Pro for enterprise**: Contact Canonical for pricing
- **Support**: Available through Ubuntu Pro subscription
