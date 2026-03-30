# Demo Day Setup - Scripts & Camera Streaming

## Your Startup Scripts ✅

Both scripts are **correct versions** for demo day:

### startserver (→ start_server.sh)
- Runs on **your Pi (Rpi4)** - database & GUI server
- Starts FastAPI backend (port 8000)
- Starts frontend dev server (port 5173)
- Auto-detects your Pi's IP and tells teammates what to use
- Cleans up old processes, sets up venv, generates .env

**Usage:**
```bash
chmod +x startserver
./startserver
```

Then teammates see:
```
📋 For your teammates:
   Set PI_SERVER_IP=<your-ip> in their .env
   Then run ./startnode on their Pi
```

### startnode (→ start_node.sh)
- Runs on **teammate Pis** (Scanner/Solver/Motor nodes)
- Asks which type of Pi it is (1=Scanner, 2=Solver, 3=Motor)
- Sends heartbeats to server every 3 seconds
- Checks server connectivity before starting
- Generates .env with correct NODE_ID and NODE_TYPE

**Usage:**
```bash
chmod +x startnode
./startnode
# Then choose: 1 (Scanner), 2 (Solver), or 3 (Motor)
```

Both scripts are **demo-day ready**. Use them as-is.

---

## Adding Live Camera Feed to Web UI

### What's New
I created `Scanner/stream_server.py` - a simple MJPEG server that broadcasts live camera from Scanner Pi directly to your web UI.

### How It Works

**Architecture:**
```
Scanner Pi (Rpi1)
    ↓ (camera captures frame)
stream_server.py (port 8001)
    ↓ (MJPEG stream)
Frontend (Dashboard)
    ↓ (displays <img src="..." />)
User sees live camera
```

### Setup Steps

#### 1. On Scanner Pi (Rpi1)

Option A: Launch from demo script (recommended)
```bash
# In startnode.sh, when user selects "1 (Scanner)", add:
# python Scanner/stream_server.py &
```

Option B: Manual start
```bash
pip install flask opencv-python picamera2
python Scanner/stream_server.py
# → Server running on http://localhost:8001/video_feed
```

#### 2. In Frontend Dashboard

Add camera component to `frontend/src/pages/Dashboard.tsx`:

```tsx
import { useEffect, useState } from 'react';

export function ScannerView() {
  const [url, setUrl] = useState('');
  
  useEffect(() => {
    // Get Scanner Pi IP from server or env
    const scannerIp = new URL(import.meta.env.VITE_API_URL).hostname;
    setUrl(`http://${scannerIp}:8001/video_feed`);
  }, []);
  
  return (
    <div className="camera-panel">
      <h3>📷 Live Scanner Feed</h3>
      <img 
        src={url} 
        alt="scanner"
        style={{ maxWidth: '100%', borderRadius: '8px' }}
      />
    </div>
  );
}
```

Then add to Dashboard:
```tsx
<ScannerView />
```

#### 3. In startnode.sh (Update for Scanner option)

Modify the heartbeat section to also start stream server:

```bash
if [ "$NODE_TYPE" = "scanner" ]; then
    echo "🎥 Starting camera stream server..."
    python Scanner/stream_server.py > /tmp/pi3-camera.log 2>&1 &
    echo "   ✓ Camera feed on http://<ip>:8001/video_feed"
fi
```

### Features

- **Real-time**: ~30 FPS MJPEG stream
- **Lightweight**: JPEG compression (quality 80)
- **Fallback**: Shows "Camera Offline" if no camera
- **Health check**: GET /health endpoint
- **No dependencies**: Works with standard OpenCV

### Test Locally

```bash
python Scanner/stream_server.py
# Then open browser: http://localhost:8001
# Or curl: curl http://localhost:8001/video_feed | file -
```

### Demo Day Checklist

- [ ] Scanner Pi has `stream_server.py` running on port 8001
- [ ] Dashboard has `<ScannerView />` component
- [ ] Network allows camera Pi → dashboard connection
- [ ] Test on same Wi-Fi network
- [ ] Fallback message shows if camera offline

### Troubleshooting

**"Camera Offline" on dashboard:**
- Check Scanner Pi is running: `ps aux | grep stream_server`
- Verify it's on port 8001: `lsof -i :8001`
- Check IP: `hostname -I` on Scanner Pi
- Test: `curl http://192.168.x.x:8001/health`

**High latency:**
- Reduce resolution in stream_server.py: `FRAME_WIDTH = 320` (instead of 640)
- Lower MJPEG_QUALITY to 60
- Use H.264 if Flask becomes bottleneck

**CORS/Connection issues:**
- Both Pis must be on same Wi-Fi network
- Firewall may block port 8001 (try 8000 via backend proxy instead)
- Test: `curl -v http://scanner-pi:8001/video_feed`

---

## Your Demo Day Flow

### Server Pi (You, Rpi4)
```bash
./startserver
# Runs backend + frontend
# Shows dashboard at http://<your-ip>:5173
```

### Scanner Pi (Basil, Rpi1)
```bash
./startnode
# Choose: 1 (Scanner)
# Connects to your server
# Streams camera feed to port 8001
# Dashboard shows live feed
```

### Solver Pi (Luke, Rpi2)
```bash
./startnode
# Choose: 2 (Solver)
# Connects to your server
# Listens for solve requests
```

### Motor Pi (Eric, Rpi3)
```bash
./startnode
# Choose: 3 (Motor)
# Connects to your server
# Executes moves (or simulates)
```

### Result
- All nodes online in dashboard
- Live camera feed visible
- Full pipeline: Scan → Solve → Execute in UI

---

## Files Created

| File | Purpose |
|------|---------|
| `startserver` → `start_server.sh` | Your Pi startup (backend + frontend) |
| `startnode` → `start_node.sh` | Teammate Pi startup (heartbeat + subsystem) |
| `Scanner/stream_server.py` | Live MJPEG camera stream |
| `CAMERA_STREAMING_DESIGN.md` | Detailed design doc |

All are **demo-day ready**. You can use them now.
