# Live Camera Feed on Web UI - Design & Implementation Guide

## Architecture Overview

To show live camera feed from the Scanner Pi on the web UI, you need:

1. **Scanner Pi (Rpi1)** - Capture camera frames and encode as MJPEG stream
2. **Backend API** - Proxy the stream or WebSocket bridge
3. **Frontend UI** - Display the stream with OpenCV overlay (detected colors)

## Option A: MJPEG Stream (Simplest - Recommended for Demo Day)

### How it works
- Scanner Pi streams MJPEG directly from OpenCV (easiest, no extra dependencies)
- Frontend displays `<img src="http://scanner-pi:8001/video_feed" />` or `<video />`
- Minimal latency, widely supported

### Implementation

#### 1. Scanner Pi - Create MJPEG Server (Scanner/stream_server.py)

```python
#!/usr/bin/env python3
"""
MJPEG Stream Server for live camera feed
Broadcasts detected colors and current face overlay
"""
import cv2
import threading
from flask import Flask, Response
from Scanner import Scanner

app = Flask(__name__)
scanner = Scanner()
frame_lock = threading.Lock()
current_frame = None

def capture_frames():
    global current_frame
    while True:
        frame = scanner.capture_frame()  # OpenCV Mat
        if frame is not None:
            with frame_lock:
                current_frame = frame
        cv2.waitKey(1)

def generate_mjpeg():
    """Generator for MJPEG stream"""
    global current_frame
    while True:
        if current_frame is not None:
            with frame_lock:
                ret, buffer = cv2.imencode('.jpg', current_frame)
                frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n'
                   + frame + b'\r\n')
        else:
            cv2.waitKey(100)

@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start frame capture thread
    t = threading.Thread(target=capture_frames, daemon=True)
    t.start()
    
    # Start MJPEG server on port 8001
    app.run(host='0.0.0.0', port=8001, threaded=True)
```

#### 2. Backend API - Proxy Endpoint (backend/routers/scanner.py - new)

```python
@router.get("/camera_feed")
async def camera_feed():
    """
    Proxy Scanner Pi camera feed
    Frontend: GET /scanner/camera_feed
    """
    # Option A: Direct client-side request (no proxy needed)
    # Client fetches directly from http://scanner-pi:8001/video_feed
    
    # Option B: Proxy through backend (if same-origin CORS issues)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("http://rpi1-scanner:8001/video_feed", timeout=5)
            return StreamingResponse(
                iter([r.content]),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Camera unavailable: {e}")
```

#### 3. Frontend - Display Stream (frontend/src/components/ScannerView.tsx)

```tsx
import { useEffect, useState } from 'react';

export function ScannerView() {
  const [cameraUrl, setCameraUrl] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Try direct connection to Scanner Pi
    // Fallback: use backend proxy at /scanner/camera_feed
    const url = `http://${import.meta.env.VITE_SCANNER_IP || 'localhost'}:8001/video_feed`;
    setCameraUrl(url);
    
    // Test connection
    const img = new Image();
    img.onload = () => setIsConnected(true);
    img.onerror = () => setIsConnected(false);
    img.src = url;
  }, []);

  return (
    <div className="scanner-view">
      <h2>Live Scanner Feed</h2>
      {isConnected ? (
        <img
          src={cameraUrl}
          alt="Scanner camera feed"
          style={{ maxWidth: '100%', borderRadius: '8px' }}
        />
      ) : (
        <div className="error">
          <p>Camera offline - check Scanner Pi connection</p>
        </div>
      )}
      <p className="meta">Detecting colors in real-time...</p>
    </div>
  );
}
```

#### 4. Dashboard Integration (frontend/src/pages/Dashboard.tsx)

```tsx
import { ScannerView } from '../components/ScannerView';

export function Dashboard() {
  return (
    <div className="dashboard-grid">
      <div className="left-panel">
        <ScannerView />  {/* ← Add camera feed here */}
      </div>
      <div className="right-panel">
        {/* Existing controls, status, etc. */}
      </div>
    </div>
  );
}
```

## Option B: WebSocket Stream (More Complex - Better for Production)

If you need bi-directional control (e.g., trigger scan, adjust focus), use WebSocket:

1. Scanner Pi sends JPEG frames as base64 over WebSocket
2. Backend relays via Socket.IO
3. Frontend decodes and displays

Pros:
- Single connection
- Can send commands back to scanner
- Works through proxies

Cons:
- More bandwidth (base64 encoding overhead)
- Slightly higher latency
- More complex code

## Configuration

### .env variables
```bash
VITE_SCANNER_IP=192.168.1.50    # Scanner Pi IP
VITE_SCANNER_PORT=8001           # MJPEG stream port
SCANNER_STREAM_URL=http://rpi1-scanner:8001/video_feed
```

### Docker Compose (if needed)
```yaml
scanner-mjpeg:
  image: raspberrypi/python:3.11-slim
  command: python Scanner/stream_server.py
  ports:
    - "8001:8001"
  environment:
    - CAMERA_INDEX=0
```

## Demo Day Checklist

- [ ] Scanner Pi running `Scanner/stream_server.py` on port 8001
- [ ] Frontend displaying `<ScannerView />` component
- [ ] Camera feed shows in real-time with color overlays
- [ ] Handle offline gracefully (show "Camera offline" message)
- [ ] Test on same Wi-Fi network (IP reachability)

## Troubleshooting

**"Camera offline" error:**
- Check Scanner Pi is running: `ps aux | grep stream_server`
- Verify IP: `hostname -I` on Scanner Pi
- Test connection: `curl http://scanner-pi:8001/video_feed`

**Latency too high:**
- Reduce frame resolution in Scanner.py (CAPTURE_WIDTH/HEIGHT)
- Drop FPS (add sleep in capture loop)
- Use H.264 codec instead of JPEG

**CORS issues (frontend can't access):**
- Use backend proxy endpoint `/scanner/camera_feed`
- Add CORS headers to MJPEG server
- Or use WebSocket approach

## Next Steps

Choose Option A (MJPEG) for simplicity. If you implement it:

1. Add `stream_server.py` to Scanner/ directory
2. Update `startnode.sh` to launch stream server on Scanner Pi
3. Create `ScannerView` component in frontend
4. Embed in Dashboard

Would you like me to implement the full MJPEG stream setup for you?
