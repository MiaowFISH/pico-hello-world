"""
Device state management for Pico2W tracked arm car.
Centralizes state tracking for WiFi, servos, motors, and system status.
"""

import time
import wifi


class DeviceState:
    """Manage and track device state"""
    
    def __init__(self, config):
        """Initialize device state"""
        self.config = config
        self.start_time = time.monotonic()
        self.last_command_time = 0
        self.errors = []
        
        # Initialize servo states
        self.servo_states = {}
        for servo in config.get("servos", []):
            self.servo_states[servo["channel"]] = {
                "channel": servo["channel"],
                "name": servo["name"],
                "current_angle": servo.get("initial_angle", 90),
                "min_angle": servo["min_angle"],
                "max_angle": servo["max_angle"]
            }
        
        # Initialize track state
        self.track_state = {
            "left_speed": 0,
            "right_speed": 0,
            "enabled": True
        }
        
        # Initialize base rotation state
        self.base_rotation_state = {
            "direction": "stop",
            "speed": 0,
            "sleeping": True
        }
    
    def get_wifi_status(self):
        """Get current WiFi status"""
        try:
            connected = wifi.radio.connected
            ip = str(wifi.radio.ipv4_address) if connected else None
            
            # Try to get RSSI (signal strength)
            rssi = None
            try:
                if connected and hasattr(wifi.radio, 'ap_info'):
                    rssi = wifi.radio.ap_info.rssi
            except:
                pass
            
            return {
                "connected": connected,
                "ssid": self.config.get("wifi", {}).get("ssid", ""),
                "ip_address": ip,
                "rssi": rssi
            }
        except Exception as e:
            print(f"ERROR getting WiFi status: {e}")
            return {
                "connected": False,
                "ssid": "",
                "ip_address": None,
                "rssi": None
            }
    
    def get_servo_states(self):
        """Get all servo states as list"""
        return list(self.servo_states.values())
    
    def update_servo_state(self, channel, angle):
        """Update servo state"""
        if channel in self.servo_states:
            self.servo_states[channel]["current_angle"] = angle
    
    def get_track_state(self):
        """Get track motor state"""
        return self.track_state.copy()
    
    def update_track_state(self, left_speed, right_speed):
        """Update track state"""
        self.track_state["left_speed"] = left_speed
        self.track_state["right_speed"] = right_speed
    
    def get_base_rotation_state(self):
        """Get base rotation state"""
        return self.base_rotation_state.copy()
    
    def update_base_rotation_state(self, direction, speed):
        """Update base rotation state"""
        self.base_rotation_state["direction"] = direction
        self.base_rotation_state["speed"] = speed
        self.base_rotation_state["sleeping"] = (direction == "stop")
    
    def update_last_command(self):
        """Update timestamp of last command"""
        self.last_command_time = time.monotonic()
    
    def get_last_command_time(self):
        """Get milliseconds since last command"""
        if self.last_command_time == 0:
            return -1
        return int((time.monotonic() - self.last_command_time) * 1000)
    
    def get_uptime(self):
        """Get system uptime in milliseconds"""
        return int((time.monotonic() - self.start_time) * 1000)
    
    def add_error(self, error_message):
        """Add error to error list (keep last 10)"""
        print(f"[ERROR] Device error: {error_message}")
        self.errors.append({
            "message": error_message,
            "timestamp": time.monotonic()
        })
        # Keep only last 10 errors
        if len(self.errors) > 10:
            self.errors.pop(0)
    
    def get_errors(self):
        """Get recent error messages"""
        return [e["message"] for e in self.errors]
    
    def clear_errors(self):
        """Clear error list"""
        self.errors = []
