"""
WebSocket handler for Pico2W tracked arm car.
Processes real-time control commands for tracks, servos, and base rotation.
"""

import json
from base_rotation_controller import BaseRotationController
from servo_controller import ServoController
from track_controller import TrackController
import time


class WebSocketHandler:
    """Handle WebSocket messages and dispatch commands to controllers"""
    
    def __init__(self, config, device_state, servo_controller: ServoController, track_controller: TrackController, base_controller: BaseRotationController):
        """
        Initialize WebSocket handler
        
        Args:
            config: Loaded configuration dict
            device_state: Shared device state object
            servo_controller: Servo controller instance
            track_controller: Track controller instance
            base_controller: Base rotation controller instance
        """
        self.config = config
        self.device_state = device_state
        self.servo_controller = servo_controller
        self.track_controller = track_controller
        self.base_controller = base_controller
        self.speed_presets = config.get("speed_presets", {
            "slow": 30,
            "medium": 60,
            "fast": 100
        })
    
    def handle_message(self, message_str):
        """
        Process incoming WebSocket message
        
        Args:
            message_str: JSON string message
            
        Returns:
            dict: Response message to send back
        """
        try:
            message = json.loads(message_str)
            action = message.get("action")
            
            print(f"[INFO] WebSocket command: {action}")
            
            # Update last command timestamp
            self.device_state.update_last_command()
            
            # Dispatch based on action
            if action == "ping":
                return self._handle_ping()
            elif action == "track":
                return self._handle_track(message)
            elif action == "servo":
                return self._handle_servo(message)
            elif action == "servo_batch":
                return self._handle_servo_batch(message)
            elif action == "servo_reset":
                return self._handle_servo_reset()
            elif action == "base":
                return self._handle_base(message)
            else:
                print(f"[WARNING] Unknown action: {action}")
                return self._error_response(action, "invalid_action", f"Unknown action: {action}")
        
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON decode failed: {e}")
            return self._error_response(None, "invalid_json", str(e))
        except Exception as e:
            print(f"[ERROR] handle_message exception: {e}")
            return self._error_response(None, "internal_error", str(e))
    
    def _handle_ping(self):
        """Handle ping heartbeat"""
        return {
            "status": "pong",
            "timestamp": int(time.monotonic() * 1000)
        }
    
    def _handle_track(self, message):
        """Handle track control commands"""
        try:
            # Check for shorthand command
            if "command" in message:
                command = message["command"]
                speed_name = message.get("speed", "medium")
                speed = self.speed_presets.get(speed_name, 60)
                
                if command == "forward":
                    left, right = speed, speed
                elif command == "backward":
                    left, right = -speed, -speed
                elif command == "left":
                    left, right = -speed, speed
                elif command == "right":
                    left, right = speed, -speed
                elif command == "stop":
                    left, right = 0, 0
                else:
                    return self._error_response("track", "invalid_command", f"Unknown command: {command}")
            else:
                # Direct speed control
                left = message.get("left", 0)
                right = message.get("right", 0)
            
            # Validate speed range
            if not (-100 <= left <= 100) or not (-100 <= right <= 100):
                return self._error_response("track", "speed_out_of_range", "Speed must be between -100 and 100")
            
            # Send to track controller
            if self.track_controller:
                self.track_controller.set_speeds(left, right)
                self.device_state.update_track_state(left, right)
            
            return self._success_response("track")
            
        except Exception as e:
            return self._error_response("track", "execution_error", str(e))
    
    def _handle_servo(self, message):
        """Handle single servo control"""
        try:
            channel = message.get("channel")
            angle = message.get("angle")
            
            if channel is None or angle is None:
                return self._error_response("servo", "missing_parameters", "channel and angle are required")
            
            # Get servo config for validation
            servo_config = self._get_servo_config(channel)
            if not servo_config:
                return self._error_response("servo", "channel_not_found", f"Servo channel {channel} not configured")
            
            # Clamp angle to configured range
            min_angle = servo_config["min_angle"]
            max_angle = servo_config["max_angle"]
            original_angle = angle
            angle = max(min_angle, min(max_angle, angle))
            
            # Send to servo controller
            if self.servo_controller:
                clamped = self.servo_controller.set_angle(channel, angle)
                if clamped is not None:
                    self.device_state.update_servo_state(channel, clamped)
            
            response = self._success_response("servo")
            if original_angle != angle:
                response["clamped_value"] = angle
                response["message"] = f"Angle clamped from {original_angle} to {angle}"
            
            return response
            
        except Exception as e:
            return self._error_response("servo", "execution_error", str(e))
    
    def _handle_servo_batch(self, message):
        """Handle batch servo update"""
        try:
            angles = message.get("angles", [])
            
            if not isinstance(angles, list):
                return self._error_response("servo_batch", "invalid_format", "angles must be a list")
            
            servos = self.config.get("servos", [])
            if len(angles) != len(servos):
                return self._error_response("servo_batch", "length_mismatch", 
                                           f"Expected {len(servos)} angles, got {len(angles)}")
            
            # Update all servos
            for i, angle in enumerate(angles):
                servo_config = servos[i]
                channel = servo_config["channel"]
                
                # Clamp angle
                clamped_angle = max(servo_config["min_angle"], min(servo_config["max_angle"], angle))
                
                if self.servo_controller:
                    clamped = self.servo_controller.set_angle(channel, clamped_angle)
                    if clamped is not None:
                        self.device_state.update_servo_state(channel, clamped)
            
            return self._success_response("servo_batch")
            
        except Exception as e:
            return self._error_response("servo_batch", "execution_error", str(e))
    
    def _handle_servo_reset(self):
        """Reset all servos to initial angles"""
        try:
            servos = self.config.get("servos", [])
            
            for servo_config in servos:
                channel = servo_config["channel"]
                initial_angle = servo_config.get("initial_angle", 90)
                
                if self.servo_controller:
                    clamped = self.servo_controller.set_angle(channel, initial_angle)
                    if clamped is not None:
                        self.device_state.update_servo_state(channel, clamped)
            
            return self._success_response("servo_reset")
            
        except Exception as e:
            return self._error_response("servo_reset", "execution_error", str(e))
    
    def _handle_base(self, message):
        """Handle base rotation control"""
        try:
            direction = message.get("direction", "stop")
            speed = message.get("speed", 100)
            
            if direction not in ["cw", "ccw", "stop"]:
                return self._error_response("base", "invalid_direction", 
                                           f"Direction must be 'cw', 'ccw', or 'stop', got '{direction}'")
            
            if not (0 <= speed <= 100):
                return self._error_response("base", "speed_out_of_range", "Speed must be between 0 and 100")
            
            # Send to base rotation controller
            if self.base_controller:
                self.base_controller.set_direction(direction, speed)
                self.device_state.update_base_rotation_state(direction, speed)
            
            return self._success_response("base")
            
        except Exception as e:
            return self._error_response("base", "execution_error", str(e))
    
    def _get_servo_config(self, channel):
        """Get servo configuration by channel"""
        servos = self.config.get("servos", [])
        for servo in servos:
            if servo["channel"] == channel:
                return servo
        return None
    
    def _success_response(self, action):
        """Create success response"""
        return {
            "status": "ok",
            "action": action,
            "timestamp": int(time.monotonic() * 1000)
        }
    
    def _error_response(self, action, error_code, message):
        """Create error response"""
        return {
            "status": "error",
            "action": action,
            "error": error_code,
            "message": message
        }
