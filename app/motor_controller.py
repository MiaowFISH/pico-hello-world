"""
电机控制器模块
支持TB6612双路电机驱动器和DRV8837单路电机驱动器
"""
import board
import pwmio
import digitalio
import time


class TB6612Controller:
    """TB6612双路电机驱动器控制类（用于履带）"""
    
    def __init__(self, pwma_pin, ain1_pin, ain2_pin, 
                 pwmb_pin, bin1_pin, bin2_pin, stby_pin):
        """
        初始化TB6612控制器
        
        Args:
            pwma_pin: A路PWM引脚（控制左履带速度）
            ain1_pin: A路方向引脚1
            ain2_pin: A路方向引脚2
            pwmb_pin: B路PWM引脚（控制右履带速度）
            bin1_pin: B路方向引脚1
            bin2_pin: B路方向引脚2
            stby_pin: 待机引脚（高电平工作，低电平待机）
        """
        # A路（左履带）PWM
        self.pwma = pwmio.PWMOut(pwma_pin, frequency=1000, duty_cycle=0)
        self.ain1 = digitalio.DigitalInOut(ain1_pin)
        self.ain1.direction = digitalio.Direction.OUTPUT
        self.ain2 = digitalio.DigitalInOut(ain2_pin)
        self.ain2.direction = digitalio.Direction.OUTPUT
        
        # B路（右履带）PWM
        self.pwmb = pwmio.PWMOut(pwmb_pin, frequency=1000, duty_cycle=0)
        self.bin1 = digitalio.DigitalInOut(bin1_pin)
        self.bin1.direction = digitalio.Direction.OUTPUT
        self.bin2 = digitalio.DigitalInOut(bin2_pin)
        self.bin2.direction = digitalio.Direction.OUTPUT
        
        # 待机控制
        self.stby = digitalio.DigitalInOut(stby_pin)
        self.stby.direction = digitalio.Direction.OUTPUT
        
        # 当前速度状态 (-100 到 100)
        self.left_speed = 0
        self.right_speed = 0
        
        # 初始化时不启用，需要时手动调用enable()
        self.stby.value = False  # 待机状态
        
        print("TB6612电机控制器初始化完成")
    
    def enable(self):
        """启用驱动器"""
        self.stby.value = True
    
    def standby(self):
        """进入待机模式"""
        self.stby.value = False
        self.left_speed = 0
        self.right_speed = 0
    
    def _set_motor_a(self, speed):
        """
        设置A路电机（左履带）速度
        
        Args:
            speed: -100到100的速度值，负数为反转
        """
        speed = max(-100, min(100, speed))
        self.left_speed = speed
        
        if speed == 0:
            self.ain1.value = False
            self.ain2.value = False
            self.pwma.duty_cycle = 0
        elif speed > 0:
            self.ain1.value = True
            self.ain2.value = False
            self.pwma.duty_cycle = int(abs(speed) * 655.35)  # 0-65535
        else:
            self.ain1.value = False
            self.ain2.value = True
            self.pwma.duty_cycle = int(abs(speed) * 655.35)
    
    def _set_motor_b(self, speed):
        """
        设置B路电机（右履带）速度
        
        Args:
            speed: -100到100的速度值，负数为反转
        """
        speed = max(-100, min(100, speed))
        self.right_speed = speed
        
        if speed == 0:
            self.bin1.value = False
            self.bin2.value = False
            self.pwmb.duty_cycle = 0
        elif speed > 0:
            self.bin1.value = True
            self.bin2.value = False
            self.pwmb.duty_cycle = int(abs(speed) * 655.35)
        else:
            self.bin1.value = False
            self.bin2.value = True
            self.pwmb.duty_cycle = int(abs(speed) * 655.35)
    
    def set_motors(self, left_speed, right_speed):
        """
        设置两个电机速度
        
        Args:
            left_speed: 左履带速度 (-100到100)
            right_speed: 右履带速度 (-100到100)
        """
        self.enable()
        self._set_motor_a(left_speed)
        self._set_motor_b(right_speed)
    
    def forward(self, speed=50):
        """前进"""
        self.set_motors(speed, speed)
    
    def backward(self, speed=50):
        """后退"""
        self.set_motors(-speed, -speed)
    
    def turn_left(self, speed=50):
        """左转（左履带后退，右履带前进）"""
        self.set_motors(-speed, speed)
    
    def turn_right(self, speed=50):
        """右转（左履带前进，右履带后退）"""
        self.set_motors(speed, -speed)
    
    def stop(self):
        """停止"""
        self.set_motors(0, 0)
    
    def get_status(self):
        """获取当前状态"""
        return {
            "left_speed": self.left_speed,
            "right_speed": self.right_speed,
            "enabled": self.stby.value
        }
    
    def deinit(self):
        """清理资源"""
        self.standby()
        self.pwma.deinit()
        self.pwmb.deinit()


