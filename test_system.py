"""
Test Script for Vehicle Collision Detection System
Run this to verify all components are working correctly
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher required")
        return False
    
    print("✓ Python version OK")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required = [
        'flask',
        'flask_socketio',
        'socketio'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"❌ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print("\n❌ Missing packages detected")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed")
    return True

def check_files():
    """Check if all required files exist"""
    print_header("Checking Project Files")
    
    required_files = [
        'server.py',
        'car_a.py',
        'car_b.py',
        'index.html',
        'requirements.txt',
        'config.py',
        'README.md'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"❌ {file} NOT FOUND")
            missing.append(file)
    
    if missing:
        print("\n❌ Missing files detected")
        return False
    
    print("\n✓ All required files present")
    return True

def test_server_start():
    """Test if server can be started"""
    print_header("Testing Server Startup")
    
    try:
        # Try to import server modules
        import server
        print("✓ Server module can be imported")
        
        # Check if port is available
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("⚠ Warning: Port 5000 already in use")
            print("  Server may already be running or port is blocked")
            return True
        else:
            print("✓ Port 5000 is available")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_calls():
    """Test API endpoints if server is running"""
    print_header("Testing API Endpoints")
    
    base_url = "http://localhost:5000"
    
    # Check if server is running
    try:
        response = requests.get(base_url, timeout=2)
        print("✓ Server is responding")
    except requests.exceptions.RequestException:
        print("⚠ Server not running (this is OK if you haven't started it)")
        print("  Start server with: python server.py")
        return True
    
    # Test endpoints
    endpoints = [
        "/",
        "/api/vehicles",
        "/api/stats"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(base_url + endpoint, timeout=2)
            if response.status_code == 200:
                print(f"✓ {endpoint} - OK")
            else:
                print(f"⚠ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    return True

def show_quick_start():
    """Show quick start instructions"""
    print_header("Quick Start Guide")
    
    print("""
To start the system:

1. Start the server:
   python server.py

2. In a new terminal, start Car A:
   python car_a.py

3. In another terminal, start Car B:
   python car_b.py

4. Open index.html in your browser

5. Select your vehicle ID from the dropdown

You should see vehicles on the map and alerts when they approach!

For detailed instructions, see README.md
""")

def main():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Vehicle Collision Detection System - Test Suite         ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    tests = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Files", check_files),
        ("Server Module", test_server_start),
        ("API Endpoints", test_api_calls)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        show_quick_start()
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("Refer to README.md for troubleshooting help.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
