# 🚗 Advanced Vehicle Collision Detection System

A real-time vehicle collision warning system that detects oncoming vehicles and potential collisions using GPS coordinates, speed, and direction data. The system provides multi-level alerts (critical, warning, info) based on distance, approach angle, and time-to-collision.

## 🌟 Features

### Core Features
- **Real-time Vehicle Tracking**: Monitor multiple vehicles simultaneously
- **Multi-level Alerts**: 
  - 🔴 **Critical**: Collision imminent (<30m)
  - 🟡 **Warning**: Oncoming vehicle detected (<80m)
  - 🔵 **Info**: Vehicle approaching (<150m)
- **Smart Detection**: 
  - Oncoming vehicle detection (opposite directions)
  - Cross-traffic warnings
  - Time-to-collision estimates
- **Interactive Map**: Real-time visualization using Leaflet.js
- **Vehicle Trails**: Historical path tracking
- **Audio Alerts**: Sound warnings for critical situations

### Technical Features
- WebSocket-based real-time communication
- RESTful API for analytics
- Vehicle history tracking
- Configurable thresholds
- GPS noise simulation for realistic testing
- Automatic cleanup of inactive vehicles
- Comprehensive logging

## 📋 Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Network connection (for local testing, localhost is sufficient)

## 🚀 Installation

### 1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd vehicle-collision-detection

# Or extract the ZIP file and navigate to the folder
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 🎮 Usage

### Starting the System

#### 1. Start the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`. You should see:
```
Starting Vehicle Detection Server...
Server running on 0.0.0.0:5000
* Running on http://127.0.0.1:5000
```

#### 2. Start Vehicle Simulators

**Terminal 2 - Start Car A (moving north):**
```bash
python car_a.py
```

**Terminal 3 - Start Car B (moving south - oncoming):**
```bash
python car_b.py
```

You can start additional vehicles by modifying the vehicle ID in the simulators.

#### 3. Open the Web Interface

Open `index.html` in your web browser:
```bash
# Option 1: Double-click index.html
# Option 2: Use command line
# On macOS:
open index.html
# On Linux:
xdg-open index.html
# On Windows:
start index.html
```

**Select your vehicle ID** from the dropdown to see alerts for your vehicle.

## 🎯 How It Works

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Vehicle A      │         │  Vehicle B      │
│  (Simulator)    │         │  (Simulator)    │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │ Socket.IO                 │ Socket.IO
         │ (GPS Updates)             │ (GPS Updates)
         │                           │
         └───────────┬───────────────┘
                     │
              ┌──────▼──────┐
              │   Server    │
              │  (Python)   │
              │             │
              │ - Tracking  │
              │ - Detection │
              │ - Alerts    │
              └──────┬──────┘
                     │
         ┌───────────┴───────────┐
         │ Socket.IO             │
         │ (Vehicle Data +       │
         │  Alerts)              │
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │  Web UI  │          │  Web UI  │
    │ (Car A)  │          │ (Car B)  │
    └──────────┘          └──────────┘
```

### Detection Algorithm

1. **Position Updates**: Vehicles send GPS coordinates every second
2. **Speed Calculation**: Server calculates speed from distance traveled
3. **Direction Calculation**: Bearing between consecutive positions
4. **Threat Assessment**:
   - Calculate distance between vehicles
   - Compare directions (oncoming if >150° difference)
   - Check if vehicles are approaching
   - Estimate time-to-collision
5. **Alert Generation**: Based on severity thresholds

### Alert Thresholds

| Severity | Distance | Conditions |
|----------|----------|------------|
| Critical | < 30m | Oncoming + Approaching |
| Warning | < 80m | Oncoming/Crossing + Approaching |
| Info | < 150m | Oncoming |

## ⚙️ Configuration

### Server Configuration

Edit `server.py` to modify detection parameters:

```python
class Config:
    # Detection thresholds
    CRITICAL_DISTANCE = 30   # meters
    WARNING_DISTANCE = 80    # meters
    INFO_DISTANCE = 150      # meters
    
    # Direction thresholds
    ONCOMING_ANGLE = 150     # degrees
    
    # Speed thresholds
    MIN_SPEED_ALERT = 5      # km/h
    HIGH_SPEED = 50          # km/h