class DRV8837Controller:
    """DRV8837单路电机驱动器控制类（用于底盘旋转）"""
    
    def __init__(self, in1_pin, in2_pin, sleep_pin=None):
        """
        初始化DRV8837控制器
        
        Args:
            in1_pin: 输入引脚1（PWM）
            in2_pin: 输入引脚2（PWM）
            sleep_pin: 休眠引脚（可选，高电平工作，低电平休眠）
        """
        # IN1和IN2都使用PWM
        self.in1 = pwmio.PWMOut(in1_pin, frequency=1000, duty_cycle=0)
        self.in2 = pwmio.PWMOut(in2_pin, frequency=1000, duty_cycle=0)
        
        # 休眠控制（可选）
        self.sleep = None
        if sleep_pin:
            self.sleep = digitalio.DigitalInOut(sleep_pin)
            self.sleep.direction = digitalio.Direction.OUTPUT
            self.sleep.value = False  # 默认休眠
        
        self.current_speed = 0
        
        # 初始化时不启用，需要时手动调用enable()
        if self.sleep:
            self.sleep.value = False  # 休眠状态
        
        print("DRV8837电机控制器初始化完成")
    
    def enable(self):
        """启用驱动器"""
        if self.sleep:
            self.sleep.value = True
    
    def disable(self):
        """禁用驱动器（进入休眠）"""
        if self.sleep:
            self.sleep.value = False
        self.current_speed = 0
        self.in1.duty_cycle = 0
        self.in2.duty_cycle = 0
    
    def set_speed(self, speed):
        """
        设置电机速度
        
        Args:
            speed: -100到100的速度值，负数为反转
        """
        speed = max(-100, min(100, speed))
        self.current_speed = speed
        
        self.enable()
        
        if speed == 0:
            # 刹车（两个引脚都为高）
            self.in1.duty_cycle = 65535
            self.in2.duty_cycle = 65535
        elif speed > 0:
            # 正转：IN1=PWM, IN2=0
            self.in1.duty_cycle = int(abs(speed) * 655.35)
            self.in2.duty_cycle = 0
        else:
            # 反转：IN1=0, IN2=PWM
            self.in1.duty_cycle = 0
            self.in2.duty_cycle = int(abs(speed) * 655.35)
    
    def rotate_cw(self, speed=50):
        """顺时针旋转"""
        self.set_speed(speed)
    
    def rotate_ccw(self, speed=50):
        """逆时针旋转"""
        self.set_speed(-speed)
    
    def stop(self):
        """停止"""
        self.set_speed(0)
    
    def coast(self):
        """滑行停止（两个引脚都为低）"""
        self.in1.duty_cycle = 0
        self.in2.duty_cycle = 0
        self.current_speed = 0
    
    def get_status(self):
        """获取当前状态"""
        return {
            "speed": self.current_speed,
            "enabled": self.sleep.value if self.sleep else True
        }
    
    def deinit(self):
        """清理资源"""
        self.disable()
        self.in1.deinit()
        self.in2.deinit()
