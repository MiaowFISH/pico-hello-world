"""
Configuration loader for Pico2W tracked arm car.
Loads and validates config.json with schema validation.
"""

import json


class ConfigLoader:
    """Load and validate system configuration from config.json"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = None
        
    def load(self):
        """Load configuration from file with validation"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            self._validate()
            return self.config
            
        except OSError as e:
            print(f"ERROR: Failed to load config file: {e}")
            return self._get_default_config()
        except ValueError as e:
            print(f"ERROR: Invalid JSON in config file: {e}")
            return self._get_default_config()
    
    def _validate(self):
        """Validate required configuration sections"""
        required_sections = ['wifi', 'server', 'i2c', 'pca9685', 'servos', 'motors', 'safety']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate WiFi config
        if 'ssid' not in self.config['wifi'] or 'password' not in self.config['wifi']:
            raise ValueError("WiFi config must have 'ssid' and 'password'")
        
        # Validate servos
        if not isinstance(self.config['servos'], list) or len(self.config['servos']) == 0:
            raise ValueError("Servos must be a non-empty list")
        
        for servo in self.config['servos']:
            self._validate_servo(servo)
        
        # Validate motor config
        if 'tracks' not in self.config['motors']:
            raise ValueError("Missing tracks motor configuration")
        if 'base_rotation' not in self.config['motors']:
            raise ValueError("Missing base_rotation motor configuration")
        
        # Validate safety config
        if 'command_timeout_ms' not in self.config['safety']:
            raise ValueError("Missing command_timeout_ms in safety config")
    
    def _validate_servo(self, servo):
        """Validate individual servo configuration"""
        required_fields = ['channel', 'name', 'min_angle', 'max_angle', 'min_pulse', 'max_pulse', 'initial_angle']
        
        for field in required_fields:
            if field not in servo:
                raise ValueError(f"Servo missing required field: {field}")
        
        # Validate angle ranges
        if servo['min_angle'] >= servo['max_angle']:
            raise ValueError(f"Servo {servo['name']}: min_angle must be less than max_angle")
        
        if not (servo['min_angle'] <= servo['initial_angle'] <= servo['max_angle']):
            raise ValueError(f"Servo {servo['name']}: initial_angle must be between min_angle and max_angle")
        
        # Validate pulse ranges
        if servo['min_pulse'] >= servo['max_pulse']:
            raise ValueError(f"Servo {servo['name']}: min_pulse must be less than max_pulse")
    
    def _get_default_config(self):
        """Return default configuration as fallback"""
        print("WARNING: Using default configuration")
        return {
            "wifi": {
                "ssid": "CONFIGURE_ME",
                "password": "CONFIGURE_ME"
            },
            "server": {
                "port": 80
            },
            "i2c": {
                "sda_pin": "GP0",
                "scl_pin": "GP1"
            },
            "pca9685": {
                "frequency": 50
            },
            "servos": [
                {
                    "channel": 0,
                    "name": "Joint 1",
                    "min_angle": 0,
                    "max_angle": 180,
                    "min_pulse": 500,
                    "max_pulse": 2500,
                    "initial_angle": 90
                },
                {
                    "channel": 1,
                    "name": "Joint 2",
                    "min_angle": 0,
                    "max_angle": 180,
                    "min_pulse": 500,
                    "max_pulse": 2500,
                    "initial_angle": 90
                },
                {
                    "channel": 2,
                    "name": "Gripper",
                    "min_angle": 0,
                    "max_angle": 180,
                    "min_pulse": 500,
                    "max_pulse": 2500,
                    "initial_angle": 90
                }
            ],
            "motors": {
                "tracks": {
                    "pwma_pin": "GP6",
                    "ain1_pin": "GP7",
                    "ain2_pin": "GP8",
                    "pwmb_pin": "GP9",
                    "bin1_pin": "GP10",
                    "bin2_pin": "GP11",
                    "stby_pin": "GP12"
                },
                "base_rotation": {
                    "in1_pin": "GP14",
                    "in2_pin": "GP15",
                    "sleep_pin": "GP13"
                }
            },
            "speed_presets": {
                "slow": 30,
                "medium": 60,
                "fast": 100
            },
            "safety": {
                "command_timeout_ms": 2000,
                "idle_sleep_ms": 5000
            }
        }
    
    def get(self, *keys):
        """Get nested configuration value by keys
        
        Example: config.get('wifi', 'ssid')
        """
        if self.config is None:
            self.load()
        
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
