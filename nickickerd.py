#!/usr/bin/env python3
"""
nickickerd - Network connectivity monitoring daemon

This daemon runs in the background and periodically pings various remote endpoints
to monitor the health of its Internet connection and respond accordingly.
"""

import os
import sys
import time
import signal
import logging
import yaml
import subprocess
import socket
from pathlib import Path
from typing import Dict, List, Any
import argparse


class NickickerDaemon:
    """Main daemon class for network connectivity monitoring."""
    
    def __init__(self, config_path: str = "/etc/nickicker.conf"):
        self.config_path = config_path
        self.config = {}
        self.running = False
        self.logger = self._setup_logging()
        
        # Load configuration
        self._load_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('nickickerd')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler
        log_file = "/var/log/nickickerd.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self.config = self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is not available."""
        return {
            'endpoints': [
                {
                    'name': 'a.root-servers.net',
                    'addresses': ['198.41.0.4', '2001:503:ba3e::2:30']
                },
                {
                    'name': 'b.root-servers.net',
                    'addresses': ['170.247.170.2', '2801:1b8:10::b']
                }
            ],
            'test_interval': '30m',
            'outage_threshold': '2h',
            'actions': ['logbundle']
        }
    
    def _parse_time_interval(self, interval_str: str) -> int:
        """Parse time interval string (e.g., '30m', '2h') to seconds."""
        if interval_str.endswith('m'):
            return int(interval_str[:-1]) * 60
        elif interval_str.endswith('h'):
            return int(interval_str[:-1]) * 3600
        elif interval_str.endswith('s'):
            return int(interval_str[:-1])
        else:
            return int(interval_str)
    
    def _test_connectivity(self, endpoint: Dict[str, Any]) -> bool:
        """Test connectivity to a specific endpoint."""
        name = endpoint.get('name', 'unknown')
        addresses = endpoint.get('addresses', [])
        
        for address in addresses:
            try:
                # Try to ping the address
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '5', address],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.debug(f"Successfully pinged {name} ({address})")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        self.logger.warning(f"Failed to ping {name} ({addresses})")
        return False
    
    def _test_all_endpoints(self) -> bool:
        """Test connectivity to all configured endpoints."""
        endpoints = self.config.get('endpoints', [])
        if not endpoints:
            self.logger.warning("No endpoints configured")
            return False
        
        successful_tests = 0
        total_tests = len(endpoints)
        
        for endpoint in endpoints:
            if self._test_connectivity(endpoint):
                successful_tests += 1
        
        success_rate = successful_tests / total_tests
        self.logger.info(f"Connectivity test: {successful_tests}/{total_tests} endpoints reachable")
        
        # Consider connection healthy if at least 40% of endpoints are reachable
        return success_rate >= 0.4
    
    def _execute_actions(self, actions: List[str]):
        """Execute configured actions when connectivity issues are detected."""
        for action in actions:
            try:
                if action == 'logbundle':
                    self._create_log_bundle()
                elif action == 'reboot':
                    self.logger.warning("Reboot action requested - use with caution")
                    subprocess.run(['reboot'])
                elif action == 'email':
                    self._send_email_alert()
                else:
                    self.logger.warning(f"Unknown action: {action}")
            except Exception as e:
                self.logger.error(f"Error executing action {action}: {e}")
    
    def _create_log_bundle(self):
        """Create a log bundle for troubleshooting."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            bundle_path = f"/tmp/nickicker_logs_{timestamp}.tar.gz"
            
            # Collect relevant logs and system information
            log_files = [
                "/var/log/nickickerd.log",
                "/var/log/messages",
                "/var/log/syslog"
            ]
            
            # Create tar.gz bundle
            cmd = ['tar', '-czf', bundle_path]
            for log_file in log_files:
                if os.path.exists(log_file):
                    cmd.append(log_file)
            
            if len(cmd) > 3:  # More than just tar command
                subprocess.run(cmd, check=True)
                self.logger.info(f"Log bundle created: {bundle_path}")
            else:
                self.logger.warning("No log files found to bundle")
                
        except Exception as e:
            self.logger.error(f"Error creating log bundle: {e}")
    
    def _send_email_alert(self):
        """Send email alert about connectivity issues."""
        # This is a placeholder - implement based on your email requirements
        self.logger.info("Email alert would be sent here")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main daemon loop."""
        self.logger.info("nickickerd starting up...")
        self.running = True
        
        # Parse intervals
        test_interval = self._parse_time_interval(self.config.get('test_interval', '30m'))
        outage_threshold = self._parse_time_interval(self.config.get('outage_threshold', '2h'))
        
        last_test_time = time.time()
        consecutive_failures = 0
        last_success_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time to test connectivity
                if current_time - last_test_time >= test_interval:
                    self.logger.debug("Running connectivity test...")
                    
                    if self._test_all_endpoints():
                        # Connection is healthy
                        consecutive_failures = 0
                        last_success_time = current_time
                        self.logger.info("Network connectivity is healthy")
                    else:
                        # Connection issues detected
                        consecutive_failures += 1
                        outage_duration = current_time - last_success_time
                        
                        self.logger.warning(
                            f"Connectivity issues detected. "
                            f"Consecutive failures: {consecutive_failures}, "
                            f"Outage duration: {outage_duration:.0f}s"
                        )
                        
                        # Check if we should execute actions
                        if outage_duration >= outage_threshold:
                            actions = self.config.get('actions', [])
                            if actions:
                                self.logger.warning(f"Executing actions: {actions}")
                                self._execute_actions(actions)
                    
                    last_test_time = current_time
                
                # Sleep for a short interval
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)
        
        self.logger.info("nickickerd shutting down...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='nickickerd - Network connectivity monitoring daemon')
    parser.add_argument(
        '--config', '-c',
        default='/etc/nickicker.conf',
        help='Path to configuration file (default: /etc/nickicker.conf)'
    )
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run in foreground (for debugging)'
    )
    
    args = parser.parse_args()
    
    # Create and run daemon
    daemon = NickickerDaemon(args.config)
    
    if args.foreground:
        daemon.run()
    else:
        # Daemonize
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                sys.exit(0)
            
            # Child process
            os.chdir('/')
            os.umask(0)
            os.setsid()
            
            # Fork again to detach from terminal
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
            
            # Write PID file
            with open('/var/run/nickickerd.pid', 'w') as f:
                f.write(str(os.getpid()))
            
            # Run daemon
            daemon.run()
            
        except OSError as e:
            sys.stderr.write(f"Failed to daemonize: {e}\n")
            sys.exit(1)


if __name__ == '__main__':
    main()
