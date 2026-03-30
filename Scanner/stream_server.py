#!/usr/bin/env python3
"""
============================================================
Scanner Pi MJPEG Stream Server
M004 - Live Camera Streaming to Dashboard

Broadcasts live camera feed as MJPEG stream.
Accessible at: http://<scanner-pi-ip>:8001/video_feed

HOW TO RUN:
===========

Option 1: Local Testing (on any machine with camera)
    $ python Scanner/stream_server.py
    → Opens http://localhost:8001 in browser

Option 2: Scanner Pi via startnode.sh (Demo Day)
    $ ./startnode
    $ # Choose: 1 (Scanner)
    → stream_server.py auto-launches on port 8001
    → Check /tmp/pi3-camera.log for logs

Option 3: Manual on Scanner Pi
    $ ssh basil@192.168.x.x
    $ cd /path/to/project
    $ python Scanner/stream_server.py
    → Stream available at http://192.168.x.x:8001/video_feed

INTEGRATION:
=============

Frontend sees stream at:
    <img src="http://SCANNER_IP:8001/video_feed" />

Dashboard component automatically connects to:
    http://<scanner-ip>:8001/video_feed

Environment Variables:
    SCANNER_STREAM_PORT=8001 (default)
    SCANNER_STREAM_FPS=30 (default)
    SCANNER_STREAM_QUALITY=80 (default JPEG quality 1-100)

Prerequisites:
    pip install flask opencv-python picamera2
    # Falls back to USB camera if picamera2 unavailable

TROUBLESHOOTING:
=================

1. "Camera Offline" on Dashboard
   → Check: ps aux | grep stream_server
   → Check: lsof -i :8001
   → Check: curl http://192.168.x.x:8001/health

2. Connection refused
   → Verify Scanner Pi IP: hostname -I
   → Verify firewall allows port 8001
   → Check same Wi-Fi network

3. Slow stream / High latency
   → Reduce resolution in this file (FRAME_WIDTH/HEIGHT)
   → Lower SCANNER_STREAM_QUALITY env var

4. Port already in use
   → Kill: lsof -ti :8001 | xargs kill
   → Or set: SCANNER_STREAM_PORT=8002
============================================================
"""
import cv2
import threading
import time
import os
import sys
from flask import Flask, Response

app = Flask(__name__)

# Configuration from environment
PORT = int(os.getenv('SCANNER_STREAM_PORT', 8001))
TARGET_FPS = int(os.getenv('SCANNER_STREAM_FPS', 30))
JPEG_QUALITY = int(os.getenv('SCANNER_STREAM_QUALITY', 80))
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Global frame buffer
frame_lock = threading.Lock()
current_frame = None
fps_counter = 0
last_update = time.time()
camera_online = False
camera_type = "unknown"


