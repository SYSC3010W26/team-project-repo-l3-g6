# Scanner Pi Setup Guide - Live Camera Streaming

**For: Basil (Scanner Pi - Rpi1)**  
**Component: Camera Feed on Main Dashboard**

---

## Overview

Your Scanner Pi will:
1. Run the camera stream server on **port 8001**
2. Broadcast live MJPEG feed from your camera
3. Dashboard displays the stream in real-time
4. All automated via `./startnode` script

---

## Quick Start (Demo Day)

```bash
chmod +x startnode
./startnode
# When prompted: Choose "1" for Scanner Pi
# Stream auto-launches on port 8001
```

That's it! Dashboard will show live camera within 5 seconds.

---

## How It Works: Architecture

### Data Flow

```
[Your Camera on Rpi1]
        ↓ (picamera2 captures frame)
[stream_server.py - port 8001]
        ↓ (MJPEG encode)
[Browser requests: http://192.168.x.x:8001/video_feed]
        ↓ (continuous JPEG stream)
[Dashboard <img> element displays it]
        ↓
[User sees live color detection in real-time]
```

### Components

**1. Scanner/stream_server.py** (on your Pi)
- Captures frames from picamera2 (or USB camera fallback)
- Encodes frames as JPEG at quality 80
- Streams via Flask on port 8001
- Includes `/health` endpoint for status checking
- Falls back to "Camera Offline" pattern if no camera

**2. Dashboard Component** (frontend)
- `ScannerCameraFeed.tsx` displays the stream
- Shows green "ONLINE" badge when connected
- Shows red "OFFLINE" badge when stream unavailable
- Auto-retries connection 3 times
- Responsive: works on mobile/tablet/desktop

**3. start_node.sh** (your launcher)
- Detects you chose "Scanner Pi"
- Auto-starts `stream_server.py` in background
- Logs to `/tmp/pi3-camera.log`
- Cleans up on Ctrl+C

---

## Local Testing (Your Development)

### Before Demo Day

Test the stream locally on your Pi:

```bash
# Terminal 1: Start camera server
python Scanner/stream_server.py

# Terminal 2: Check it's running
curl http://localhost:8001/health
# Expected response:
# {"status":"ok","camera":"online","camera_type":"picamera2","port":8001,"fps":30,"quality":80}

# Browser: Navigate to http://localhost:8001
# Should see your live camera + "🎥 Scanner Camera Stream" page
```

---

## Demo Day Testing (Network)

### Test on Same Wi-Fi

**On your Scanner Pi:**
```bash
./startnode
# Choose: 1 (Scanner)
# Note your Pi's IP when prompted, e.g., 192.168.1.50
```

**On the central server Pi (from another terminal):**
```bash
# Test direct stream access
curl http://192.168.1.50:8001/health

# Open browser to central server dashboard:
# http://192.168.1.100:5173  (adjust IP as needed)
# Look for "Live Scanner Feed" card at the top
```

**What you should see:**
- Dashboard loads
- "Live Scanner Feed" card appears at top
- Camera feed shows in real-time
- Green "ONLINE" badge

---

## Configuration

### Environment Variables

These can be set before running `./startnode`:

```bash
# Frame rate (default: 30)
export SCANNER_STREAM_FPS=24

# JPEG quality 1-100 (default: 80, lower=smaller/faster)
export SCANNER_STREAM_QUALITY=70

# Port (default: 8001)
export SCANNER_STREAM_PORT=8001

# Then start
./startnode
```

### For Slow Networks

If stream is choppy or slow:

```bash
# Reduce quality
export SCANNER_STREAM_QUALITY=60

# Reduce FPS
export SCANNER_STREAM_FPS=15

# Both together:
export SCANNER_STREAM_QUALITY=60 SCANNER_STREAM_FPS=15
./startnode
```

---

## Troubleshooting

### "Camera Offline" on Dashboard

**Checklist:**

