"""
Main entry point for Pico2W tracked arm car control system.
Initializes WiFi, HTTP server, WebSocket handler, and hardware controllers.
"""

import time
import json
import wifi
import socketpool
import board
import busio
from config_loader import ConfigLoader
from device_state import DeviceState
from http_handler import HTTPHandler
from websocket_handler import WebSocketHandler

print("=" * 50)
print("🤖 履带机械臂小车控制系统 v2.0")
print("   React 19 + CircuitPython 10.x")
print("=" * 50)

# Load configuration
print("\n[1/7] Loading configuration...")
config_loader = ConfigLoader("config.json")
config = config_loader.load()
print("✓ Configuration loaded successfully")

# Initialize device state
print("\n[2/7] Initializing device state...")
device_state = DeviceState(config)
print("✓ Device state initialized")

# Connect to WiFi
print("\n[3/7] Connecting to WiFi...")
ssid = config["wifi"]["ssid"]
password = config["wifi"]["password"]

print(f"  SSID: {ssid}")
try:
    wifi.radio.connect(ssid, password, timeout=30)
    print(f"✓ Connected to WiFi")
    print(f"  IP Address: {wifi.radio.ipv4_address}")
except Exception as e:
    print(f"✗ WiFi connection failed: {e}")
    print("  Please check WiFi credentials in config.json")
    device_state.add_error(f"WiFi connection failed: {e}")

# Initialize I2C for PCA9685 (servo controller)
print("\n[4/7] Initializing I2C bus...")
try:
    i2c_config = config["i2c"]
    sda_pin = getattr(board, i2c_config["sda_pin"])
    scl_pin = getattr(board, i2c_config["scl_pin"])
    i2c = busio.I2C(scl_pin, sda_pin)
    print(f"✓ I2C initialized on {i2c_config['sda_pin']}/{i2c_config['scl_pin']}")
except Exception as e:
    print(f"✗ I2C initialization failed: {e}")
    i2c = None
    device_state.add_error(f"I2C init failed: {e}")

# Initialize hardware controllers
print("\n[5/7] Initializing hardware controllers...")
controllers = {
    "servo": None,
    "track": None,
    "base": None
}

# Initialize servo controller
if i2c:
    try:
        from servo_controller import ServoController
        controllers["servo"] = ServoController(i2c, config)
    except Exception as e:
        print(f"✗ Servo controller failed: {e}")
        device_state.add_error(f"Servo init failed: {e}")

# Initialize track controller
try:
    from track_controller import TrackController
    controllers["track"] = TrackController(config)
except Exception as e:
    print(f"✗ Track controller failed: {e}")
    device_state.add_error(f"Track init failed: {e}")

# Initialize base rotation controller
try:
    from base_rotation_controller import BaseRotationController
    controllers["base"] = BaseRotationController(config)
except Exception as e:
    print(f"✗ Base rotation controller failed: {e}")
    device_state.add_error(f"Base init failed: {e}")

# Initialize handlers
print("\n[6/7] Initializing request handlers...")
http_handler = HTTPHandler(config, device_state)
ws_handler = WebSocketHandler(
    config, 
    device_state, 
    controllers.get("servo"),
    controllers.get("track"),
    controllers.get("base")
)
print("✓ HTTP and WebSocket handlers ready")

# Start HTTP/WebSocket server
print("\n[7/7] Starting HTTP/WebSocket server...")

