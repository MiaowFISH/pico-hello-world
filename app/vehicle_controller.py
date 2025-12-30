"""
车辆控制器模块
整合舵机控制器和电机控制器，提供统一的车辆控制接口
"""
import board
from servo_controller import ServoController
from motor_controller import TB6612Controller, DRV8837Controller


class VehicleController:
    """履带机械臂小车控制器"""
    
    def __init__(self, config):
        """
        初始化车辆控制器
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化舵机控制器（机械臂）
        print("\n初始化舵机控制器...")
        self.servo_ctrl = ServoController(
            frequency=config['pca9685']['frequency']
        )
        
        # 配置舵机
        for servo_cfg in config['servos']:
            self.servo_ctrl.add_servo(
                channel=servo_cfg['channel'],
                min_angle=servo_cfg['min_angle'],
                max_angle=servo_cfg['max_angle'],
                min_pulse=servo_cfg.get('min_pulse', 500),
                max_pulse=servo_cfg.get('max_pulse', 2500)
            )
            
            # 设置初始角度
            if 'initial_angle' in servo_cfg:
                self.servo_ctrl.set_angle(
                    servo_cfg['channel'], 
                    servo_cfg['initial_angle']
                )
        
        # 初始化履带控制器（TB6612）
        print("\n初始化履带控制器...")
        track_cfg = config['motors']['tracks']
        self.track_ctrl = TB6612Controller(
            pwma_pin=getattr(board, track_cfg['pwma_pin']),
            ain1_pin=getattr(board, track_cfg['ain1_pin']),
            ain2_pin=getattr(board, track_cfg['ain2_pin']),
            pwmb_pin=getattr(board, track_cfg['pwmb_pin']),
            bin1_pin=getattr(board, track_cfg['bin1_pin']),
            bin2_pin=getattr(board, track_cfg['bin2_pin']),
            stby_pin=getattr(board, track_cfg['stby_pin'])
        )
        
        # 初始化底盘旋转控制器（DRV8837）
        print("\n初始化底盘旋转控制器...")
        base_cfg = config['motors']['base_rotation']
        self.base_ctrl = DRV8837Controller(
            in1_pin=getattr(board, base_cfg['in1_pin']),
            in2_pin=getattr(board, base_cfg['in2_pin']),
            sleep_pin=getattr(board, base_cfg.get('sleep_pin')) if base_cfg.get('sleep_pin') else None
        )
        
        # 自动启用所有电机驱动器
        print("\n启用电机驱动器...")
        self.track_ctrl.enable()
        self.base_ctrl.enable()
        print("✅ 电机驱动器已启用")
        
        print("\n车辆控制器初始化完成！")
    
    # ========== 舵机控制方法 ==========
    
    def set_servo_angle(self, channel, angle, smooth=False):
        """设置舵机角度"""
        return self.servo_ctrl.set_angle(channel, angle, smooth)
    
    def get_servo_angle(self, channel):
        """获取舵机角度"""
        return self.servo_ctrl.get_angle(channel)
    
    def get_servo_info(self):
        """获取所有舵机信息"""
        return self.servo_ctrl.get_servo_info()
    
    def center_all_servos(self):
        """将所有舵机移到中心位置"""
        return self.servo_ctrl.center_all()
    
    def disable_servos(self, channel=None):
        """禁用舵机"""
        self.servo_ctrl.disable(channel)
    
    # ========== 履带控制方法 ==========
    
    def move_forward(self, speed=50):
        """前进"""
        self.track_ctrl.forward(speed)
    
    def move_backward(self, speed=50):
        """后退"""
        self.track_ctrl.backward(speed)
    
    def turn_left(self, speed=50):
        """左转"""
        self.track_ctrl.turn_left(speed)
    
    def turn_right(self, speed=50):
        """右转"""
        self.track_ctrl.turn_right(speed)
    
    def stop_tracks(self):
        """停止履带"""
        self.track_ctrl.stop()
    
    def set_track_speeds(self, left_speed, right_speed):
        """设置左右履带速度（差动转向）"""
        self.track_ctrl.set_motors(left_speed, right_speed)
    
    def get_track_status(self):
        """获取履带状态"""
        return self.track_ctrl.get_status()
    
    # ========== 底盘旋转控制方法 ==========
    
    def rotate_base_cw(self, speed=50):
        """顺时针旋转底盘"""
        self.base_ctrl.rotate_cw(speed)
    
    def rotate_base_ccw(self, speed=50):
        """逆时针旋转底盘"""
        self.base_ctrl.rotate_ccw(speed)
    
    def stop_base(self):
        """停止底盘旋转"""
        self.base_ctrl.stop()
    
    def set_base_rotation(self, speed):
        """设置底盘旋转速度"""
        self.base_ctrl.set_speed(speed)
    
    def get_base_status(self):
        """获取底盘状态"""
        return self.base_ctrl.get_status()
    
    # ========== 综合控制方法 ==========
    
    def stop_all(self):
        """停止所有运动"""
        self.track_ctrl.stop()
        self.base_ctrl.stop()
    
    def emergency_stop(self):
        """紧急停止"""
        self.stop_all()
        self.track_ctrl.standby()
        self.base_ctrl.disable()
    
    def get_all_status(self):
        """获取所有状态信息"""
        return {
            "servos": self.get_servo_info(),
            "tracks": self.get_track_status(),
            "base_rotation": self.get_base_status()
        }
    
    def deinit(self):
        """清理资源"""
        print("\n清理车辆控制器资源...")
        self.track_ctrl.deinit()
        self.base_ctrl.deinit()
        self.servo_ctrl.disable()
