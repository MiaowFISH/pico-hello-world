"""
HTTP handler for Pico2W tracked arm car.
Provides REST API endpoints for status, config, and health checks.
Serves static frontend files.
"""

import json


class HTTPHandler:
    """Handle HTTP requests for status, config, and static files"""
    
    def __init__(self, config, device_state):
        """
        Initialize HTTP handler
        
        Args:
            config: Loaded configuration dict
            device_state: Shared device state object
        """
        self.config = config
        self.device_state = device_state
    
    def handle_status(self, request):
        """GET /api/status - Return current device status"""
        try:
            status = {
                "wifi": self.device_state.get_wifi_status(),
                "servos": self.device_state.get_servo_states(),
                "tracks": self.device_state.get_track_state(),
                "base_rotation": self.device_state.get_base_rotation_state(),
                "last_command_ms": self.device_state.get_last_command_time(),
                "uptime_ms": self.device_state.get_uptime(),
                "errors": self.device_state.get_errors()
            }
            
            return self._json_response(status)
            
        except Exception as e:
            print(f"ERROR in handle_status: {e}")
            return self._error_response("Internal server error", 500)
    
    def handle_config(self, request):
        """GET /api/config - Return device configuration (without WiFi password)"""
        try:
            # Return safe configuration for frontend
            config_response = {
                "servos": [
                    {
                        "channel": s["channel"],
                        "name": s["name"],
                        "min_angle": s["min_angle"],
                        "max_angle": s["max_angle"],
                        "initial_angle": s["initial_angle"]
                    }
                    for s in self.config.get("servos", [])
                ],
                "speed_presets": self.config.get("speed_presets", {
                    "slow": 30,
                    "medium": 60,
                    "fast": 100
                }),
                "safety": {
                    "command_timeout_ms": self.config.get("safety", {}).get("command_timeout_ms", 2000)
                }
            }
            
            return self._json_response(config_response)
            
        except Exception as e:
            print(f"ERROR in handle_config: {e}")
            return self._error_response("Internal server error", 500)
    
    def handle_health(self, request):
        """GET /api/health - Simple health check"""
        try:
            health = {
                "status": "ok",
                "uptime_ms": self.device_state.get_uptime()
            }
            
            return self._json_response(health)
            
        except Exception as e:
            print(f"ERROR in handle_health: {e}")
            return self._error_response("Internal server error", 500)
    
    def _json_response(self, data, status=200):
        """Create JSON response with proper headers"""
        return {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)
        }
    
    def _error_response(self, message, status=400):
        """Create error response"""
        return self._json_response({
            "status": "error",
            "message": message
        }, status)
