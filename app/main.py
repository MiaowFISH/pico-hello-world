"""
履带机械臂小车主程序
从config.json读取配置
"""
import time
import json
from vehicle_controller import VehicleController
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
    print("🤖 履带机械臂小车控制系统")
    print("=" * 50)
    
    # 加载配置
    print("\n加载配置文件...")
    config = load_config()
    if not config:
        print("无法加载配置，程序退出")
        return
    
    print("配置加载成功！")
    
    try:
        # 1. 初始化车辆控制器
        print("\n[1/3] 初始化车辆控制器...")
        vehicle = VehicleController(config)
        
        # 2. 连接WiFi
        print("\n[2/3] 连接WiFi...")
        web_server = WebServer(vehicle, port=config['server']['port'])
        
        wifi_ssid = config['wifi']['ssid']
        wifi_password = config['wifi']['password']
        
        if not web_server.connect_wifi(wifi_ssid, wifi_password):
            print("WiFi连接失败，请检查配置")
            return
        
        # 3. 启动Web服务器
        print("\n[3/3] 启动Web服务器...")
        if not web_server.start():
            print("服务器启动失败")
            return
        
        print("\n" + "=" * 50)
        print("✅ 系统启动成功！")
        print("=" * 50)
        print(f"\n📱 API地址: http://{web_server.pool.getaddrinfo('0.0.0.0', 80)[0][4][0]}:{config['server']['port']}")
        print("\n💡 提示: 请使用独立的前端应用进行控制")
        print("   前端项目位置: frontend/")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 主循环
        while True:
            web_server.handle_request()
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n收到停止信号...")
        vehicle.emergency_stop()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exception(e)
    finally:
        print("清理资源...")
        try:
            vehicle.deinit()
        except:
            pass


if __name__ == '__main__':
    main()