```

### Vehicle Simulator Configuration

Edit `car_a.py` or `car_b.py`:

```python
# Configuration
VEHICLE_ID = "A"              # Change vehicle ID
START_LAT = 12.9716          # Starting latitude
START_LON = 77.5946          # Starting longitude
SERVER_URL = "http://localhost:5000"
SCENARIO = "north"           # Movement scenario
```

Available scenarios:
- `north`: Move northward
- `south`: Move southward
- `east`: Move eastward
- `circuit`: Square circuit pattern
- `zigzag`: Zigzag pattern
- `variable_speed`: Varying speeds
- `accelerating`: Gradual acceleration

## 📊 API Endpoints

The server provides REST API endpoints for analytics:

```bash
# System status
GET http://localhost:5000/

# All active vehicles
GET http://localhost:5000/api/vehicles

# Specific vehicle data
GET http://localhost:5000/api/vehicle/<vehicle_id>

# Vehicle movement history
GET http://localhost:5000/api/vehicle/<vehicle_id>/history

# Recent alerts
GET http://localhost:5000/api/alerts

# System statistics
GET http://localhost:5000/api/stats
```

### Example API Usage

```bash
# Get all vehicles
curl http://localhost:5000/api/vehicles

# Get vehicle A data
curl http://localhost:5000/api/vehicle/A

# Get recent alerts
curl http://localhost:5000/api/alerts
```

## 🔧 Customization

### Adding More Vehicles

1. Copy `car_a.py` to `car_c.py`
2. Modify the configuration:
```python
VEHICLE_ID = "C"
START_LAT = 12.9720
START_LON = 77.5950
SCENARIO = "east"
```
3. Run the new simulator

### Creating Custom Scenarios

Add new scenarios to the vehicle simulator:

```python
elif scenario == "custom":
    self.speed = 50  # km/h
    move_per_second = (self.speed * 1000 / 3600)
    
    while True:
        # Your custom movement logic
        self.move_straight(move_per_second, 45)  # Northeast
        self.update_position()
        time.sleep(1)
```

### Changing Map Location

Edit `index.html`:

```javascript
// Change initial map center
const map = L.map('map').setView([YOUR_LAT, YOUR_LON], 15);
```

Edit vehicle simulators for starting positions:

```python
START_LAT = YOUR_LAT
START_LON = YOUR_LON
```

## 🐛 Troubleshooting

### Server won't start

**Error**: `Address already in use`
- **Solution**: Another process is using port 5000
```bash
# On Linux/macOS
lsof -i :5000
kill -9 <PID>

# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Vehicles not connecting

**Error**: `Connection failed`
- **Solution**: Ensure server is running and accessible
- Check SERVER_URL in vehicle simulators matches server address
- For network testing, replace `localhost` with your IP address

### No alerts showing

- **Check**: Vehicle ID is selected in web interface
- **Check**: At least 2 vehicles are running
- **Check**: Vehicles are moving toward each other (opposite directions)
- **Check**: Vehicles are within detection range (<150m)

### Map not loading

- **Check**: Internet connection (map tiles require internet)
- **Check**: Browser console for JavaScript errors (F12)
- **Alternative**: Use offline map tiles if needed

## 📈 Future Enhancements

Potential improvements for the system:

- [ ] Machine learning for collision prediction
- [ ] Integration with real GPS hardware
- [ ] Support for vehicle acceleration data
- [ ] Weather condition impact analysis
- [ ] Road network integration (OpenStreetMap)
- [ ] Multi-lane detection
- [ ] Vehicle classification (car, truck, motorcycle)
- [ ] Driver behavior analysis
- [ ] Mobile app (Android/iOS)
- [ ] Cloud deployment (AWS, Azure, GCP)
- [ ] Database integration for historical analysis
- [ ] Heat maps for accident-prone areas

## 📝 License

This project is provided for educational and research purposes.

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements.

## 📧 Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs (`vehicle_system.log`)
3. Check browser console for errors
4. Verify all dependencies are installed

## 🎓 Educational Use

This system is ideal for:
- IoT and embedded systems courses
- Real-time systems projects
- Transportation engineering research
- Computer science capstone projects
- Smart city initiatives

## ⚠️ Disclaimer

This is a demonstration/educational system. For production use in real vehicles, additional safety features, redundancy, and professional testing are required.

---

**Built with**: Python, Flask, Socket.IO, Leaflet.js, OpenStreetMap

**Version**: 2.0.0
