"""
Main entry point for Pico2W tracked arm car control system.
Initializes WiFi, HTTP server, WebSocket handler, and hardware controllers.
"""

import time
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
print("=" * 50)

# Load configuration
print("\n[1/6] Loading configuration...")
config_loader = ConfigLoader("config.json")
config = config_loader.load()
print("✓ Configuration loaded successfully")

# Initialize device state
print("\n[2/6] Initializing device state...")
device_state = DeviceState(config)
print("✓ Device state initialized")

# Connect to WiFi
print("\n[3/6] Connecting to WiFi...")
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
    # Continue anyway for development/testing
    device_state.add_error(f"WiFi connection failed: {e}")

# Initialize I2C for PCA9685 (servo controller)
print("\n[4/6] Initializing hardware controllers...")
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

# Initialize controllers (placeholders until implementation phases)
controllers = {
    "servo": None,   # Will be initialized in Phase 4 (User Story 2)
    "track": None,   # Will be initialized in Phase 3 (User Story 1)
    "base": None     # Will be initialized in Phase 5 (User Story 3)
}

print("  Note: Hardware controllers will be initialized in later phases")
print("  ✓ Controller infrastructure ready")

# Initialize handlers
print("\n[5/6] Initializing request handlers...")
http_handler = HTTPHandler(config, device_state)
ws_handler = WebSocketHandler(config, device_state, controllers)
print("✓ HTTP and WebSocket handlers ready")

# Note: adafruit_httpserver needs to be installed
print("\n[6/6] Starting HTTP/WebSocket server...")
print("\n" + "!" * 50)
print("⚠️  IMPORTANT: This requires adafruit_httpserver library")
print("!" * 50)
print("\nTo install:")
print("  1. Connect Pico via USB")
print("  2. Run: circup install adafruit_httpserver")
print("\nFor manual installation, see: LIBRARY_SETUP.md")
print("\n" + "=" * 50)

try:
    # Import adafruit_httpserver (will fail if not installed)
    from adafruit_httpserver import Server, Request, Response, Websocket
    
    # Create server
    pool = socketpool.SocketPool(wifi.radio)
    server = Server(pool, "/static", debug=True)
    
    # Store active websocket connection (only one allowed)
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
        
        # Close existing connection if any
        if active_websocket is not None:
            try:
                active_websocket.close()
            except:
                pass
        
        # Accept new WebSocket connection
        ws = Websocket(request)
        active_websocket = ws
        
        print(f"WebSocket client connected from {request.client_address}")
        
        try:
            while True:
                # Receive message (non-blocking with timeout)
                data = ws.receive(timeout=0.1, fail_silently=True)
                
                if data:
                    # Process message
                    response = ws_handler.handle_message(data)
                    # Send response
                    ws.send_message(str(response))
                
                # Check command timeout for safety
                last_cmd_ms = device_state.get_last_command_time()
                timeout_ms = config["safety"]["command_timeout_ms"]
                
                if last_cmd_ms > 0 and last_cmd_ms > timeout_ms:
                    # Safety timeout: stop all motors
                    print(f"⚠️  Command timeout ({last_cmd_ms}ms) - stopping motors")
                    if controllers.get("track"):
                        controllers["track"].stop()
                    if controllers.get("base"):
                        controllers["base"].stop()
                    device_state.update_track_state(0, 0)
                    device_state.update_base_rotation_state("stop", 0)
                    # Reset timer
                    device_state.update_last_command()
                
                time.sleep(0.01)  # Small delay to prevent busy-waiting
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            print("WebSocket client disconnected")
            if active_websocket == ws:
                active_websocket = None
    
    # Start server
    server.start(str(wifi.radio.ipv4_address), config["server"]["port"])
    
    print("\n" + "=" * 50)
    print("✅ System started successfully!")
    print("=" * 50)
    print(f"\n📱 Control Interface: http://{wifi.radio.ipv4_address}:{config['server']['port']}/")
    print(f"📊 API Status: http://{wifi.radio.ipv4_address}:{config['server']['port']}/api/status")
    print(f"🔌 WebSocket: ws://{wifi.radio.ipv4_address}:{config['server']['port']}/ws")
    print("\n💡 Tip: Access the control interface from your browser")
    print("   Frontend project location: frontend/")
    print("\nPress Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Main server loop
    while True:
        try:
            server.poll()
        except Exception as e:
            print(f"Server error: {e}")
            device_state.add_error(str(e))
        time.sleep(0.001)

except ImportError as e:
    print(f"\n✗ Failed to import adafruit_httpserver: {e}")
    print("\nPlease install required library:")
    print("  circup install adafruit_httpserver")
    print("\nSee LIBRARY_SETUP.md for detailed instructions")
    
except KeyboardInterrupt:
    print("\n\n⏹️  Shutdown requested...")
    # Emergency stop
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
    # Emergency stop
    try:
        if controllers.get("track"):
            controllers["track"].stop()
        if controllers.get("base"):
            controllers["base"].stop()
    except:
        pass
