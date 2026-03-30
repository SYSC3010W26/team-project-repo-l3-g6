#!/usr/bin/env python3
"""
Rubik's Cube Scanner Bridge — File Watcher to API Gateway

Monitors Scanner output (cube_state.json, cube_string.txt) and POSTs
results to backend API /scan/submit endpoint. Implements retry logic
and graceful error handling.

SYSC3010 L3-G6 — Saim Hashmi & Eric McFetridge
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Environment variables
SESSION_ID = os.getenv("SESSION_ID", None)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
SCANNER_OUTPUT_DIR = os.getenv("SCANNER_OUTPUT_DIR", ".")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds, exponential backoff
REQUEST_TIMEOUT = 5.0  # seconds

# Output file monitoring
CUBE_STATE_FILE = "cube_state.json"
CUBE_STRING_FILE = "cube_string.txt"

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
    """Configure logging for bridge daemon."""
    logger = logging.getLogger("scanner_bridge")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler with detailed format
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScanResult:
    """Parsed scan result from files."""
    state_string: str
    cube_state: Dict[str, list]
    is_valid: bool
    confidence: float
    
    @staticmethod
    def from_files(state_file: Path, json_file: Path) -> Optional["ScanResult"]:
        """Load and parse scan result from files.
        
        Returns None if files are invalid or incomplete.
        """
        try:
            # Read state string
            with open(state_file, "r") as f:
                state_string = f.read().strip()
            
            # Read cube state JSON
            with open(json_file, "r") as f:
                cube_state = json.load(f)
            
            # Validate state string format (54 characters)
            if len(state_string) != 54:
                logger.warning(
                    f"Invalid state string length: {len(state_string)} "
                    f"(expected 54). State: {state_string}"
                )
                return None
            
            # Compute confidence: percentage of recognized colours (not '?')
            all_colours = [c for face in cube_state.values() for c in face]
            recognized = sum(1 for c in all_colours if c != "?")
            confidence = recognized / len(all_colours) if all_colours else 0.0
            
            # Is valid: no '?' in state string AND all 6 faces present
            is_valid = "?" not in state_string and len(cube_state) == 6
            
            logger.info(
                f"Loaded scan result: {len(state_string)} chars, "
                f"{confidence:.1%} confidence, valid={is_valid}"
            )
            
            return ScanResult(
                state_string=state_string,
                cube_state=cube_state,
                is_valid=is_valid,
                confidence=confidence
            )
        
        except FileNotFoundError as e:
            logger.warning(f"File not found: {e.filename}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading scan result: {e}")
            return None

# ─────────────────────────────────────────────────────────────────────────────
# API COMMUNICATION
# ─────────────────────────────────────────────────────────────────────────────

class ScannerAPIClient:
    """HTTP client for posting scan results to backend API."""
    
    def __init__(self, base_url: str, session_id: int):
        self.base_url = base_url
        self.session_id = session_id
        self.endpoint = f"{base_url}/scan/submit"
    
    def post_scan(self, result: ScanResult) -> Tuple[bool, Optional[int]]:
        """POST scan result to API with retry logic.
        
        Returns:
            (success: bool, cube_state_id: Optional[int])
        """
        payload = {
            "session_id": self.session_id,
            "state_string": result.state_string,
            "is_valid": result.is_valid,
            "confidence": result.confidence,
        }
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"POST attempt {attempt}/{MAX_RETRIES} to {self.endpoint} "
                    f"with session_id={self.session_id}"
                )
                
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                # Success
                resp_data = response.json()
                cube_state_id = resp_data.get("cube_state_id")
                logger.info(
                    f"✓ POST /scan/submit succeeded: "
                    f"cube_state_id={cube_state_id}"
                )
                return True, cube_state_id
            
            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout on attempt {attempt}/{MAX_RETRIES} "
                    f"(timeout={REQUEST_TIMEOUT}s)"
                )
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"Connection error on attempt {attempt}/{MAX_RETRIES}: {e}"
                )
            
            except requests.exceptions.HTTPError as e:
                # Distinguish retryable vs non-retryable errors
                status = e.response.status_code
                
                if status == 404:
                    # Session not found — don't retry, likely stale session_id
                    logger.error(
                        f"✗ Session {self.session_id} not found (404). "
                        f"Start a new solve session on the frontend."
                    )
                    return False, None
                
                elif status == 400:
                    # Bad request — don't retry, issue is with scan data
                    try:
                        detail = e.response.json().get("detail", "Unknown")
                    except:
                        detail = str(e.response.text)
                    logger.error(
                        f"✗ Bad request (400): {detail}. "
                        f"State string: {result.state_string}"
                    )
                    return False, None
                
                elif status >= 500:
                    # Server error — retry
                    logger.warning(
                        f"Server error on attempt {attempt}/{MAX_RETRIES} "
                        f"({status})"
                    )
                else:
                    # Other client error
                    logger.error(f"HTTP {status}: {e.response.text}")
                    return False, None
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False, None
            
            # Wait before retry (exponential backoff)
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"Waiting {delay:.1f}s before retry...")
                time.sleep(delay)
        
        # All retries exhausted
        logger.error(f"✗ All {MAX_RETRIES} POST attempts failed.")
        return False, None

# ─────────────────────────────────────────────────────────────────────────────
# FILE MONITORING
# ─────────────────────────────────────────────────────────────────────────────

def monitor_and_post(output_dir: str, session_id: int) -> None:
    """Monitor Scanner output directory for new scans and POST to API.
    
    Watches for both cube_state.json and cube_string.txt to appear,
    then POSTs to /scan/submit. Blocks indefinitely (suitable for daemon).
    """
    
    if not SESSION_ID:
        logger.error(
            "SESSION_ID environment variable not set. "
            "Cannot POST scans without session_id. Exiting."
        )
        return
    
    output_path = Path(output_dir)
    state_file = output_path / CUBE_STRING_FILE
    json_file = output_path / CUBE_STATE_FILE
    
    logger.info(
        f"Starting Scanner Bridge v1.0\n"
        f"  API Base URL:       {API_BASE_URL}\n"
        f"  Session ID:         {session_id}\n"
        f"  Output Directory:   {output_path.absolute()}\n"
        f"  Watch Files:        {CUBE_STRING_FILE}, {CUBE_STATE_FILE}\n"
        f"  Max Retries:        {MAX_RETRIES}\n"
        f"  Retry Delay:        {RETRY_DELAY}s (exponential backoff)\n"
    )
    
    api_client = ScannerAPIClient(API_BASE_URL, session_id)
    
    last_scan_time = 0.0
    processed_scans = set()  # Track processed scans to avoid duplicates
    
    while True:
        try:
            # Check if both files exist and have been updated
            if state_file.exists() and json_file.exists():
                # Use file modification time to detect new scans
                state_mtime = state_file.stat().st_mtime
                json_mtime = json_file.stat().st_mtime
                
                # Both files must have been updated since last check
                scan_time = max(state_mtime, json_mtime)
                
                # Simple duplicate detection: if both files unchanged
                # since last successful POST, skip
                if scan_time > last_scan_time and scan_time not in processed_scans:
                    logger.info(
                        f"Detected new scan files "
                        f"({state_file.name} {state_file.stat().st_size} bytes, "
                        f"{json_file.name} {json_file.stat().st_size} bytes)"
                    )
                    
                    # Load and validate scan result
                    result = ScanResult.from_files(state_file, json_file)
                    
                    if result:
                        # POST to API
                        success, cube_state_id = api_client.post_scan(result)
                        
                        if success:
                            logger.info("Scan successfully posted to backend.")
                            last_scan_time = scan_time
                            processed_scans.add(scan_time)
                            
                            # Keep processed list bounded (don't grow indefinitely)
                            if len(processed_scans) > 100:
                                processed_scans = {max(processed_scans)}
                        else:
                            # POST failed, retries exhausted
                            logger.error("Could not post scan to API.")
                            # Don't mark as processed — will retry on next scan
                    else:
                        logger.warning("Scan files invalid or incomplete.")
                        processed_scans.add(scan_time)
                        last_scan_time = scan_time
            
            # Check periodically (don't spin CPU)
            time.sleep(1.0)
        
        except KeyboardInterrupt:
            logger.info("Shutting down (Ctrl+C).")
            break
        
        except Exception as e:
            logger.exception(f"Unexpected error in monitor loop: {e}")
            time.sleep(5.0)  # Backoff on unexpected error

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Entry point for scanner bridge daemon."""
    
    # Validate configuration
    if not SESSION_ID:
        logger.error(
            "SESSION_ID environment variable not set.\n"
            "Usage: SESSION_ID=123 python scanner_bridge.py\n"
            "       SESSION_ID=123 API_BASE_URL=http://192.168.1.100:8000 python scanner_bridge.py"
        )
        return 1
    
    try:
        session_id = int(SESSION_ID)
    except ValueError:
        logger.error(f"SESSION_ID must be an integer, got: {SESSION_ID}")
        return 1
    
    # Start monitoring
    monitor_and_post(SCANNER_OUTPUT_DIR, session_id)
    return 0

if __name__ == "__main__":
    exit(main())
