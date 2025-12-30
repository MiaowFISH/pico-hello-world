"""
舵机控制器模块
用于控制连接到PCA9685的舵机，支持角度限位配置
"""
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import time


class ServoController:
    """舵机控制器类"""
    
    def __init__(self, i2c=None, frequency=50):
        """
        初始化舵机控制器
        
        Args:
            i2c: I2C总线对象，如果为None则创建默认I2C总线
            frequency: PWM频率，默认50Hz（舵机标准频率）
        """
        if i2c is None:
            i2c = busio.I2C(board.GP1, board.GP0)  # SCL, SDA
        
        self.pca = PCA9685(i2c)
        self.pca.frequency = frequency
        
        # 存储舵机对象
        self.servos = {}
        # 存储每个舵机的限位配置 {channel: (min_angle, max_angle)}
        self.limits = {}
        # 存储每个舵机的当前角度
        self.current_angles = {}
        
        print("PCA9685舵机控制器初始化完成")
    
    def add_servo(self, channel, min_angle=0, max_angle=180, 
                  min_pulse=500, max_pulse=2500):
        """
        添加一个舵机到指定通道
        
        Args:
            channel: PCA9685通道号 (0-15)
            min_angle: 最小角度限位
            max_angle: 最大角度限位
            min_pulse: 最小脉冲宽度（微秒）
            max_pulse: 最大脉冲宽度（微秒）
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if channel < 0 or channel > 15:
            print(f"错误: 通道 {channel} 超出范围 (0-15)")
            return False
        
        if min_angle >= max_angle:
            print(f"错误: 最小角度必须小于最大角度")
            return False
        
        try:
            # 创建舵机对象
            servo_obj = servo.Servo(
                self.pca.channels[channel],
                min_pulse=min_pulse,
                max_pulse=max_pulse
            )
            
            self.servos[channel] = servo_obj
            self.limits[channel] = (min_angle, max_angle)
            self.current_angles[channel] = None
            
            print(f"舵机已添加到通道 {channel}, 限位: {min_angle}°-{max_angle}°")
            return True
        except Exception as e:
            print(f"添加舵机失败: {e}")
            return False
    
    def _check_interference(self, channel, angle, other_angles=None):
        """
        检查指定通道的角度是否会与其他舵机产生干涉
        
        根据测试数据推导的机械臂干涉模型：
        Servo 1 (ch 0) 和 Servo 2 (ch 1) 之间存在连杆干涉。
        
        推导公式：
        1. 下限干涉：S1 + S2 >= 145
        2. 上限干涉：S1 + 6*S2 <= 630
        """
        # 获取其他舵机的角度，优先从other_angles获取，否则从self.current_angles获取
        def get_val(ch):
            if other_angles and ch in other_angles:
                return other_angles[ch]
            return self.current_angles.get(ch)

        # 专门处理 Servo 1 (ch 0) 和 Servo 2 (ch 1) 的干涉
        if channel == 0 or channel == 1:
            s1 = angle if channel == 0 else get_val(0)
            s2 = angle if channel == 1 else get_val(1)
            
            if s1 is not None and s2 is not None:
                if s1 + s2 < 145:
                    print(f"干涉警告: Servo 1({s1}) + Servo 2({s2}) < 145 (下限干涉)")
                    return False
                if s1 + 6 * s2 > 630:
                    print(f"干涉警告: Servo 1({s1}) + 6*Servo 2({s2}) > 630 (上限干涉)")
                    return False
                
        return True

    def set_angle(self, channel, angle, smooth=False, step=5, delay=0.02):
        """
        设置指定舵机的角度
        
        Args:
            channel: 通道号
            angle: 目标角度
            smooth: 是否平滑移动
            step: 平滑移动的步进角度
            delay: 每步之间的延迟（秒）
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if channel not in self.servos:
            print(f"错误: 通道 {channel} 未配置舵机")
            return False
        
        # 检查角度限位
        min_angle, max_angle = self.limits[channel]
        if angle < min_angle or angle > max_angle:
            print(f"错误: 角度 {angle}° 超出限位范围 ({min_angle}°-{max_angle}°)")
            return False
        
        # 检查干涉
        if not self._check_interference(channel, angle):
            print(f"错误: 角度 {angle}° 在通道 {channel} 会产生干涉")
            return False
        
        try:
            if smooth and self.current_angles[channel] is not None:
                # 平滑移动
                current = self.current_angles[channel]
                direction = 1 if angle > current else -1
                
                while abs(current - angle) > step:
                    current += step * direction
                    self.servos[channel].angle = current
                    time.sleep(delay)
            
            # 设置最终角度
            self.servos[channel].angle = angle
            self.current_angles[channel] = angle
            print(f"通道 {channel} 设置为 {angle}°")
            return True
        except Exception as e:
            print(f"设置角度失败: {e}")
            return False
    
    def get_angle(self, channel):
        """
        获取指定舵机的当前角度
        
        Args:
            channel: 通道号
        
        Returns:
            float or None: 当前角度，如果未设置返回None
        """
        return self.current_angles.get(channel)
    
    def get_limits(self, channel):
        """
        获取指定舵机的角度限位
        
        Args:
            channel: 通道号
        
        Returns:
            tuple or None: (min_angle, max_angle)，如果未配置返回None
        """
        return self.limits.get(channel)
    
    def set_limits(self, channel, min_angle, max_angle):
        """
        设置指定舵机的角度限位
        
        Args:
            channel: 通道号
            min_angle: 最小角度
            max_angle: 最大角度
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if channel not in self.servos:
            print(f"错误: 通道 {channel} 未配置舵机")
            return False
        
        if min_angle >= max_angle:
            print(f"错误: 最小角度必须小于最大角度")
            return False
        
        self.limits[channel] = (min_angle, max_angle)
        print(f"通道 {channel} 限位已更新为: {min_angle}°-{max_angle}°")
        return True
    
    def set_multiple(self, angles_dict, smooth=False):
        """
        同时设置多个舵机的角度
        
        Args:
            angles_dict: 字典，格式为 {channel: angle}
            smooth: 是否平滑移动
        
        Returns:
            dict: 每个通道的执行结果 {channel: bool}
        """
        # 首先检查所有目标角度是否合法（包括干涉检查）
        for channel, angle in angles_dict.items():
            if channel not in self.servos:
                print(f"错误: 通道 {channel} 未配置舵机")
                return {ch: False for ch in angles_dict.keys()}
            
            min_angle, max_angle = self.limits[channel]
            if angle < min_angle or angle > max_angle:
                print(f"错误: 通道 {channel} 角度 {angle}° 超出限位")
                return {ch: False for ch in angles_dict.keys()}
            
            if not self._check_interference(channel, angle, other_angles=angles_dict):
                print(f"错误: 通道 {channel} 角度 {angle}° 会产生干涉")
                return {ch: False for ch in angles_dict.keys()}

        results = {}
        for channel, angle in angles_dict.items():
            results[channel] = self.set_angle(channel, angle, smooth=smooth)
        return results
    
    def center_all(self):
        """
        将所有舵机移动到中心位置（限位范围的中点）
        
        Returns:
            dict: 每个通道的执行结果
        """
        results = {}
        for channel in self.servos.keys():
            min_angle, max_angle = self.limits[channel]
            center = (min_angle + max_angle) / 2
            results[channel] = self.set_angle(channel, center)
        return results
    
    def disable(self, channel=None):
        """
        禁用舵机（停止PWM信号）
        
        Args:
            channel: 通道号，如果为None则禁用所有舵机
        """
        if channel is None:
            # 禁用所有舵机
            for ch in self.servos.keys():
                self.servos[ch].angle = None
            print("所有舵机已禁用")
        else:
            if channel in self.servos:
                self.servos[channel].angle = None
                print(f"通道 {channel} 已禁用")
    
    def get_servo_info(self):
        """
        获取所有舵机的信息
        
        Returns:
            dict: 舵机信息字典
        """
        info = {}
        for channel in self.servos.keys():
            info[channel] = {
                'current_angle': self.current_angles[channel],
                'limits': self.limits[channel],
                'min_angle': self.limits[channel][0],
                'max_angle': self.limits[channel][1]
            }
        return info
    
    def deinit(self):
        """释放资源"""
        try:
            self.pca.deinit()
            print("舵机控制器已释放资源")
        except Exception as e:
            print(f"释放资源时出错: {e}")
