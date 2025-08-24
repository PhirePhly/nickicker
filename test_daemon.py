#!/usr/bin/env python3
"""
Simple test script for nickickerd functionality.
This script tests the core functionality without running as a daemon.
"""

import sys
import os
import tempfile
import yaml
from pathlib import Path

# Add the current directory to Python path to import nickickerd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nickickerd import NickickerDaemon


def create_test_config():
    """Create a temporary test configuration file."""
    config = {
        'endpoints': [
            {
                'name': 'test-endpoint-1',
                'addresses': ['127.0.0.1']  # Localhost for testing
            },
            {
                'name': 'test-endpoint-2',
                'addresses': ['8.8.8.8']  # Google DNS for real testing
            }
        ],
        'test_interval': '10s',
        'outage_threshold': '30s',
        'actions': ['logbundle']
    }
    
    # Create temporary config file
    fd, config_path = tempfile.mkstemp(suffix='.conf', prefix='nickicker_test_')
    with os.fdopen(fd, 'w') as f:
        yaml.dump(config, f)
    
    return config_path


def test_daemon_basic():
    """Test basic daemon functionality."""
    print("Testing basic daemon functionality...")
    
    # Create test config
    config_path = create_test_config()
    print(f"Created test config at: {config_path}")
    
    try:
        # Create daemon instance
        daemon = NickickerDaemon(config_path)
        print("✓ Daemon instance created successfully")
        
        # Test configuration loading
        print(f"✓ Configuration loaded: {len(daemon.config.get('endpoints', []))} endpoints")
        
        # Test time parsing
        test_interval = daemon._parse_time_interval('30m')
        assert test_interval == 1800, f"Expected 1800, got {test_interval}"
        print("✓ Time interval parsing works correctly")
        
        # Test endpoint structure
        endpoints = daemon.config.get('endpoints', [])
        assert len(endpoints) == 2, f"Expected 2 endpoints, got {len(endpoints)}"
        print("✓ Endpoint configuration structure is correct")
        
        print("✓ All basic tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(config_path)
            print(f"Cleaned up test config: {config_path}")
        except:
            pass
    
    return True


def test_connectivity():
    """Test connectivity testing functionality."""
    print("\nTesting connectivity functionality...")
    
    config_path = create_test_config()
    
    try:
        daemon = NickickerDaemon(config_path)
        
        # Test connectivity to localhost (should always work)
        localhost_endpoint = {
            'name': 'localhost',
            'addresses': ['127.0.0.1']
        }
        
        result = daemon._test_connectivity(localhost_endpoint)
        if result:
            print("✓ Localhost connectivity test passed")
        else:
            print("✗ Localhost connectivity test failed")
        
        # Test the overall connectivity test
        overall_result = daemon._test_all_endpoints()
        print(f"✓ Overall connectivity test completed: {overall_result}")
        
        print("✓ Connectivity tests completed!")
        
    except Exception as e:
        print(f"✗ Connectivity test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass
    
    return True


def main():
    """Run all tests."""
    print("nickickerd Test Suite")
    print("=" * 50)
    
    tests = [
        test_daemon_basic,
        test_connectivity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The daemon is ready for use.")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
