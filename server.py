"""
Advanced Oncoming Vehicle Detection System - Server
Features:
- Multi-level collision warnings (critical, warning, info)
- Configurable thresholds
- Vehicle history tracking
- Detailed logging
- REST API for analytics
"""

from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
import math
import time
import logging
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import json

# Configuration
class Config:
    HOST = "0.0.0.0"
    PORT = 5000
    DEBUG = True
    
    # Detection thresholds
    CRITICAL_DISTANCE = 30  # meters
    WARNING_DISTANCE = 80   # meters
    INFO_DISTANCE = 150     # meters
    
    # Direction thresholds (degrees)
    ONCOMING_ANGLE = 150    # vehicles moving in opposite directions
    PERPENDICULAR_ANGLE = 45  # vehicles at cross-angles
    
    # Speed thresholds (km/h)
    MIN_SPEED_ALERT = 5     # ignore stationary vehicles
    HIGH_SPEED = 50         # high-speed threshold
    
    # History
    MAX_HISTORY_POINTS = 100
    VEHICLE_TIMEOUT = 30    # seconds before removing inactive vehicle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vehicle_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vehicle_detection_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Data structures
@dataclass
class VehicleState:
    vehicle_id: str
    lat: float
    lon: float
    speed: float
    direction: float
    timestamp: float
    altitude: float = 0.0
    accuracy: float = 10.0

@dataclass
class Alert:
    severity: str  # 'critical', 'warning', 'info'
    target_vehicle: str
    distance: float
    relative_speed: float
    time_to_collision: Optional[float]
    message: str

class VehicleTracker:
    def __init__(self):
        self.vehicles: Dict[str, VehicleState] = {}
        self.history: Dict[str, deque] = {}
        self.previous_distances: Dict[Tuple[str, str], float] = {}
        self.alert_history: List[Dict] = []
        
    def update_vehicle(self, vehicle_id: str, lat: float, lon: float, 
                      altitude: float = 0.0, accuracy: float = 10.0) -> VehicleState:
        """Update vehicle position and calculate speed/direction"""
        now = time.time()
        
        speed = 0.0
        direction = 0.0
        
        if vehicle_id in self.vehicles:
            prev = self.vehicles[vehicle_id]
            
            # Calculate distance moved
            dist = haversine(prev.lat, prev.lon, lat, lon)
            dt = now - prev.timestamp
            
            if dt > 0:
                # Speed in km/h
                speed = (dist / dt) * 3.6
                
                # Direction (bearing)
                if dist > 0.5:  # Only update direction if moved significantly
                    direction = bearing(prev.lat, prev.lon, lat, lon)
                else:
                    direction = prev.direction  # Keep previous direction if barely moved
        
        # Create new state
        state = VehicleState(
            vehicle_id=vehicle_id,
            lat=lat,
            lon=lon,
            speed=round(speed, 2),
            direction=round(direction, 2),
            timestamp=now,
            altitude=altitude,
            accuracy=accuracy
        )
        
        self.vehicles[vehicle_id] = state
        
        # Update history
        if vehicle_id not in self.history:
            self.history[vehicle_id] = deque(maxlen=Config.MAX_HISTORY_POINTS)
        self.history[vehicle_id].append({
            'lat': lat,
            'lon': lon,
            'timestamp': now,
            'speed': speed
        })
        
        logger.info(f"Vehicle {vehicle_id} updated: {lat:.6f}, {lon:.6f}, "
                   f"speed={speed:.2f} km/h, dir={direction:.2f}°")
        
        return state
    
    def detect_collisions(self) -> Dict[str, List[Alert]]:
        """Detect potential collisions between all vehicles"""
        alerts: Dict[str, List[Alert]] = {vid: [] for vid in self.vehicles}
        
        vehicle_ids = list(self.vehicles.keys())
        
        for i, my_id in enumerate(vehicle_ids):
            for other_id in vehicle_ids[i+1:]:
                my_vehicle = self.vehicles[my_id]
                other_vehicle = self.vehicles[other_id]
                
                # Calculate metrics
                dist = haversine(my_vehicle.lat, my_vehicle.lon, 
                               other_vehicle.lat, other_vehicle.lon)
                
                dir_diff = direction_diff(my_vehicle.direction, other_vehicle.direction)
                
                # Check if approaching
                key = (my_id, other_id)
                prev_dist = self.previous_distances.get(key, dist + 1)
                approaching = dist < prev_dist
                self.previous_distances[key] = dist
                
                # Calculate relative speed
                relative_speed = abs(my_vehicle.speed - other_vehicle.speed)
                
                # Time to collision (simple estimate)
                ttc = None
                if approaching and my_vehicle.speed > 0:
                    closing_speed = (my_vehicle.speed + other_vehicle.speed) / 3.6  # m/s
                    if closing_speed > 0:
                        ttc = dist / closing_speed
                
                # Generate alerts based on conditions
                alert = self._evaluate_threat(
                    my_id, other_id, dist, dir_diff, approaching, 
                    relative_speed, ttc, my_vehicle, other_vehicle
                )
                
                if alert:
                    alerts[my_id].append(alert)
                    # Mirror alert for other vehicle
                    mirror_alert = Alert(
                        severity=alert.severity,
                        target_vehicle=my_id,
                        distance=alert.distance,
                        relative_speed=alert.relative_speed,
                        time_to_collision=alert.time_to_collision,
                        message=alert.message.replace(other_id, my_id).replace(my_id, other_id)
                    )
                    alerts[other_id].append(mirror_alert)
                    
                    # Log alert
                    self.alert_history.append({
                        'timestamp': time.time(),
                        'vehicle_1': my_id,
                        'vehicle_2': other_id,
                        'severity': alert.severity,
                        'distance': dist,
                        'ttc': ttc
                    })
        
        return alerts
    
    def _evaluate_threat(self, my_id: str, other_id: str, dist: float, 
                        dir_diff: float, approaching: bool, relative_speed: float,
                        ttc: Optional[float], my_vehicle: VehicleState, 
                        other_vehicle: VehicleState) -> Optional[Alert]:
        """Evaluate threat level and generate appropriate alert"""
        
        # Ignore stationary vehicles
        if my_vehicle.speed < Config.MIN_SPEED_ALERT and \
           other_vehicle.speed < Config.MIN_SPEED_ALERT:
            return None
        
        # Check for oncoming vehicles
        is_oncoming = dir_diff > Config.ONCOMING_ANGLE
        is_crossing = 45 < dir_diff < 135
        
        severity = None
        message = ""
        
        # Critical alerts
        if is_oncoming and approaching and dist < Config.CRITICAL_DISTANCE:
            severity = "critical"
            message = f"⚠️ COLLISION IMMINENT with Vehicle {other_id}!"
            
        # Warning alerts
        elif is_oncoming and approaching and dist < Config.WARNING_DISTANCE:
            severity = "warning"
            message = f"⚠ Oncoming Vehicle {other_id} detected"
            
        # Crossing vehicle warnings
        elif is_crossing and approaching and dist < Config.WARNING_DISTANCE:
            severity = "warning"
            message = f"⚠ Crossing Vehicle {other_id} detected"
            
        # Info alerts
        elif is_oncoming and dist < Config.INFO_DISTANCE:
            severity = "info"
            message = f"ℹ Vehicle {other_id} approaching"
        
        if severity:
            return Alert(
                severity=severity,
                target_vehicle=other_id,
                distance=round(dist, 2),
                relative_speed=round(relative_speed, 2),
                time_to_collision=round(ttc, 1) if ttc else None,
                message=message
            )
        
        return None
    
    def cleanup_inactive_vehicles(self):
        """Remove vehicles that haven't reported in a while"""
        now = time.time()
        inactive = [
            vid for vid, vehicle in self.vehicles.items()
            if now - vehicle.timestamp > Config.VEHICLE_TIMEOUT
        ]
        
        for vid in inactive:
            logger.info(f"Removing inactive vehicle {vid}")
            del self.vehicles[vid]
            if vid in self.history:
                del self.history[vid]

