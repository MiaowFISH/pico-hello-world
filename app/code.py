"""
Pico2W舵机控制主程序
使用PCA9685驱动板通过WiFi控制舵机
"""
import time
import board
from servo_controller import ServoController
from web_server import WebServer

# ===================== 配置区域 =====================
# WiFi配置
WIFI_SSID = "mi-router-ax3000t-2g-0fdbd"      # 修改为你的WiFi名称
WIFI_PASSWORD = "12345678"  # 修改为你的WiFi密码

# 舵机配置
# 格式: (通道号, 最小角度, 最大角度, 最小脉冲宽度, 最大脉冲宽度)
SERVO_CONFIG = [
    (0, 0, 180, 500, 2500),    # 通道0：0-180度
    (1, 45, 135, 500, 2500),   # 通道1：45-135度（有限位）
    (2, 0, 90, 500, 2500),     # 通道2：0-90度
    # 添加更多舵机配置...
]

# 服务器端口
SERVER_PORT = 80
# ===================================================


def setup_servos(controller):
    """配置所有舵机"""
    print("\n正在配置舵机...")
    for config in SERVO_CONFIG:
        channel = config[0]
        min_angle = config[1]
        max_angle = config[2]
        min_pulse = config[3] if len(config) > 3 else 500
        max_pulse = config[4] if len(config) > 4 else 2500
        
        controller.add_servo(
            channel=channel,
            min_angle=min_angle,
            max_angle=max_angle,
            min_pulse=min_pulse,
            max_pulse=max_pulse
        )
    
    print("舵机配置完成！")
    return True


def demo_servos(controller):
    """舵机演示程序"""
    print("\n运行舵机演示...")
    print("将所有舵机移动到中心位置...")
    controller.center_all()
    time.sleep(2)
    
    print("演示单个舵机控制...")
    for channel in controller.servos.keys():
        min_angle, max_angle = controller.limits[channel]
        print(f"  通道{channel}: {min_angle}° -> {max_angle}°")
        controller.set_angle(channel, min_angle)
        time.sleep(0.5)
        controller.set_angle(channel, max_angle)
        time.sleep(0.5)
        controller.set_angle(channel, (min_angle + max_angle) / 2)
        time.sleep(0.5)
    
    print("演示完成！")


def main():
    """主程序"""
    print("=" * 50)
    print("Pico2W PCA9685舵机控制系统")
    print("=" * 50)
    
    try:
        # 1. 初始化舵机控制器
        print("\n[1/4] 初始化舵机控制器...")
        servo_ctrl = ServoController()
        
        # 2. 配置舵机
        print("\n[2/4] 配置舵机...")
        setup_servos(servo_ctrl)
        
        # 3. 运行演示（可选）
        # demo_servos(servo_ctrl)
        
        # 4. 启动Web服务器
        print("\n[3/4] 连接WiFi...")
        web_server = WebServer(servo_ctrl, port=SERVER_PORT)
        
        if not web_server.connect_wifi(WIFI_SSID, WIFI_PASSWORD):
            print("WiFi连接失败，请检查配置")
            return
        
        print("\n[4/4] 启动Web服务器...")
        if not web_server.start():
            print("服务器启动失败")
            return
        
        print("\n" + "=" * 50)
        print("✅ 系统启动成功！")
        print("=" * 50)
        print(f"\n📱 控制界面: http://{web_server.pool.getaddrinfo('0.0.0.0', 80)[0][4][0]}:{SERVER_PORT}")
        print("\n可用的API接口:")
        print("  GET  /api/info              - 获取所有舵机信息")
        print("  GET  /api/servo/{channel}   - 获取指定舵机状态")
        print("  POST /api/servo/{channel}   - 控制指定舵机")
        print("       Body: {\"angle\": 90, \"smooth\": false}")
        print("  POST /api/center            - 所有舵机归中")
        print("  POST /api/disable           - 禁用所有舵机")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 主循环
        while True:
            web_server.handle_request()
            time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
    
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
