"""
============================================================
SYSC3010 L3-G6 — Socket.IO singleton
Done By : Saim Hashmi

Holds the shared AsyncServer instance so that both main.py
(ASGI composition) and individual routers (emit calls) can
import sio without triggering a circular import.

Usage:
    from backend.sio_instance import sio
============================================================
"""
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
