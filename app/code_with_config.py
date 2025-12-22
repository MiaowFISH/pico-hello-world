"""
使用配置文件的主程序
从config.json读取配置
"""
import time
import json
from servo_controller import ServoController
from web_server import WebServer


def load_config(filename='config.json'):
    """加载配置文件"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None


def main():
    """主程序"""
    print("=" * 50)
    print("Pico2W PCA9685舵机控制系统 (配置文件版)")
    print("=" * 50)
    
    # 加载配置
    print("\n加载配置文件...")
    config = load_config()
    if not config:
        print("无法加载配置，程序退出")
        return
    
    print("配置加载成功！")
    
    try:
        # 1. 初始化舵机控制器
        print("\n[1/4] 初始化舵机控制器...")
        servo_ctrl = ServoController(frequency=config['pca9685']['frequency'])
        
        # 2. 配置舵机
        print("\n[2/4] 配置舵机...")
        for servo_cfg in config['servos']:
            channel = servo_cfg['channel']
            min_angle = servo_cfg['min_angle']
            max_angle = servo_cfg['max_angle']
            min_pulse = servo_cfg.get('min_pulse', 500)
            max_pulse = servo_cfg.get('max_pulse', 2500)
            
            servo_ctrl.add_servo(
                channel=channel,
                min_angle=min_angle,
                max_angle=max_angle,
                min_pulse=min_pulse,
                max_pulse=max_pulse
            )
            
            # 设置初始角度
            if 'initial_angle' in servo_cfg:
                initial_angle = servo_cfg['initial_angle']
                servo_ctrl.set_angle(channel, initial_angle)
                print(f"  通道{channel} 初始化到 {initial_angle}°")
        
        print("舵机配置完成！")
        
        # 3. 连接WiFi
        print("\n[3/4] 连接WiFi...")
        web_server = WebServer(servo_ctrl, port=config['server']['port'])
        
        wifi_ssid = config['wifi']['ssid']
        wifi_password = config['wifi']['password']
        
        if not web_server.connect_wifi(wifi_ssid, wifi_password):
            print("WiFi连接失败，请检查配置")
            return
        
        # 4. 启动Web服务器
        print("\n[4/4] 启动Web服务器...")
        if not web_server.start():
            print("服务器启动失败")
            return
        
        print("\n" + "=" * 50)
        print("✅ 系统启动成功！")
        print("=" * 50)
        print(f"\n📱 控制界面: http://{web_server.pool.getaddrinfo('0.0.0.0', 80)[0][4][0]}:{config['server']['port']}")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 主循环
        while True:
            web_server.handle_request()
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n收到停止信号...")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exception(e)
    finally:
        print("\n清理资源...")
        try:
            if 'web_server' in locals():
                web_server.stop()
            if 'servo_ctrl' in locals():
                servo_ctrl.disable()
                servo_ctrl.deinit()
        except:
            pass
        print("程序已退出")


if __name__ == "__main__":
    main()