# Global tracker
tracker = VehicleTracker()

# Utility functions
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters"""
    R = 6371000  # Earth radius in meters
    
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing between two GPS coordinates (0-360 degrees)"""
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
         math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.cos(math.radians(lon2 - lon1)))
    
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def direction_diff(d1: float, d2: float) -> float:
    """Calculate smallest angle difference between two bearings"""
    diff = abs(d1 - d2)
    return min(diff, 360 - diff)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {id}")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected")

@socketio.on('vehicle_update')
def handle_vehicle_update(data):
    """Handle vehicle position update"""
    try:
        vehicle_id = data['vehicle_id']
        lat = float(data['lat'])
        lon = float(data['lon'])
        altitude = float(data.get('altitude', 0.0))
        accuracy = float(data.get('accuracy', 10.0))
        
        # Update vehicle
        tracker.update_vehicle(vehicle_id, lat, lon, altitude, accuracy)
        
        # Cleanup inactive vehicles
        tracker.cleanup_inactive_vehicles()
        
        # Detect collisions
        alerts = tracker.detect_collisions()
        
        # Prepare data for broadcast
        vehicle_data = {
            vid: asdict(state) 
            for vid, state in tracker.vehicles.items()
        }
        
        alert_data = {
            vid: [asdict(alert) for alert in alert_list]
            for vid, alert_list in alerts.items()
        }
        
        # Broadcast to all clients
        socketio.emit('vehicle_data', {
            'vehicles': vehicle_data,
            'alerts': alert_data,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in vehicle_update: {e}", exc_info=True)
        emit('error', {'message': str(e)})

# REST API endpoints
@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'active_vehicles': len(tracker.vehicles),
        'config': {
            'critical_distance': Config.CRITICAL_DISTANCE,
            'warning_distance': Config.WARNING_DISTANCE,
            'info_distance': Config.INFO_DISTANCE
        }
    })

@app.route('/api/vehicles')
def get_vehicles():
    """Get all active vehicles"""
    return jsonify({
        vid: asdict(state)
        for vid, state in tracker.vehicles.items()
    })

@app.route('/api/vehicle/<vehicle_id>')
def get_vehicle(vehicle_id):
    """Get specific vehicle data"""
    if vehicle_id in tracker.vehicles:
        return jsonify(asdict(tracker.vehicles[vehicle_id]))
    return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/api/vehicle/<vehicle_id>/history')
def get_vehicle_history(vehicle_id):
    """Get vehicle movement history"""
    if vehicle_id in tracker.history:
        return jsonify(list(tracker.history[vehicle_id]))
    return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/api/alerts')
def get_recent_alerts():
    """Get recent alert history"""
    recent = tracker.alert_history[-100:]  # Last 100 alerts
    return jsonify(recent)

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    return jsonify({
        'active_vehicles': len(tracker.vehicles),
        'total_alerts': len(tracker.alert_history),
        'vehicles': list(tracker.vehicles.keys()),
        'uptime': time.time()
    })

if __name__ == '__main__':
    logger.info("Starting Vehicle Detection Server...")
    logger.info(f"Server running on {Config.HOST}:{Config.PORT}")
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
