# Camera Streaming - Data Flow & Architecture

**How Basil's Camera Feed Gets to Your Dashboard**

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SCANNER PI (BASIL)                       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Raspberry Pi Camera (picamera2)                         │   │
│  │  Or USB Webcam fallback                                  │   │
│  │  • Captures RGB frames continuously                      │   │
│  │  • Resolution: 640x480 (configurable)                    │   │
│  │  • Rate: 30 FPS (configurable)                          │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ Raw camera frames                        │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  stream_server.py (Flask App)                            │   │
│  │  • Receives raw frames from camera                       │   │
│  │  • Encodes each frame to JPEG (quality 80)              │   │
│  │  • Assembles MJPEG stream with proper headers           │   │
│  │  • Listens on port 8001                                 │   │
│  │  • Routes:                                               │   │
│  │    - GET /video_feed → MJPEG stream                     │   │
│  │    - GET /health → JSON status                          │   │
│  │    - GET / → Web UI with embedded stream                │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ HTTP MJPEG stream                        │
│                       │ (continuous boundary-delimited JPEGs)    │
│                       │ Port 8001                                │
│                       ▼                                          │
│    ┌─────────────────────────────────┐                          │
│    │ Network (WiFi)                  │                          │
│    │ 192.168.x.x:8001/video_feed     │                          │
│    └────────────────┬────────────────┘                          │
│                     │                                            │
└─────────────────────┼────────────────────────────────────────────┘
                      │
      ┌───────────────┘
      │
      │ HTTP GET request + MJPEG response
      │ over WiFi network
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CENTRAL SERVER (YOU)                        │
│                         Port 5173                                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React Frontend / Dashboard.tsx                          │   │
│  │  • Loads when user opens dashboard                       │   │
│  │  • Renders ScannerCameraFeed component                   │   │
│  │  • Component reads VITE_SCANNER_IP env var              │   │
│  │    (e.g., 192.168.1.50)                                 │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ componentDidMount / useEffect            │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ScannerCameraFeed.tsx Component                         │   │
│  │                                                           │   │
│  │  1. useEffect hook runs on mount:                        │   │
│  │     - Constructs URL:                                    │   │
│  │       http://192.168.1.50:8001/video_feed              │   │
│  │                                                           │   │
│  │  2. Tests connectivity with Image preload:              │   │
│  │     const testImage = new Image()                        │   │
│  │     testImage.src = streamUrl                            │   │
│  │     testImage.onload → setState({ isOnline: true })     │   │
│  │                                                           │   │
│  │  3. Renders <img> element:                              │   │
│  │     <img src={streamUrl}                                │   │
│  │          alt="Live scanner camera feed" />              │   │
│  │                                                           │   │
│  │  4. Browser's built-in <img> handling:                  │   │
│  │     - Makes HTTP GET to /video_feed                     │   │
│  │     - Receives MJPEG boundary stream                    │   │
│  │     - Continuously updates with new JPEG frames        │   │
│  │                                                           │   │
│  │  5. Status indicators:                                  │   │
│  │     - Green badge "ONLINE" if connected                │   │
│  │     - Red badge "OFFLINE" if failed                    │   │
│  │     - Auto-retry up to 3 times                         │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                       │                                          │
│                       │ Rendered to DOM                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Browser Rendering Engine                               │   │
│  │  • Displays camera stream in real-time                   │   │
│  │  • Updates as new JPEG frames arrive                     │   │
│  │  • Shows status badges and indicators                    │   │
│  │  • User sees: Live camera feed at top of dashboard      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                      │
                      │ User sees on screen
                      │
                      ▼
                 📱 Your Browser
              "Live Scanner Feed"
              camera visible in real-time