```bash
# 1. Is stream server running?
ps aux | grep stream_server
# Should see: python Scanner/stream_server.py

# 2. Is it listening on port 8001?
lsof -i :8001
# Should show process listening

# 3. Check logs
cat /tmp/pi3-camera.log
# Should show: "[Camera] ✓ Picamera2 online" or "[Camera] ✓ USB camera online"

# 4. Test health endpoint
curl http://192.168.1.50:8001/health
# Should respond with JSON showing camera status

# 5. Try direct stream
# Open browser to: http://192.168.1.50:8001
# Should show stream page with live feed
```

### "Connection refused" on Dashboard

**Likely causes:**

```bash
# 1. Wrong IP address
hostname -I
# Use this IP in dashboard, e.g., 192.168.1.50

# 2. Firewall blocking port 8001
# Check if port is open:
lsof -i :8001

# 3. Not on same Wi-Fi network
# Verify: ping 192.168.1.100 (from your Pi)
# Should respond if on same network

# 4. Restart both services
# On Scanner Pi:
./startnode  # Choose 1

# On central server Pi:
./startserver
```

### Slow / Choppy Stream

**Reduce bandwidth:**

```bash
export SCANNER_STREAM_QUALITY=50
export SCANNER_STREAM_FPS=15
./startnode
```

### Port Already in Use

```bash
# Kill existing process
lsof -ti :8001 | xargs kill -9

# Or use different port
export SCANNER_STREAM_PORT=8002
./startnode
```

### picamera2 Not Available

If you see: `[Camera] Picamera2 not available, trying USB camera...`

```bash
# Install picamera2
sudo apt update
sudo apt install -y python3-picamera2

# Or use USB camera (automatic fallback)
```

---

## What Dashboard Shows

### Live Scanner Feed Card

Located at the **top** of the Dashboard:

```
┌─────────────────────────────────────────┐
│ 📷 Live Scanner Feed          🟢 ONLINE │
├─────────────────────────────────────────┤
│                                         │
│     [Live camera feed showing          │
│      your cube detection in           │
│      real-time]                        │
│                                         │
│  🔴 REC - Scanner is capturing        │
│  (when session is active)               │
└─────────────────────────────────────────┘
```

**Status Indicators:**
- **🟢 ONLINE** = Camera stream connected
- **🔴 OFFLINE** = Camera not responding
- **🔴 REC** = Scanner is actively capturing (during scanning phase)

---

## Commands Reference

### Normal Operation

```bash
# Start as Scanner Pi
./startnode
# Choose: 1

# Stop (Ctrl+C)
```

### Manual Testing

```bash
# Start stream server standalone
python Scanner/stream_server.py

# Test connectivity
curl http://localhost:8001/health

# Check logs
cat /tmp/pi3-camera.log

# View stream in browser
open http://localhost:8001
# Or:
firefox http://localhost:8001
```

### Debugging

```bash
# Real-time logs
tail -f /tmp/pi3-camera.log

# Process status
ps aux | grep stream_server

# Port check
netstat -tlnp | grep 8001
# Or:
lsof -i :8001

# Kill stream server
pkill -f stream_server.py
```

---

## What to Tell the Demo Audience

> "This is the live camera feed from the Scanner Pi. As I place the scrambled cube in the scanner, it captures an image and analyzes the colors in real-time. The camera stream is broadcast directly to the central dashboard here, so you see exactly what the scanner sees—30 frames per second."

---

## Environment Info (For Support)

If something goes wrong, provide:

```bash
# Your Pi's IP
hostname -I

# Camera type
curl http://localhost:8001/health

# Logs
cat /tmp/pi3-camera.log

# Python version
python3 --version

# OpenCV version
python3 -c "import cv2; print(cv2.__version__)"

# Flask installed?
python3 -c "import flask; print(flask.__version__)"
```

---

## Summary

**Before Demo Day:**
1. ✅ Test locally: `python Scanner/stream_server.py`
2. ✅ Verify at: `http://localhost:8001`
3. ✅ Check health: `curl http://localhost:8001/health`

**Demo Day:**
1. Run: `./startnode` → Choose 1 (Scanner)
2. Dashboard shows camera at top
3. Green "ONLINE" badge appears
4. Live feed displays in real-time

You're good to go! 🎥