def capture_frames_picamera2():
    """Capture from Raspberry Pi camera (picamera2) - preferred for Rpi"""
    global current_frame, fps_counter, last_update, camera_online, camera_type
    
    try:
        from picamera2 import Picamera2
        from libcamera import controls
        
        print("[Camera] Initializing Picamera2...")
        cam = Picamera2()
        config = cam.create_preview_configuration(
            main={"format": 'XRGB8888', "size": (FRAME_WIDTH, FRAME_HEIGHT)}
        )
        cam.configure(config)
        cam.set_controls({controls.Brightness: 0.2})
        cam.start()
        camera_online = True
        camera_type = "picamera2"
        print("[Camera] ✓ Picamera2 online")
        
        frame_time = 1.0 / TARGET_FPS
        last_frame_time = time.time()
        
        while True:
            now = time.time()
            if now - last_frame_time < frame_time:
                time.sleep(0.001)
                continue
            
            frame = cam.capture_array()
            if frame is not None:
                # Convert XRGB to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Add FPS counter
                fps_counter += 1
                if now - last_update >= 1.0:
                    fps = fps_counter / (now - last_update)
                    cv2.putText(frame, f"{fps:.1f} FPS", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    fps_counter = 0
                    last_update = now
                
                with frame_lock:
                    current_frame = frame.copy()
            
            last_frame_time = now
            
    except ImportError:
        print("[Camera] Picamera2 not available, trying USB camera...")
        capture_frames_usb()
    except Exception as e:
        print(f"[Camera] Error with Picamera2: {e}")
        camera_online = False
        capture_frames_usb()


def capture_frames_usb():
    """Fallback to USB camera"""
    global current_frame, fps_counter, last_update, camera_online, camera_type
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Camera] No USB camera found, showing offline pattern")
        camera_online = False
        camera_type = "offline"
        capture_frames_offline()
        return
    
    print("[Camera] ✓ USB camera online")
    camera_online = True
    camera_type = "usb"
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    
    frame_time = 1.0 / TARGET_FPS
    last_frame_time = time.time()
    
    while True:
        now = time.time()
        if now - last_frame_time < frame_time:
            time.sleep(0.001)
            continue
        
        ret, frame = cap.read()
        if ret:
            fps_counter += 1
            if now - last_update >= 1.0:
                fps = fps_counter / (now - last_update)
                cv2.putText(frame, f"{fps:.1f} FPS", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                fps_counter = 0
                last_update = now
            
            with frame_lock:
                current_frame = frame.copy()
        
        last_frame_time = now
    
    cap.release()


def capture_frames_offline():
    """Generate offline pattern when no camera available"""
    global current_frame
    
    while True:
        frame = cv2.Mat(FRAME_HEIGHT, FRAME_WIDTH, cv2.CV_8UC3, (30, 30, 30))
        cv2.putText(frame, "CAMERA OFFLINE", (FRAME_WIDTH//2 - 180, FRAME_HEIGHT//2 - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
        cv2.putText(frame, "Check stream_server.py on Scanner Pi", 
                    (FRAME_WIDTH//2 - 220, FRAME_HEIGHT//2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
        with frame_lock:
            current_frame = frame
        time.sleep(0.5)


def generate_mjpeg():
    """Generate MJPEG stream"""
    global current_frame
    
    while True:
        with frame_lock:
            if current_frame is not None:
                ret, buffer = cv2.imencode('.jpg', current_frame, 
                                          [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                           + frame_bytes + b'\r\n')
        time.sleep(0.001)


@app.route('/video_feed')
def video_feed():
    """MJPEG stream endpoint - use this in frontend"""
    return Response(
        generate_mjpeg(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
        }
    )


@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'camera': 'online' if camera_online else 'offline',
        'camera_type': camera_type,
        'port': PORT,
        'fps': TARGET_FPS,
        'quality': JPEG_QUALITY,
    }


@app.route('/')
def index():
    """Info page - navigate to http://localhost:8001 to see this"""
    status_color = '#22c55e' if camera_online else '#ef4444'
    status_text = 'ONLINE' if camera_online else 'OFFLINE'
    status_dot = '🟢' if camera_online else '🔴'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scanner Pi - Stream Server</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #e0e0e0;
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
                color: #00d4ff;
                font-size: 2em;
            }}
            .stream-section {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                border: 1px solid rgba(0, 212, 255, 0.3);
                margin-bottom: 15px;
            }}
            .info {{
                background: rgba(0, 212, 255, 0.05);
                padding: 15px;
                border-radius: 8px;
                font-size: 0.9em;
            }}
            .info p {{
                margin: 8px 0;
            }}
            .status {{
                display: inline-block;
                padding: 4px 12px;
                background: rgba({status_color if camera_online else '#ef4444'}, 0.2);
                border: 1px solid rgba({status_color if camera_online else '#ef4444'}, 0.4);
                border-radius: 20px;
                font-size: 0.85em;
                color: {status_color};
            }}
            code {{
                background: rgba(0, 0, 0, 0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Courier New', monospace;
                color: #00d4ff;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 Scanner Pi Stream Server</h1>
            
            <div class="stream-section">
                <img src="/video_feed" alt="Scanner camera feed" />
                <div class="info">
                    <p><strong>Camera Status:</strong> <span class="status">{status_dot} {status_text}</span></p>
                    <p><strong>Camera Type:</strong> {camera_type}</p>
                    <p><strong>Frame Rate:</strong> {TARGET_FPS} FPS</p>
                    <p><strong>JPEG Quality:</strong> {JPEG_QUALITY}</p>
                    <p><strong>Resolution:</strong> {FRAME_WIDTH}x{FRAME_HEIGHT}</p>
                </div>
            </div>

            <div style="background: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;">
                <h2 style="color: #00d4ff; margin-bottom: 15px;">📡 Frontend Integration</h2>
                <p style="margin-bottom: 10px;">Use this URL in the Dashboard:</p>
                <code style="display: block; padding: 10px; background: rgba(0, 0, 0, 0.3); border-radius: 6px; overflow-x: auto; margin-bottom: 15px; word-break: break-all;">
                    http://{{'{{'}}SCANNER_PI_IP{{'}}'}}/8001/video_feed
                </code>
                <p style="font-size: 0.9em; color: #00d4ff;">Example: http://192.168.1.50:8001/video_feed</p>
            </div>

            <div style="background: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                <h2 style="color: #00d4ff; margin-bottom: 15px;">🔧 API Endpoints</h2>
                <p style="margin-bottom: 10px;"><strong>Stream:</strong> <code>/video_feed</code> - MJPEG stream (use in img src)</p>
                <p><strong>Health:</strong> <code><a href="/health" style="color: #00d4ff; text-decoration: none;">/health</a></code> - JSON status check</p>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == '__main__':
    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║         Scanner Pi MJPEG Stream Server                          ║
    ║         M004 - Live Camera Streaming to Dashboard              ║
    ╚════════════════════════════════════════════════════════════════╝
    
    📡 Starting stream server on port {PORT}...
    
    🔗 Access points:
       • Web UI:  http://localhost:{PORT}
       • Stream:  http://localhost:{PORT}/video_feed
       • Health:  http://localhost:{PORT}/health
    
    ⚙️  Configuration:
       • Frame rate: {TARGET_FPS} FPS
       • JPEG quality: {JPEG_QUALITY}
       • Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}
    
    💡 Frontend Integration:
       <img src="http://SCANNER_IP:8001/video_feed" />
    
    ⌨️  Press Ctrl+C to stop
    """)
    
    # Start frame capture in background
    capture_thread = threading.Thread(
        target=capture_frames_picamera2,
        daemon=True
    )
    capture_thread.start()
    
    # Give camera time to initialize
    time.sleep(1)
    
    # Start Flask app
    try:
        app.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Stream server stopped")
        sys.exit(0)
