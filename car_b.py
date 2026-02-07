"""
Vehicle Simulator - Car B
Simulates a vehicle moving in opposite direction (south)
"""

import socketio
import time
import math
import random
from typing import Tuple, List

class VehicleSimulator:
    def __init__(self, vehicle_id: str, start_lat: float, start_lon: float, 
                 server_url: str = "http://localhost:5000"):
        self.vehicle_id = vehicle_id
        self.lat = start_lat
        self.lon = start_lon
        self.altitude = 920.0  # Bangalore altitude
        self.speed = 0.0  # km/h
        self.direction = 0.0  # degrees
        self.server_url = server_url
        
        # Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1,
            reconnection_delay_max=5
        )
        
        # Setup event handlers
        self.setup_events()
        
    def setup_events(self):
        @self.sio.event
        def connect():
            print(f"✓ Vehicle {self.vehicle_id} connected to server")
            
        @self.sio.event
        def disconnect():
            print(f"✗ Vehicle {self.vehicle_id} disconnected from server")
            
        @self.sio.event
        def connection_response(data):
            print(f"Server response: {data}")
            
        @self.sio.event
        def error(data):
            print(f"Error from server: {data}")
    
    def connect(self):
        """Connect to server"""
        print(f"Connecting Vehicle {self.vehicle_id} to {self.server_url}...")
        try:
            self.sio.connect(self.server_url, wait_timeout=10)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def move_straight(self, distance_meters: float, direction: float):
        """Move vehicle in a straight line"""
        # Convert distance to degrees (approximate)
        lat_change = (distance_meters / 111000.0) * math.cos(math.radians(direction))
        lon_change = (distance_meters / 111000.0) * math.sin(math.radians(direction)) / \
                     math.cos(math.radians(self.lat))
        
        self.lat += lat_change
        self.lon += lon_change
        self.direction = direction
    
    def update_position(self):
        """Send position update to server"""
        try:
            # Add small GPS noise for realism
            noise_lat = random.uniform(-0.000005, 0.000005)
            noise_lon = random.uniform(-0.000005, 0.000005)
            
            data = {
                "vehicle_id": self.vehicle_id,
                "lat": self.lat + noise_lat,
                "lon": self.lon + noise_lon,
                "altitude": self.altitude + random.uniform(-2, 2),
                "accuracy": random.uniform(5, 15)
            }
            
            self.sio.emit("vehicle_update", data)
            
            print(f"Car {self.vehicle_id}: lat={self.lat:.6f}, lon={self.lon:.6f}, "
                  f"speed={self.speed:.1f} km/h, dir={self.direction:.1f}°")
            
        except Exception as e:
            print(f"Error sending update: {e}")
    
    def run_scenario(self, scenario: str = "south"):
        """Run predefined movement scenario"""
        print(f"\n🚗 Starting Vehicle {self.vehicle_id} - Scenario: {scenario}")
        print("=" * 60)
        
        if scenario == "south":
            # Move south along a road (opposite to Car A)
            self.speed = 45  # km/h
            move_per_second = (self.speed * 1000 / 3600)  # meters per second
            
            while True:
                self.move_straight(move_per_second, 180)  # 180° = South
                self.update_position()
                time.sleep(1)
                
        elif scenario == "east":
            # Move east along a road
            self.speed = 35  # km/h
            move_per_second = (self.speed * 1000 / 3600)
            
            while True:
                self.move_straight(move_per_second, 90)  # 90° = East
                self.update_position()
                time.sleep(1)
                
        elif scenario == "zigzag":
            # Zigzag pattern (simulating lane changes)
            self.speed = 40  # km/h
            move_per_second = (self.speed * 1000 / 3600)
            directions = [180, 190, 180, 170]  # South with slight variations
            direction_index = 0
            step_count = 0
            
            while True:
                current_dir = directions[direction_index]
                self.move_straight(move_per_second, current_dir)
                self.update_position()
                
                step_count += 1
                if step_count >= 5:  # Change direction every 5 seconds
                    step_count = 0
                    direction_index = (direction_index + 1) % len(directions)
                
                time.sleep(1)
        
        elif scenario == "accelerating":
            # Accelerating scenario
            self.speed = 20  # Starting speed
            max_speed = 70
            acceleration = 2  # km/h per second
            
            while True:
                move_per_second = (self.speed * 1000 / 3600)
                self.move_straight(move_per_second, 180)  # South
                self.update_position()
                
                # Accelerate
                if self.speed < max_speed:
                    self.speed += acceleration
                    if self.speed >= max_speed:
                        print(f"⚡ Reached max speed: {max_speed} km/h")
                
                time.sleep(1)

def main():
    # Configuration
    VEHICLE_ID = "B"
    START_LAT = 12.9726  # Slightly north of Car A
    START_LON = 77.5946
    SERVER_URL = "http://localhost:5000"
    SCENARIO = "south"  # Options: south, east, zigzag, accelerating
    
    # Create simulator
    simulator = VehicleSimulator(VEHICLE_ID, START_LAT, START_LON, SERVER_URL)
    
    # Connect to server
    if simulator.connect():
        try:
            # Run scenario
            simulator.run_scenario(SCENARIO)
        except KeyboardInterrupt:
            print(f"\n\n🛑 Vehicle {VEHICLE_ID} stopped by user")
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
        finally:
            simulator.sio.disconnect()
            print(f"Vehicle {VEHICLE_ID} disconnected")
    else:
        print("Failed to connect to server. Exiting...")

if __name__ == "__main__":
    main()
