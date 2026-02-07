"""
Real Car GPS Tracker using OBD-II Port
Reads GPS and vehicle data from car's OBD-II port

HARDWARE NEEDED:
- ELM327 Bluetooth or WiFi OBD-II adapter ($15-40)
- Available on Amazon: search "ELM327 OBD2 adapter"

WORKS WITH:
- Any car made after 1996 (has OBD-II port)
- Location: Under dashboard, near steering wheel
"""

import socketio
import time
import threading
from datetime import datetime

# OBD library
try:
    import obd
    OBD_AVAILABLE = True
except ImportError:
    OBD_AVAILABLE = False
    print("⚠️ obd library not installed!")
    print("Install with: pip install obd")

# Bluetooth library for ELM327
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("⚠️ pybluez not installed (needed for Bluetooth)")
    print("Install with: pip install pybluez")


class CarOBDTracker:
    """Track real car using OBD-II GPS data"""
    
    def __init__(self, vehicle_id: str, server_url: str = "http://localhost:5000"):
        self.vehicle_id = vehicle_id
        self.server_url = server_url
        
        # Car data
        self.lat = None
        self.lon = None
        self.speed = None  # km/h
        self.rpm = None
        self.throttle = None
        self.fuel_level = None
        self.engine_temp = None
        
        # OBD connection
        self.obd_connection = None
        self.running = False
        
        # Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1
        )
        
        self.setup_events()
    
    def setup_events(self):
        """Setup Socket.IO events"""
        @self.sio.event
        def connect():
            print(f"✅ Vehicle {self.vehicle_id} connected to server")
            
        @self.sio.event
        def disconnect():
            print(f"❌ Disconnected from server")
            
        @self.sio.event
        def error(data):
            print(f"⚠️ Error: {data}")
    
    def find_obd_adapter(self):
        """Automatically find OBD-II adapter"""
        print("🔍 Searching for OBD-II adapter...")
        
        # Try common Bluetooth OBD adapters
        if BLUETOOTH_AVAILABLE:
            print("   Scanning Bluetooth devices...")
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            
            for addr, name in nearby_devices:
                if 'OBD' in name.upper() or 'ELM' in name.upper():
                    print(f"   Found: {name} at {addr}")
                    return addr
        
        # Try USB/Serial connections
        print("   Trying USB/Serial connections...")
        ports = [
            '/dev/ttyUSB0',  # Linux
            '/dev/rfcomm0',  # Linux Bluetooth
            'COM3', 'COM4', 'COM5', 'COM6',  # Windows
        ]
        
        for port in ports:
            try:
                connection = obd.OBD(port)
                if connection.is_connected():
                    print(f"   ✅ Found OBD adapter on {port}")
                    return connection
            except:
                continue
        
        return None
    
    def connect_to_car(self, port=None):
        """Connect to car's OBD-II port"""
        if not OBD_AVAILABLE:
            print("❌ OBD library not installed!")
            print("   Install with: pip install obd")
            return False
        
        print("\n🚗 Connecting to car's OBD-II port...")
        
        try:
            if port:
                # Connect to specific port
                self.obd_connection = obd.OBD(port)
            else:
                # Auto-detect
                self.obd_connection = obd.OBD()  # Auto-connect
            
            if self.obd_connection.is_connected():
                print("✅ Connected to car!")
                print(f"   Protocol: {self.obd_connection.protocol_name()}")
                print(f"   Port: {self.obd_connection.port_name()}")
                
                # List available commands
                supported = self.obd_connection.supported_commands
                print(f"   Supported commands: {len(supported)}")
                
                # Check for GPS support
                if obd.commands.GPS in supported:
                    print("   ✅ GPS supported!")
                else:
                    print("   ⚠️ GPS not directly supported")
                    print("   Will use phone GPS fallback or external GPS")
                
                return True
            else:
                print("❌ Could not connect to OBD-II adapter")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def read_car_data(self):
        """Read data from car"""
        if not self.obd_connection or not self.obd_connection.is_connected():
            return
        
        try:
            # Read speed
            response = self.obd_connection.query(obd.commands.SPEED)
            if not response.is_null():
                self.speed = response.value.magnitude  # km/h
            
            # Read RPM
            response = self.obd_connection.query(obd.commands.RPM)
            if not response.is_null():
                self.rpm = response.value.magnitude
            
            # Read throttle position
            response = self.obd_connection.query(obd.commands.THROTTLE_POS)
            if not response.is_null():
                self.throttle = response.value.magnitude
            
            # Read fuel level
            response = self.obd_connection.query(obd.commands.FUEL_LEVEL)
            if not response.is_null():
                self.fuel_level = response.value.magnitude
            
            # Read engine temperature
            response = self.obd_connection.query(obd.commands.COOLANT_TEMP)
            if not response.is_null():
                self.engine_temp = response.value.magnitude
            
            # Try to read GPS if supported
            try:
                response = self.obd_connection.query(obd.commands.GPS)
                if not response.is_null():
                    # GPS data format varies by car
                    gps_data = response.value
                    if hasattr(gps_data, 'latitude'):
                        self.lat = gps_data.latitude
                        self.lon = gps_data.longitude
            except:
                # GPS not supported via OBD
                pass
            
            # Display car data
            print(f"🚗 Speed: {self.speed:.0f} km/h | "
                  f"RPM: {self.rpm:.0f} | "
                  f"Throttle: {self.throttle:.0f}% | "
                  f"Fuel: {self.fuel_level:.0f}%")
            
        except Exception as e:
            print(f"⚠️ Error reading car data: {e}")
    
    def read_gps_fallback(self):
        """
        Fallback GPS method if OBD doesn't provide GPS
        Uses phone GPS or external GPS module
        """
        # This would connect to your phone's GPS or external GPS
        # For now, placeholder
        print("ℹ️ Using fallback GPS (connect phone or GPS module)")
    
    def send_position_update(self):
        """Send car data to server"""
        if self.lat is None or self.lon is None:
            # No GPS data yet
            return
        
        try:
            data = {
                "vehicle_id": self.vehicle_id,
                "lat": self.lat,
                "lon": self.lon,
                "speed": self.speed if self.speed else 0,
                "altitude": 0,
                "accuracy": 10
            }
            
            self.sio.emit("vehicle_update", data)
            
            print(f"📤 Sent: {self.vehicle_id} | "
                  f"{self.lat:.6f}, {self.lon:.6f} | "
                  f"{self.speed:.0f} km/h")
            
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    def run(self, update_interval: float = 1.0, obd_port=None):
        """
        Main tracking loop
        
        Args:
            update_interval: Seconds between updates
            obd_port: Specific OBD port (None = auto-detect)
        """
        print("""
╔═══════════════════════════════════════════════════════════╗
║          🚗 Real Car OBD-II GPS Tracker                   ║
╚═══════════════════════════════════════════════════════════╝
""")
        
        # Connect to car
        if not self.connect_to_car(obd_port):
            print("\n❌ Could not connect to car!")
            print("\n📋 Troubleshooting:")
            print("   1. Is OBD-II adapter plugged in?")
            print("   2. Is car ignition ON?")
            print("   3. Is adapter paired (if Bluetooth)?")
            print("   4. Try: pip install obd")
            return
        
        # Connect to server
        print(f"\n🔌 Connecting to server: {self.server_url}")
        try:
            self.sio.connect(self.server_url, wait_timeout=10)
        except Exception as e:
            print(f"⚠️ Server connection failed: {e}")
            print("   Continuing anyway (data will be logged locally)")
        
        self.running = True
        
        print(f"\n✅ Tracking started!")
        print(f"🚗 Vehicle ID: {self.vehicle_id}")
        print(f"🔄 Update interval: {update_interval}s")
        print("\n⚠️ NOTE: Many cars don't provide GPS via OBD-II")
        print("   If no GPS data, use phone_gps_tracker.py instead")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while self.running:
                # Read car data
                self.read_car_data()
                
                # Send update if we have GPS
                if self.lat and self.lon:
                    self.send_position_update()
                else:
                    print("⚠️ No GPS data (car may not provide GPS via OBD-II)")
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Tracking stopped")
        finally:
            self.running = False
            if self.obd_connection:
                self.obd_connection.close()
            self.sio.disconnect()
            print("✅ Disconnected")


def main():
    """Main function"""
    
    # ============ CONFIGURATION ============
    
    VEHICLE_ID = "MY_CAR"
    SERVER_URL = "http://localhost:5000"
    
    # OBD Port (None = auto-detect)
    # Windows: 'COM3', 'COM4', etc.
    # Linux: '/dev/ttyUSB0', '/dev/rfcomm0'
    OBD_PORT = None
    
    UPDATE_INTERVAL = 1.0  # seconds
    
    # =======================================
    
    tracker = CarOBDTracker(
        vehicle_id=VEHICLE_ID,
        server_url=SERVER_URL
    )
    
    tracker.run(update_interval=UPDATE_INTERVAL, obd_port=OBD_PORT)


if __name__ == "__main__":
    main()
