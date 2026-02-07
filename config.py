"""
Configuration File for Vehicle Collision Detection System
Modify these values to customize system behavior
"""

class SystemConfig:
    """Main system configuration"""
    
    # Server Settings
    SERVER_HOST = "0.0.0.0"  # Use "0.0.0.0" to accept connections from any IP
    SERVER_PORT = 5000
    DEBUG_MODE = True
    
    # Logging Settings
    LOG_FILE = "vehicle_system.log"
    LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Database Settings (optional - for future use)
    USE_DATABASE = False
    DATABASE_URL = "sqlite:///vehicles.db"


class DetectionConfig:
    """Collision detection parameters"""
    
    # Distance Thresholds (meters)
    CRITICAL_DISTANCE = 30   # Red alert - collision imminent
    WARNING_DISTANCE = 80    # Yellow alert - oncoming vehicle
    INFO_DISTANCE = 150      # Blue alert - vehicle approaching
    
    # Direction Thresholds (degrees)
    ONCOMING_ANGLE = 150     # Vehicles moving in opposite directions
    PERPENDICULAR_ANGLE = 45  # Vehicles at right angles
    
    # Speed Thresholds (km/h)
    MIN_SPEED_ALERT = 5      # Ignore vehicles moving slower than this
    HIGH_SPEED_THRESHOLD = 50  # Flag high-speed vehicles
    
    # Time Settings
    UPDATE_INTERVAL = 1.0    # Seconds between vehicle updates
    VEHICLE_TIMEOUT = 30     # Remove vehicle after this many seconds of inactivity
    
    # History Settings
    MAX_HISTORY_POINTS = 100  # Number of position points to store per vehicle
    KEEP_ALERT_HISTORY = True
    MAX_ALERT_HISTORY = 1000


class SimulatorConfig:
    """Vehicle simulator settings"""
    
    # Default Starting Locations (Bangalore, India)
    DEFAULT_START_LAT = 12.9716
    DEFAULT_START_LON = 77.5946
    DEFAULT_ALTITUDE = 920.0  # meters above sea level
    
    # Movement Settings
    DEFAULT_SPEED = 40       # km/h
    MAX_SPEED = 120          # km/h
    MIN_SPEED = 5            # km/h
    
    # GPS Simulation
    GPS_NOISE_ENABLED = True
    GPS_NOISE_RANGE = 0.000005  # degrees (about 0.5 meters)
    GPS_ACCURACY_RANGE = (5, 15)  # meters
    
    # Update Rate
    UPDATE_RATE = 1.0        # seconds
    
    # Reconnection Settings
    RECONNECT_ENABLED = True
    RECONNECT_ATTEMPTS = 0   # 0 = infinite
    RECONNECT_DELAY = 1      # seconds


class UIConfig:
    """Web interface configuration"""
    
    # Map Settings
    MAP_CENTER_LAT = 12.9716
    MAP_CENTER_LON = 77.5946
    MAP_ZOOM_LEVEL = 15
    MAP_MAX_ZOOM = 19
    
    # Display Settings
    SHOW_VEHICLE_TRAILS = True
    MAX_TRAIL_POINTS = 30
    AUTO_CENTER_ON_MY_CAR = True
    
    # Alert Settings
    ENABLE_AUDIO_ALERTS = True
    AUDIO_ALERT_FREQUENCY = 800  # Hz
    AUDIO_ALERT_DURATION = 0.5   # seconds
    ALERT_COOLDOWN = 2.0         # seconds between alerts
    
    # Colors (hex)
    TRAIL_COLOR_MY_CAR = "#3b82f6"
    TRAIL_COLOR_OTHER = "#666666"
    CRITICAL_COLOR = "#ef4444"
    WARNING_COLOR = "#f59e0b"
    INFO_COLOR = "#3b82f6"


class ScenarioConfig:
    """Predefined movement scenarios"""
    
    SCENARIOS = {
        "north": {
            "speed": 40,
            "direction": 0,
            "description": "Move north at constant speed"
        },
        "south": {
            "speed": 45,
            "direction": 180,
            "description": "Move south at constant speed"
        },
        "east": {
            "speed": 35,
            "direction": 90,
            "description": "Move east at constant speed"
        },
        "west": {
            "speed": 35,
            "direction": 270,
            "description": "Move west at constant speed"
        },
        "circuit": {
            "speed": 30,
            "pattern": [0, 90, 180, 270],
            "interval": 30,
            "description": "Square circuit pattern"
        },
        "zigzag": {
            "speed": 40,
            "pattern": [180, 190, 180, 170],
            "interval": 5,
            "description": "Zigzag pattern (lane changes)"
        },
        "variable_speed": {
            "speeds": [20, 30, 40, 50, 60, 40, 20],
            "direction": 0,
            "interval": 20,
            "description": "Variable speed northbound"
        },
        "accelerating": {
            "start_speed": 20,
            "max_speed": 70,
            "acceleration": 2,
            "direction": 180,
            "description": "Gradual acceleration southbound"
        }
    }


# Test Scenarios for Demonstration
class TestScenarios:
    """Pre-configured test scenarios"""
    
    HEAD_ON_COLLISION = {
        "car_a": {
            "id": "A",
            "start_lat": 12.9716,
            "start_lon": 77.5946,
            "scenario": "north",
            "speed": 50
        },
        "car_b": {
            "id": "B",
            "start_lat": 12.9726,
            "start_lon": 77.5946,
            "scenario": "south",
            "speed": 50
        },
        "description": "Two cars approaching head-on"
    }
    
    INTERSECTION_CROSSING = {
        "car_a": {
            "id": "A",
            "start_lat": 12.9716,
            "start_lon": 77.5946,
            "scenario": "north",
            "speed": 40
        },
        "car_b": {
            "id": "B",
            "start_lat": 12.9716,
            "start_lon": 77.5936,
            "scenario": "east",
            "speed": 40
        },
        "description": "Intersection crossing scenario"
    }
    
    MULTIPLE_VEHICLES = {
        "car_a": {
            "id": "A",
            "start_lat": 12.9716,
            "start_lon": 77.5946,
            "scenario": "circuit",
        },
        "car_b": {
            "id": "B",
            "start_lat": 12.9726,
            "start_lon": 77.5946,
            "scenario": "south",
        },
        "car_c": {
            "id": "C",
            "start_lat": 12.9716,
            "start_lon": 77.5936,
            "scenario": "east",
        },
        "description": "Multiple vehicles in complex patterns"
    }


# Export all configs
__all__ = [
    'SystemConfig',
    'DetectionConfig',
    'SimulatorConfig',
    'UIConfig',
    'ScenarioConfig',
    'TestScenarios'
]
