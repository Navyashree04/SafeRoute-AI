"""
Real-Time Vehicle Tracker with Actual GPS Hardware
Supports: GPS modules (USB/Serial), Android GPS, iOS GPS
"""

import socketio
import time
import json
from typing import Optional, Tuple
import threading

# Try to import GPS libraries (install as needed)
try:
    import serial
    import pynmea2
    GPS_SERIAL_AVAILABLE = True
except ImportError:
    GPS_SERIAL_AVAILABLE = False
    print("⚠️ Warning: pyserial/pynmea2 not installed. Install with: pip install pyserial pynmea2")

try:
    from gps3 import gps3
    GPS3_AVAILABLE = True
except ImportError:
    GPS3_AVAILABLE = False
    print("⚠️ Warning: gps3 not installed. Install with: pip install gps3")


class RealGPSTracker:
    """Real-time GPS tracker for actual vehicles"""
    
    def __init__(self, vehicle_id: str, server_url: str = "http://localhost:5000", 
                 gps_source: str = "serial"):
        """
        Initialize GPS tracker
        
        Args:
            vehicle_id: Unique vehicle identifier
            server_url: Server WebSocket URL
            gps_source: 'serial', 'gpsd', 'android', or 'ios'
        """
        self.vehicle_id = vehicle_id
        self.server_url = server_url
        self.gps_source = gps_source
        
        # Current GPS data
        self.lat = None
        self.lon = None
        self.altitude = None
        self.speed = None  # km/h
        self.heading = None  # degrees
        self.accuracy = None
        self.satellites = 0
        self.gps_fix = False
        
        # Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1
        )
        
        # GPS thread
        self.gps_thread = None
        self.running = False
        
        self.setup_events()
    
    def setup_events(self):
        """Setup Socket.IO events"""
        @self.sio.event
        def connect():
            print(f"✅ Vehicle {self.vehicle_id} connected to server")
            
        @self.sio.event
        def disconnect():
            print(f"❌ Vehicle {self.vehicle_id} disconnected from server")
            
        @self.sio.event
        def error(data):
            print(f"⚠️ Error: {data}")
    
    def connect_to_server(self):
        """Connect to collision detection server"""
        print(f"🔌 Connecting to server: {self.server_url}")
        try:
            self.sio.connect(self.server_url, wait_timeout=10)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def read_gps_serial(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        """
        Read GPS from USB/Serial GPS module (NMEA protocol)
        
        Common GPS modules: NEO-6M, NEO-7M, NEO-8M, BN-880
        Ports: 
            - Linux: /dev/ttyUSB0, /dev/ttyACM0
            - Windows: COM3, COM4, COM5
            - Mac: /dev/cu.usbserial
        """
        if not GPS_SERIAL_AVAILABLE:
            print("❌ pyserial/pynmea2 not installed!")
            return
        
        print(f"📡 Opening GPS on {port} at {baudrate} baud...")
        
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            print(f"✅ GPS module connected on {port}")
            
            while self.running:
                try:
                    line = ser.readline().decode('ascii', errors='replace').strip()
                    
                    if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                        # GGA - Fix data
                        msg = pynmea2.parse(line)
                        if msg.latitude and msg.longitude:
                            self.lat = msg.latitude
                            self.lon = msg.longitude
                            self.altitude = msg.altitude if msg.altitude else 0.0
                            self.satellites = msg.num_sats if msg.num_sats else 0
                            self.gps_fix = msg.gps_qual > 0
                            
                    elif line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                        # RMC - Recommended minimum data
                        msg = pynmea2.parse(line)
                        if msg.latitude and msg.longitude:
                            self.lat = msg.latitude
                            self.lon = msg.longitude
                            # Convert knots to km/h
                            if msg.spd_over_grnd:
                                self.speed = msg.spd_over_grnd * 1.852
                            if msg.true_course:
                                self.heading = msg.true_course
                                
                    elif line.startswith('$GPVTG') or line.startswith('$GNVTG'):
                        # VTG - Course and speed
                        msg = pynmea2.parse(line)
                        if msg.spd_over_grnd_kmph:
                            self.speed = msg.spd_over_grnd_kmph
                        if msg.true_track:
                            self.heading = msg.true_track
                    
                    # Show status
                    if self.gps_fix and self.lat and self.lon:
                        print(f"🛰️  GPS: {self.lat:.6f}, {self.lon:.6f} | "
                              f"Sats: {self.satellites} | Fix: ✅")
                    else:
                        print(f"🔍 Searching for GPS fix... Satellites: {self.satellites}")
                        
                except pynmea2.ParseError:
                    continue
                except UnicodeDecodeError:
                    continue
                    
        except serial.SerialException as e:
            print(f"❌ Serial error: {e}")
        finally:
            if 'ser' in locals():
                ser.close()
    
    def read_gps_gpsd(self):
        """
        Read GPS from gpsd daemon (Linux)
        Requires: apt-get install gpsd gpsd-clients
        """
        if not GPS3_AVAILABLE:
            print("❌ gps3 not installed!")
            return
        
        print("📡 Connecting to gpsd...")
        
        gps_socket = gps3.GPSDSocket()
        data_stream = gps3.DataStream()
        
        try:
            gps_socket.connect()
            gps_socket.watch()
            print("✅ Connected to gpsd")
            
            while self.running:
                for new_data in gps_socket:
                    if new_data:
                        data_stream.unpack(new_data)
                        
                        if data_stream.TPV['lat'] != 'n/a':
                            self.lat = float(data_stream.TPV['lat'])
                        if data_stream.TPV['lon'] != 'n/a':
                            self.lon = float(data_stream.TPV['lon'])
                        if data_stream.TPV['alt'] != 'n/a':
                            self.altitude = float(data_stream.TPV['alt'])
                        if data_stream.TPV['speed'] != 'n/a':
                            # Convert m/s to km/h
                            self.speed = float(data_stream.TPV['speed']) * 3.6
                        if data_stream.TPV['track'] != 'n/a':
                            self.heading = float(data_stream.TPV['track'])
                        
                        self.gps_fix = data_stream.TPV['mode'] >= 2
                        
                        if self.gps_fix:
                            print(f"🛰️  GPS: {self.lat:.6f}, {self.lon:.6f} | Fix: ✅")
                        
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ gpsd error: {e}")
        finally:
            gps_socket.close()
    
    def read_gps_android(self, port: int = 50000):
        """
        Read GPS from Android phone
        Requires: GPS2IP app or similar
        Phone sends NMEA data over TCP/IP
        """
        import socket
        
        print(f"📱 Waiting for Android GPS on port {port}...")
        print("   Install 'GPS2IP' app on your phone and start streaming")
        
        server_socket = socket.socket(socket.AF_INET, socket.AF_INET6)
        server_socket.bind(('', port))
        server_socket.listen(1)
        
        print(f"📡 Listening on port {port}...")
        
        while self.running:
            try:
                conn, addr = server_socket.accept()
                print(f"✅ Android device connected from {addr}")
                
                buffer = ""
                while self.running:
                    data = conn.recv(1024).decode('ascii', errors='replace')
                    if not data:
                        break
                    
                    buffer += data
                    lines = buffer.split('\n')
                    buffer = lines[-1]
                    
                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith('$'):
                            try:
                                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                                    msg = pynmea2.parse(line)
                                    if msg.latitude and msg.longitude:
                                        self.lat = msg.latitude
                                        self.lon = msg.longitude
                                        self.altitude = msg.altitude if msg.altitude else 0.0
                                        self.gps_fix = msg.gps_qual > 0
                                        
                                elif line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                                    msg = pynmea2.parse(line)
                                    if msg.spd_over_grnd:
                                        self.speed = msg.spd_over_grnd * 1.852
                                    if msg.true_course:
                                        self.heading = msg.true_course
                                        
                            except pynmea2.ParseError:
                                continue
                    
                    if self.gps_fix and self.lat and self.lon:
                        print(f"📱 GPS: {self.lat:.6f}, {self.lon:.6f} | Speed: {self.speed:.1f} km/h")
                        
            except Exception as e:
                print(f"⚠️ Connection error: {e}")
                time.sleep(1)
    
    def start_gps(self, **kwargs):
        """Start GPS reading in background thread"""
        self.running = True
        
        if self.gps_source == "serial":
            port = kwargs.get('port', '/dev/ttyUSB0')  # or 'COM3' on Windows
            baudrate = kwargs.get('baudrate', 9600)
            self.gps_thread = threading.Thread(
                target=self.read_gps_serial, 
                args=(port, baudrate)
            )
        elif self.gps_source == "gpsd":
            self.gps_thread = threading.Thread(target=self.read_gps_gpsd)
        elif self.gps_source == "android":
            port = kwargs.get('port', 50000)
            self.gps_thread = threading.Thread(
                target=self.read_gps_android,
                args=(port,)
            )
        else:
            print(f"❌ Unknown GPS source: {self.gps_source}")
            return False
        
        self.gps_thread.daemon = True
        self.gps_thread.start()
        return True
    
    def send_position_update(self):
        """Send current position to server"""
        if not self.gps_fix or self.lat is None or self.lon is None:
            return
        
        try:
            data = {
                "vehicle_id": self.vehicle_id,
                "lat": self.lat,
                "lon": self.lon,
                "altitude": self.altitude if self.altitude else 0.0,
                "accuracy": self.accuracy if self.accuracy else 10.0
            }
            
            self.sio.emit("vehicle_update", data)
            
            print(f"📤 Sent: Vehicle {self.vehicle_id} | "
                  f"{self.lat:.6f}, {self.lon:.6f} | "
                  f"{self.speed:.1f} km/h | "
                  f"{self.heading:.1f}° | "
                  f"Sats: {self.satellites}")
            
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    def run(self, update_interval: float = 1.0, **gps_kwargs):
        """
        Main loop - read GPS and send updates
        
        Args:
            update_interval: Seconds between server updates
            **gps_kwargs: GPS-specific parameters (port, baudrate, etc.)
        """
        # Start GPS reading
        if not self.start_gps(**gps_kwargs):
            print("❌ Failed to start GPS")
            return
        
        # Connect to server
        if not self.connect_to_server():
            print("❌ Failed to connect to server")
            return
        
        print(f"\n🚗 Vehicle {self.vehicle_id} tracking started!")
        print(f"📡 GPS Source: {self.gps_source}")
        print(f"🔄 Update interval: {update_interval}s")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.send_position_update()
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Vehicle {self.vehicle_id} stopped by user")
        finally:
            self.running = False
            self.sio.disconnect()
            print("✅ Disconnected")


def main():
    """Main function with configuration"""
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Real-Time GPS Vehicle Tracker                         ║
║     Connect actual GPS hardware to track your vehicle     ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # ============ CONFIGURATION ============
    
    VEHICLE_ID = "CAR_001"  # Change this for each vehicle
    SERVER_URL = "http://localhost:5000"  # Your server address
    
    # GPS Source: "serial", "gpsd", or "android"
    GPS_SOURCE = "serial"
    
    # GPS Settings (modify based on your setup)
    GPS_SETTINGS = {
        # For USB/Serial GPS modules:
        'port': 'COM3',        # Windows: COM3, COM4, etc.
                               # Linux: /dev/ttyUSB0, /dev/ttyACM0
                               # Mac: /dev/cu.usbserial
        'baudrate': 9600,      # Usually 9600 or 115200
        
        # For Android GPS streaming:
        # 'port': 50000,       # TCP port for GPS2IP app
    }
    
    UPDATE_INTERVAL = 1.0  # Send updates every 1 second
    
    # =======================================
    
    # Create tracker
    tracker = RealGPSTracker(
        vehicle_id=VEHICLE_ID,
        server_url=SERVER_URL,
        gps_source=GPS_SOURCE
    )
    
    # Run
    tracker.run(update_interval=UPDATE_INTERVAL, **GPS_SETTINGS)


if __name__ == "__main__":
    main()
