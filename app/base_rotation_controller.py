"""
Base rotation controller wrapper for DRV8837 motor driver.
Provides high-level interface for platform rotation with sleep mode.
"""

import board
import time
from motor_controller import DRV8837Controller


class BaseRotationController:
    """High-level base rotation control with sleep mode management"""
    
    def __init__(self, config):
        """
        Initialize base rotation controller
        
        Args:
            config: Motors configuration dict
        """
        base_cfg = config["motors"]["base_rotation"]
        
        self.controller = DRV8837Controller(
            in1_pin=getattr(board, base_cfg["in1_pin"]),
            in2_pin=getattr(board, base_cfg["in2_pin"]),
            sleep_pin=getattr(board, base_cfg["sleep_pin"])
        )
        
        self.idle_sleep_timeout = config.get("safety", {}).get("idle_sleep_ms", 5000) / 1000.0
        self.last_command_time = 0
        self.current_direction = "stop"
        
        print("✓ Base rotation controller initialized")
    
    def set_direction(self, direction, speed=100):
        """
        Set base rotation direction and speed
        
        Args:
            direction: 'cw', 'ccw', or 'stop'
            speed: Speed percentage (0-100)
        """
        self.last_command_time = time.monotonic()
        self.current_direction = direction
        
        if direction == "cw":
            self.controller.enable()
            self.controller.set_speed_cw(speed)
        elif direction == "ccw":
            self.controller.enable()
            self.controller.set_speed_ccw(speed)
        else:  # stop
            self.controller.brake()
            self.current_direction = "stop"
    
    def stop(self):
        """Stop base rotation"""
        self.set_direction("stop", 0)
    
    def check_idle_sleep(self):
        """
        Check if motor should enter sleep mode due to inactivity
        Should be called periodically from main loop
        """
        if self.current_direction == "stop":
            idle_time = time.monotonic() - self.last_command_time
            if idle_time > self.idle_sleep_timeout:
                self.controller.disable()
    
    def get_status(self):
        """Get current base rotation status"""
        return {
            "direction": self.current_direction,
            "speed": self.controller.current_speed,
            "sleeping": not (self.controller.sleep and self.controller.sleep.value)
        }
    
    def deinit(self):
        """Cleanup resources"""
        self.stop()
        self.controller.deinit()
