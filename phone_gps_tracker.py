"""
Smartphone GPS Tracker
Use your phone's GPS to track vehicle position
Works with: Android, iOS via web browser
"""

import socketio
import time
from flask import Flask, render_template_string, jsonify, request
import threading

app = Flask(__name__)
sio_client = socketio.Client(reconnection=True)

# Global GPS data
gps_data = {
    'vehicle_id': 'PHONE_001',
    'lat': None,
    'lon': None,
    'speed': None,
    'heading': None,
    'accuracy': None,
    'timestamp': None
}

SERVER_URL = "http://localhost:5000"  # Change to your server IP

# HTML page with GPS access
PHONE_GPS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Phone GPS Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .status.disconnected {
            background: rgba(239, 68, 68, 0.3);
        }
        
        .status.connected {
            background: rgba(34, 197, 94, 0.3);
        }
        
        .status.tracking {
            background: rgba(59, 130, 246, 0.3);
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .label {
            opacity: 0.8;
        }
        
        .value {
            font-weight: 600;
            font-family: 'Courier New', monospace;
        }
        
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-start {
            background: #22c55e;
            color: white;
        }
        
        .btn-stop {
            background: #ef4444;
            color: white;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .input-group input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Phone GPS Tracker</h1>
        
        <div class="card">
            <div class="input-group">
                <label>Vehicle ID:</label>
                <input type="text" id="vehicleId" value="PHONE_001" placeholder="Enter vehicle ID">
            </div>
            
            <div class="input-group">
                <label>Server URL:</label>
                <input type="text" id="serverUrl" value="{{ server_url }}" placeholder="http://SERVER_IP:5000">
            </div>
        </div>
        
        <div id="status" class="status disconnected">
            🔴 Not Connected
        </div>
        
        <div class="card">
            <h3 style="margin-bottom: 15px;">📍 GPS Data</h3>
            <div class="info-row">
                <span class="label">Latitude:</span>
                <span class="value" id="lat">--</span>
            </div>
            <div class="info-row">
                <span class="label">Longitude:</span>
                <span class="value" id="lon">--</span>
            </div>
            <div class="info-row">
                <span class="label">Speed:</span>
                <span class="value" id="speed">-- km/h</span>
            </div>
            <div class="info-row">
                <span class="label">Heading:</span>
                <span class="value" id="heading">--°</span>
            </div>
            <div class="info-row">
                <span class="label">Accuracy:</span>
                <span class="value" id="accuracy">-- m</span>
            </div>
            <div class="info-row">
                <span class="label">Altitude:</span>
                <span class="value" id="altitude">-- m</span>
            </div>
        </div>
        
        <button id="toggleBtn" class="btn-start" onclick="toggleTracking()">
            🚀 Start Tracking
        </button>
    </div>

    <script>
        let tracking = false;
        let watchId = null;
        
        function updateStatus(message, className) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + className;
        }
        
        function updateDisplay(position) {
            document.getElementById('lat').textContent = position.coords.latitude.toFixed(6);
            document.getElementById('lon').textContent = position.coords.longitude.toFixed(6);
            document.getElementById('speed').textContent = 
                position.coords.speed ? (position.coords.speed * 3.6).toFixed(1) + ' km/h' : '0.0 km/h';
            document.getElementById('heading').textContent = 
                position.coords.heading ? position.coords.heading.toFixed(1) + '°' : '--°';
            document.getElementById('accuracy').textContent = 
                position.coords.accuracy ? position.coords.accuracy.toFixed(1) + ' m' : '-- m';
            document.getElementById('altitude').textContent = 
                position.coords.altitude ? position.coords.altitude.toFixed(1) + ' m' : '-- m';
        }
        
        function sendGPSData(position) {
            const vehicleId = document.getElementById('vehicleId').value;
            const serverUrl = document.getElementById('serverUrl').value;
            
            const data = {
                vehicle_id: vehicleId,
                lat: position.coords.latitude,
                lon: position.coords.longitude,
                speed: position.coords.speed ? position.coords.speed * 3.6 : 0,
                heading: position.coords.heading || 0,
                accuracy: position.coords.accuracy || 10,
                altitude: position.coords.altitude || 0,
                timestamp: position.timestamp
            };
            
            // Send to local server
            fetch('/update_gps', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(response => response.json())
              .then(result => {
                  if (result.status === 'ok') {
                      updateStatus('🟢 Tracking Active', 'tracking pulse');
                  }
              })
              .catch(err => console.error('Error:', err));
            
            updateDisplay(position);
        }
        
        function toggleTracking() {
            if (!tracking) {
                startTracking();
            } else {
                stopTracking();
            }
        }
        
        function startTracking() {
            if (!navigator.geolocation) {
                alert('❌ GPS not supported on this device!');
                return;
            }
            
            updateStatus('🔵 Requesting GPS access...', 'connected');
            
            const options = {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            };
            
            watchId = navigator.geolocation.watchPosition(
                (position) => {
                    tracking = true;
                    sendGPSData(position);
                    document.getElementById('toggleBtn').textContent = '🛑 Stop Tracking';
                    document.getElementById('toggleBtn').className = 'btn-stop';
                },
                (error) => {
                    console.error('GPS Error:', error);
                    updateStatus('❌ GPS Error: ' + error.message, 'disconnected');
                    stopTracking();
                },
                options
            );
        }
        
        function stopTracking() {
            if (watchId) {
                navigator.geolocation.clearWatch(watchId);
                watchId = null;
            }
            tracking = false;
            updateStatus('🔴 Tracking Stopped', 'disconnected');
            document.getElementById('toggleBtn').textContent = '🚀 Start Tracking';
            document.getElementById('toggleBtn').className = 'btn-start';
        }
        
        // Check GPS permission on load
        if (navigator.permissions) {
            navigator.permissions.query({name: 'geolocation'}).then(result => {
                console.log('GPS Permission:', result.state);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the phone GPS tracker page"""
    return render_template_string(PHONE_GPS_HTML, server_url=SERVER_URL)

@app.route('/update_gps', methods=['POST'])
def update_gps():
    """Receive GPS data from phone and forward to collision detection server"""
    data = request.json
    
    # Update global GPS data
    gps_data.update(data)
    
    # Forward to collision detection server
    try:
        if sio_client.connected:
            sio_client.emit('vehicle_update', {
                'vehicle_id': data['vehicle_id'],
                'lat': data['lat'],
                'lon': data['lon'],
                'altitude': data.get('altitude', 0),
                'accuracy': data.get('accuracy', 10)
            })
            print(f"📤 {data['vehicle_id']}: {data['lat']:.6f}, {data['lon']:.6f} | "
                  f"{data.get('speed', 0):.1f} km/h")
    except Exception as e:
        print(f"❌ Error forwarding data: {e}")
    
    return jsonify({'status': 'ok'})

@app.route('/status')
def status():
    """Get current GPS status"""
    return jsonify(gps_data)

def connect_to_server():
    """Connect to collision detection server"""
    
    @sio_client.event
    def connect():
        print(f"✅ Connected to collision detection server: {SERVER_URL}")
    
    @sio_client.event
    def disconnect():
        print(f"❌ Disconnected from server")
    
    @sio_client.event
    def connect_error(data):
        print(f"⚠️ Connection error: {data}")
    
    try:
        sio_client.connect(SERVER_URL)
    except Exception as e:
        print(f"⚠️ Could not connect to server: {e}")
        print("   Server will retry automatically...")

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║          📱 Smartphone GPS Tracker                        ║
║          Use your phone to track your vehicle             ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Connect to collision detection server
    print(f"\n🔌 Connecting to server: {SERVER_URL}")
    threading.Thread(target=connect_to_server, daemon=True).start()
    
    # Start local web server
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"\n📱 Phone GPS Tracker started!")
    print(f"\n🌐 Open this URL on your phone:")
    print(f"   http://{local_ip}:8080")
    print(f"   or")
    print(f"   http://localhost:8080 (if on same device)")
    print(f"\n💡 Make sure your phone is on the same WiFi network!")
    print(f"\n⚠️  You may need to allow location access in your browser")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Tracker stopped")
        sio_client.disconnect()

if __name__ == '__main__':
    main()