try:
    from adafruit_httpserver import Server, Request, Response, Websocket
    
    pool = socketpool.SocketPool(wifi.radio)
    server = Server(pool, "/static", debug=True)
    
    active_websocket = None
    
    # Define HTTP routes
    @server.route("/api/status")
    def status_endpoint(request: Request):
        """GET /api/status"""
        result = http_handler.handle_status(request)
        return Response(request, result["body"], content_type="application/json")
    
    @server.route("/api/config")
    def config_endpoint(request: Request):
        """GET /api/config"""
        result = http_handler.handle_config(request)
        return Response(request, result["body"], content_type="application/json")
    
    @server.route("/api/health")
    def health_endpoint(request: Request):
        """GET /api/health"""
        result = http_handler.handle_health(request)
        return Response(request, result["body"], content_type="application/json")
    
    @server.route("/ws")
    def websocket_endpoint(request: Request):
        """WebSocket endpoint for real-time control"""
        global active_websocket
        
        if active_websocket is not None:
            try:
                active_websocket.close()
            except:
                pass
        
        ws = Websocket(request)
        active_websocket = ws
        
        print(f"[INFO] WebSocket client connected from {request.client_address}")
        # Return immediately - message processing will happen in main loop
        return ws
    
    # Start server
    server.start(str(wifi.radio.ipv4_address), config["server"]["port"])
    
    print("\n" + "=" * 50)
    print("✅ System started successfully!")
    print("=" * 50)
    print(f"\n📱 Control Interface: http://{wifi.radio.ipv4_address}:{config['server']['port']}/")
    print(f"📊 API Status: http://{wifi.radio.ipv4_address}:{config['server']['port']}/api/status")
    print(f"🔌 WebSocket: ws://{wifi.radio.ipv4_address}:{config['server']['port']}/ws")
    print("\n💡 All features ready:")
    print("   ✓ Track control (differential steering)")
    print("   ✓ Servo control (3-joint mechanical arm)")
    print("   ✓ Base rotation control")
    print("   ✓ Real-time status monitoring")
    print("\nPress Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Main server loop
    last_safety_check = time.monotonic()
    
    while True:
        try:
            server.poll()
            
            # Process WebSocket messages if connected
            if active_websocket is not None:
                try:
                    data = active_websocket.receive()
                    if data:
                        response = ws_handler.handle_message(data)
                        active_websocket.send_message(json.dumps(response))
                except OSError:
                    # No data available
                    pass
                except Exception as e:
                    print(f"[ERROR] WebSocket error: {e}")
                    try:
                        active_websocket.close()
                    except:
                        pass
                    active_websocket = None
            
            # Safety checks every 100ms
            current_time = time.monotonic()
            if current_time - last_safety_check > 0.1:
                # Safety timeout check
                last_cmd_ms = device_state.get_last_command_time()
                timeout_ms = config["safety"]["command_timeout_ms"]
                
                if last_cmd_ms > 0 and last_cmd_ms > timeout_ms:
                    print(f"[WARNING] Command timeout ({last_cmd_ms}ms) - stopping motors")
                    if controllers.get("track"):
                        controllers["track"].stop()
                    if controllers.get("base"):
                        controllers["base"].stop()
                    device_state.update_track_state(0, 0)
                    device_state.update_base_rotation_state("stop", 0)
                    device_state.update_last_command()
                
                # Check base idle sleep
                if controllers.get("base"):
                    controllers["base"].check_idle_sleep()
                
                last_safety_check = current_time
            
        except Exception as e:
            print(f"[ERROR] Server error: {e}")
            device_state.add_error(str(e))
        
        time.sleep(0.001)

except ImportError as e:
    print(f"\n✗ Failed to import adafruit_httpserver: {e}")
    print("\nPlease install required library:")
    print("  circup install adafruit_httpserver")
    print("\nSee LIBRARY_SETUP.md for detailed instructions")
    
except KeyboardInterrupt:
    print("\n\n⏹️  Shutdown requested...")
    if controllers.get("track"):
        controllers["track"].stop()
    if controllers.get("base"):
        controllers["base"].stop()
    print("✓ Motors stopped")
    print("✓ System shutdown complete")
    
except Exception as e:
    print(f"\n✗ Fatal error: {e}")
    import traceback
    traceback.print_exception(e)
    try:
        if controllers.get("track"):
            controllers["track"].stop()
        if controllers.get("base"):
            controllers["base"].stop()
    except:
        pass
