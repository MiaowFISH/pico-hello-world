"""
Servo controller for PCA9685-based mechanical arm.
Manages 3-joint servo angles with bounds checking and interference detection.
"""


class ServoController:
    """Control servos via PCA9685 PWM driver"""
    
    def __init__(self, i2c, config):
        """
        Initialize servo controller
        
        Args:
            i2c: I2C bus instance
            config: Configuration dict with servos and pca9685 settings
        """
        from adafruit_pca9685 import PCA9685
        from adafruit_motor import servo
        
        self.config = config
        
        # Initialize PCA9685
        self.pca = PCA9685(i2c)
        self.pca.frequency = config["pca9685"]["frequency"]
        
        # Create servo instances and track current angles
        self.servos = []
        self.current_angles = {}
        
        for servo_cfg in config["servos"]:
            servo_obj = servo.Servo(
                self.pca.channels[servo_cfg["channel"]],
                min_pulse=servo_cfg["min_pulse"],
                max_pulse=servo_cfg["max_pulse"]
            )
            # Set initial angle
            initial = servo_cfg["initial_angle"]
            servo_obj.angle = initial
            self.servos.append({
                "obj": servo_obj,
                "config": servo_cfg
            })
            self.current_angles[servo_cfg["channel"]] = initial
        
        print(f"✓ Servo controller initialized ({len(self.servos)} servos)")
        print(f"  Interference checking enabled for channels 0-1")
    
    def _check_interference(self, channel, angle):
        """
        Check if servo angle would cause mechanical interference
        
        Based on mechanical arm interference model:
        - Servo 1 (ch 0) and Servo 2 (ch 1) have linkage interference
        - Lower limit: S1 + S2 >= 145
        - Upper limit: S1 + 6*S2 <= 630
        
        Args:
            channel: Channel being set
            angle: Proposed angle
            
        Returns:
            bool: True if safe, False if interference detected
        """
        # Only check interference for channels 0 and 1
        if channel not in [0, 1]:
            return True
        
        # Get angles for both servos
        s1 = angle if channel == 0 else self.current_angles.get(0)
        s2 = angle if channel == 1 else self.current_angles.get(1)
        
        # Need both angles to check
        if s1 is None or s2 is None:
            return True
        
        # Check lower limit interference
        if s1 + s2 < 145:
            print(f"[WARNING] Interference: Servo1({s1:.0f}) + Servo2({s2:.0f}) = {s1+s2:.0f} < 145")
            return False
        
        # Check upper limit interference
        if s1 + 6 * s2 > 630:
            print(f"[WARNING] Interference: Servo1({s1:.0f}) + 6*Servo2({s2:.0f}) = {s1+6*s2:.0f} > 630")
            return False
        
        return True
    
    def set_angle(self, channel, angle):
        """
        Set servo angle with bounds checking and interference detection
        
        Args:
            channel: Servo channel number (0-15)
            angle: Target angle in degrees
            
        Returns:
            float: Clamped angle value, or None if channel not found or interference
        """
        for servo_data in self.servos:
            if servo_data["config"]["channel"] == channel:
                cfg = servo_data["config"]
                
                # Clamp angle to configured range
                clamped = max(cfg["min_angle"], min(cfg["max_angle"], angle))
                
                # Check for mechanical interference
                if not self._check_interference(channel, clamped):
                    print(f"[ERROR] Channel {channel} angle {clamped:.0f}° blocked by interference")
                    return None
                
                # Set angle and update tracking
                servo_data["obj"].angle = clamped
                self.current_angles[channel] = clamped
                
                # Log angle changes
                if abs(angle - clamped) > 0.5:
                    print(f"[INFO] Channel {channel}: {angle:.0f}° clamped to {clamped:.0f}°")
                
                return clamped
        
        print(f"[ERROR] Channel {channel} not found")
        return None
    
    def get_servo_config(self, channel):
        """Get servo configuration by channel"""
        for servo_data in self.servos:
            if servo_data["config"]["channel"] == channel:
                return servo_data["config"]
        return None
    
    def reset_all(self):
        """Reset all servos to initial angles"""
        print("[INFO] Resetting all servos to initial positions")
        for servo_data in self.servos:
            cfg = servo_data["config"]
            channel = cfg["channel"]
            initial_angle = cfg.get("initial_angle", 90)
            
            # Use set_angle to ensure interference checking
            result = self.set_angle(channel, initial_angle)
            if result is None:
                print(f"[WARNING] Failed to reset channel {channel}")
    
    def get_status(self):
        """Get current status of all servos"""
        status = []
        for servo_data in self.servos:
            cfg = servo_data["config"]
            channel = cfg["channel"]
            status.append({
                "channel": channel,
                "current_angle": self.current_angles.get(channel, 0),
                "min_angle": cfg["min_angle"],
                "max_angle": cfg["max_angle"]
            })
        return status
