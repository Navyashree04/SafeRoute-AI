# 🚀 QUICK START GUIDE

## Get Running in 5 Minutes!

### Step 1: Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### Step 2: Test the System (30 seconds)
```bash
python test_system.py
```

### Step 3: Start the Server (30 seconds)
```bash
python server.py
```
Leave this running and open a new terminal.

### Step 4: Start Car A (30 seconds)
```bash
python car_a.py
```
Leave this running and open another terminal.

### Step 5: Start Car B (30 seconds)
```bash
python car_b.py
```
This car moves in the opposite direction - collision course!

### Step 6: View the Map (1 minute)
1. Open `index.html` in your browser
2. Select "Vehicle A" or "Vehicle B" from dropdown
3. Watch the magic happen! 🎉

## What You'll See

- **Blue dots** = Your vehicle
- **Orange dots** = Other vehicles
- **Red dots** = DANGER! Collision warning
- **Colored trails** = Vehicle paths
- **Alerts panel** = Real-time warnings

## Test Different Scenarios

Edit the `SCENARIO` variable in car_a.py or car_b.py:

```python
SCENARIO = "north"      # Move north
SCENARIO = "south"      # Move south  
SCENARIO = "circuit"    # Square pattern
SCENARIO = "zigzag"     # Lane changes
```

## Add More Vehicles

```bash
# Terminal 4
python car_c.py
```

## Troubleshooting

**Server won't start?**
- Check if port 5000 is in use
- Kill the process: `lsof -i :5000` (Mac/Linux)

**No vehicles showing?**
- Wait 2-3 seconds for connection
- Check browser console (F12)
- Verify server is running

**No alerts?**
- Select your vehicle ID in dropdown
- Wait for vehicles to get close (<150m)
- Make sure they're moving toward each other

## Next Steps

- Read **README.md** for complete documentation
- Check **PROJECT_INFO.md** for technical details
- Modify **config.py** to customize behavior
- Explore the API at http://localhost:5000/api/vehicles

Enjoy your collision detection system! 🚗💨
