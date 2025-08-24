# nickicker
Daemon to run on remote systems and attempt to recover from failed Internet connections

This daemon runs in the background on systems and periodically pings various remote endpoints to monitor the health of its Internet connection and respond accordingly.

## Features

- **Network Monitoring**: Continuously monitors connectivity to configured endpoints
- **Configurable Endpoints**: Support for multiple IP addresses (IPv4 and IPv6)
- **Flexible Timing**: Configurable test intervals and outage thresholds
- **Action System**: Execute actions when connectivity issues are detected
- **Systemd Integration**: Runs as a systemd service with automatic restart
- **Comprehensive Logging**: Detailed logging to both file and systemd journal
- **Security**: Runs with appropriate security restrictions

## Installation

### Prerequisites

- Python 3.6 or higher
- systemd (for service management)
- root/sudo access for installation

### Quick Install

```bash
# Clone the repository
git clone <your-repo-url>
cd nickicker

# Install Python dependencies
pip3 install -r requirements.txt

# Install the daemon and service
sudo make install

# Enable and start the service
sudo systemctl --now enable nickickerd
```

### Manual Installation

If you prefer to install manually:

```bash
# Install Python dependencies
pip3 install PyYAML

# Copy the daemon script
sudo cp nickickerd.py /usr/local/bin/nickickerd
sudo chmod +x /usr/local/bin/nickickerd

# Copy the systemd service file
sudo cp nickickerd.service /etc/systemd/system/

# Create log file
sudo touch /var/log/nickickerd.log
sudo chmod 644 /var/log/nickickerd.log

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl --now enable nickickerd
```

## Configuration

The configuration file is located at `/etc/nickicker.conf` and uses YAML format. A sample configuration file is provided as `nickicker.conf.example`.

### Basic Configuration

```yaml
---
# List of endpoints to test for connectivity
endpoints:
  - name: a.root-servers.net
    addresses:
      - 198.41.0.4
      - 2001:503:ba3e::2:30
  
  - name: google-dns
    addresses:
      - 8.8.8.8
      - 8.8.4.4

# How often to test connectivity
test_interval: 30m

# How long to wait before considering it an outage
outage_threshold: 2h

# Actions to take when outage threshold is reached
actions:
  - logbundle
  # - reboot  # Uncomment to enable reboot action
  # - email   # Uncomment to enable email alerts
```

### Configuration Options

- **endpoints**: List of endpoints to monitor
  - **name**: Human-readable name for the endpoint
  - **addresses**: List of IP addresses to test (IPv4 and IPv6 supported)
- **test_interval**: How often to test connectivity (e.g., `30s`, `5m`, `1h`)
- **outage_threshold**: How long to wait before executing actions (e.g., `5m`, `1h`, `2h`)
- **actions**: List of actions to execute when outage threshold is reached
  - `logbundle`: Create a compressed log bundle for troubleshooting
  - `reboot`: Reboot the system (use with caution!)
  - `email`: Send email alert (placeholder - implement as needed)

## Usage

### Service Management

```bash
# Start the service
sudo systemctl start nickickerd

# Stop the service
sudo systemctl stop nickickerd

# Restart the service
sudo systemctl restart nickickerd

# Check service status
sudo systemctl status nickickerd

# View service logs
sudo journalctl -u nickickerd -f

# Enable/disable automatic startup
sudo systemctl enable nickickerd
sudo systemctl disable nickickerd
```

### Manual Testing

Test the daemon in foreground mode for debugging:

```bash
# Test with default configuration
sudo python3 nickickerd.py --foreground

# Test with custom configuration
sudo python3 nickickerd.py --foreground --config /path/to/config.conf
```

### Makefile Commands

```bash
# Install the daemon and service
sudo make install

# Uninstall everything
sudo make uninstall

# Test the daemon in foreground mode
make test

# Check service status and recent logs
make status

# Clean up Python cache files
make clean
```

## Logging

The daemon logs to multiple locations:

- **File**: `/var/log/nickickerd.log`
- **Systemd Journal**: `journalctl -u nickickerd`
- **Console**: When running in foreground mode

Log levels include:
- `INFO`: Normal operation and status updates
- `WARNING`: Connectivity issues detected
- `ERROR`: Errors in operation
- `DEBUG`: Detailed debugging information

## Troubleshooting

### Common Issues

1. **Service won't start**
   - Check if Python dependencies are installed: `pip3 install PyYAML`
   - Verify the daemon script is executable: `ls -la /usr/local/bin/nickickerd`
   - Check systemd logs: `journalctl -u nickickerd -n 50`

2. **Permission denied errors**
   - Ensure the service is running as root (required for ping operations)
   - Check log file permissions: `ls -la /var/log/nickickerd.log`

3. **Configuration errors**
   - Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('/etc/nickicker.conf'))"`
   - Check configuration file permissions: `ls -la /etc/nickicker.conf`

### Debug Mode

Run the daemon in foreground mode to see detailed output:

```bash
sudo python3 nickickerd.py --foreground --config /etc/nickicker.conf
```

### Log Analysis

```bash
# View recent logs
tail -f /var/log/nickickerd.log

# Search for specific events
grep "Connectivity issues detected" /var/log/nickickerd.log

# View systemd logs
journalctl -u nickickerd --since "1 hour ago"
```

## Security Considerations

- The daemon runs as root to access ping functionality
- Security restrictions are applied via systemd service file
- PrivateTmp, ProtectSystem, and other security measures are enabled
- Resource limits are set to prevent abuse

## Development

### Project Structure

```
nickicker/
├── nickickerd.py          # Main daemon script
├── nickickerd.service     # systemd service file
├── Makefile               # Installation and management
├── requirements.txt       # Python dependencies
├── nickicker.conf.example # Sample configuration
└── README.md             # This file
```

### Adding New Actions

To add new actions, modify the `_execute_actions` method in the `NickickerDaemon` class:

```python
def _execute_actions(self, actions: List[str]):
    for action in actions:
        try:
            if action == 'logbundle':
                self._create_log_bundle()
            elif action == 'reboot':
                self._reboot_system()
            elif action == 'email':
                self._send_email_alert()
            elif action == 'custom_action':
                self._custom_action()  # Add your custom action here
            else:
                self.logger.warning(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
```

## License

This project is licensed under the terms specified in the LICENSE file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the logs for error messages
- Open an issue on the project repository