```

---

## Network Communication Details

### HTTP Headers (MJPEG Stream)

**Request (from Frontend):**
```
GET /video_feed HTTP/1.1
Host: 192.168.1.50:8001
Accept: image/*
Connection: keep-alive
```

**Response (from Scanner Pi):**
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame
Cache-Control: no-cache, no-store, must-revalidate
Connection: keep-alive

--frame
Content-Type: image/jpeg
Content-Length: 8952

[JPEG binary data - frame 1]
--frame
Content-Type: image/jpeg
Content-Length: 9127

[JPEG binary data - frame 2]
--frame
Content-Type: image/jpeg
...
```

The browser receives a **stream** (not discrete files) and continuously parses MJPEG boundaries to update the image.

### Timing

**Typical latency breakdown:**

```
Basil's Camera
      ↓ 0-5ms (sensor capture)
stream_server.py
      ↓ 5-20ms (JPEG encode)
MJPEG stream (port 8001)
      ↓ 20-50ms (network transmission)
Your browser (img src)
      ↓ 0-10ms (browser render)
You see the frame
      
Total: ~50-100ms latency typical
(Not real-time but imperceptible to human eye)
```

---

## Code Walkthrough

### Backend (stream_server.py)

```python
# 1. CAMERA CAPTURE THREAD
while True:
    frame = cam.capture_array()  # Get raw RGB frame
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert to BGR
    
    with frame_lock:
        current_frame = frame.copy()  # Store for streaming thread
    
# 2. MJPEG STREAMING THREAD
def generate_mjpeg():
    while True:
        with frame_lock:
            if current_frame is not None:
                # Encode to JPEG
                ret, buffer = cv2.imencode('.jpg', current_frame, 
                                          [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    # Yield MJPEG boundary format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                           + frame_bytes + b'\r\n')

# 3. FLASK ROUTE
@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
```

### Frontend (ScannerCameraFeed.tsx)

```tsx
// 1. ON COMPONENT MOUNT
useEffect(() => {
    // Construct stream URL from Scanner Pi IP
    const streamUrl = `http://${scannerIp}:8001/video_feed`;
    
    // Test connectivity before rendering
    const testImage = new Image();
    testImage.onload = () => setIsOnline(true);
    testImage.onerror = () => setIsOnline(false);
    testImage.src = streamUrl;
}, [scannerIp, retryCount]);

// 2. RENDER <img> ELEMENT
<img
    src={streamUrl}  // Browser will fetch /video_feed and display MJPEG
    alt="Live scanner camera feed"
    onError={() => setIsOnline(false)}  // Handle offline
/>
```

When the browser renders `<img src="http://192.168.1.50:8001/video_feed">`:
1. Makes HTTP GET request
2. Receives MJPEG stream (never ends, continuous)
3. Parses boundaries between JPEGs
4. Updates image display with each new frame
5. Result: Video-like experience from static `<img>` tag

---

## Why MJPEG?

### MJPEG Advantages
✅ Works with standard `<img>` tag (no special player)  
✅ Works over basic HTTP (no WebSocket needed)  
✅ Browser handles all frame parsing  
✅ Good compression (JPEG format)  
✅ Widely supported  
✅ Simple to implement  

### MJPEG Disadvantages
❌ Higher bandwidth than H.264  
❌ Slightly higher latency than streaming protocols  
❌ More CPU on encoder  

**For demo day:** MJPEG is perfect - simple, reliable, impressive.

---

## Auto-Launch Flow (Demo Day)

### What Happens When Basil Runs `./startnode`

```bash
$ ./startnode
# Prompts: "Which Pi is this?"
# Basil chooses: 1 (Scanner)

# In start_node.sh:
if [ "$NODE_TYPE" = "scanner" ]; then
    python3 Scanner/stream_server.py > /tmp/pi3-camera.log 2>&1 &
    CAMERA_PID=$!
    sleep 1
    
    if kill -0 $CAMERA_PID 2>/dev/null; then
        echo "✓ Camera stream on port 8001"
    fi
fi

# stream_server.py starts:
# 1. Initializes picamera2
# 2. Creates Flask app
# 3. Starts frame capture thread
# 4. Starts Flask server on port 8001
# 5. Waits for browser requests
```

### What You See on Dashboard

```
┌────────────────────────────────────────┐
│ 📷 Live Scanner Feed      🟢 ONLINE    │
├────────────────────────────────────────┤
│                                        │
│        [Live Camera Feed               │
│         from Basil's Scanner]          │
│                                        │
│  Camera is detecting colors           │
│  in real-time                         │
│                                        │
└────────────────────────────────────────┘
```

---

## Verifying It Works

### Test 1: Camera Server Running
```bash
# On Basil's Pi
$ ps aux | grep stream_server
# Should see: python Scanner/stream_server.py

# Check port is listening
$ lsof -i :8001
# Should show Flask listening
```

### Test 2: Network Connectivity
```bash
# From your central server Pi
$ curl http://192.168.1.50:8001/health
# Response:
# {"status":"ok","camera":"online","camera_type":"picamera2","port":8001,...}
```

### Test 3: Stream Accessible
```bash
# From your browser
open http://192.168.1.50:8001
# Should see web UI with live camera
```

### Test 4: Dashboard Integration
```bash
# Navigate to your dashboard
open http://localhost:5173
# Should see "Live Scanner Feed" card at top
# Shows stream from http://192.168.1.50:8001/video_feed
```

---

## Summary

**Your question:** How does Basil's camera feed get from the Scanner Pi to your dashboard?

**The answer:**

1. Basil runs `./startnode` → chooses 1 (Scanner)
2. `stream_server.py` auto-launches on port 8001
3. It captures frames and broadcasts MJPEG stream
4. Dashboard component requests `http://scanner-ip:8001/video_feed`
5. Browser's `<img>` tag displays the MJPEG stream
6. You see live camera on dashboard in real-time

**That's it.** Simple, elegant, HTTP-based. 🎥

