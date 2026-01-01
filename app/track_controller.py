"""
Track controller wrapper for TB6612FNG motor driver.
Provides high-level interface for differential steering.
"""

import board
from motor_controller import TB6612Controller


class TrackController:
    """High-level track control with differential steering"""
    
    def __init__(self, config):
        """
        Initialize track controller
        
        Args:
            config: Motors configuration dict
        """
        track_cfg = config["motors"]["tracks"]
        
        self.controller = TB6612Controller(
            pwma_pin=getattr(board, track_cfg["pwma_pin"]),
            ain1_pin=getattr(board, track_cfg["ain1_pin"]),
            ain2_pin=getattr(board, track_cfg["ain2_pin"]),
            pwmb_pin=getattr(board, track_cfg["pwmb_pin"]),
            bin1_pin=getattr(board, track_cfg["bin1_pin"]),
            bin2_pin=getattr(board, track_cfg["bin2_pin"]),
            stby_pin=getattr(board, track_cfg["stby_pin"])
        )
        
        # Enable by default
        self.controller.enable()
        print("✓ Track controller initialized")
    
    def set_speeds(self, left_speed, right_speed):
        """
        Set track speeds with differential steering
        
        Args:
            left_speed: Left track speed (-100 to 100)
            right_speed: Right track speed (-100 to 100)
        """
        self.controller.set_motors(left_speed, right_speed)
    
    def stop(self):
        """Stop all track motors"""
        self.controller.stop()
    
    def get_status(self):
        """Get current track status"""
        return self.controller.get_status()
    
    def deinit(self):
        """Cleanup resources"""
        self.controller.deinit()
