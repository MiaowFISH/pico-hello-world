"""
WiFi连接测试工具
用于诊断WiFi连接问题
"""
import wifi
import time
import socketpool

# WiFi配置
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"

def test_wifi_connection():
    """测试WiFi连接"""
    print("=" * 60)
    print("WiFi连接诊断工具")
    print("=" * 60)
    
    # 1. 检查WiFi模块
    print("\n[1] 检查WiFi模块...")
    try:
        print(f"  MAC地址: {wifi.radio.mac_address}")
        print(f"  当前状态: {'已连接' if wifi.radio.connected else '未连接'}")
        print("  ✓ WiFi模块正常")
    except Exception as e:
        print(f"  ✗ WiFi模块错误: {e}")
        return False
    
    # 2. 断开现有连接
    print("\n[2] 断开现有连接...")
    if wifi.radio.connected:
        try:
            wifi.radio.stop_station()
            time.sleep(2)
            print("  ✓ 已断开现有连接")
        except Exception as e:
            print(f"  ⚠ 断开连接失败: {e}")
    else:
        print("  ○ 没有现有连接")
    
    # 3. 扫描网络
    print("\n[3] 扫描WiFi网络...")
    try:
        networks = wifi.radio.start_scanning_networks()
        time.sleep(2)
        networks_list = list(networks)
        wifi.radio.stop_scanning_networks()
        
        print(f"  发现 {len(networks_list)} 个网络:")
        found_target = False
        for net in networks_list[:10]:  # 只显示前10个
            is_target = net.ssid == WIFI_SSID
            marker = "  >>> " if is_target else "      "
            print(f"{marker}{net.ssid:32s} {net.rssi:4d} dBm  Ch:{net.channel}")
            if is_target:
                found_target = True
                print(f"      ✓ 找到目标网络! 信号强度: {net.rssi} dBm")
        
        if not found_target:
            print(f"  ⚠ 警告: 未找到目标网络 '{WIFI_SSID}'")
            print(f"  请检查:")
            print(f"    - SSID是否正确（区分大小写）")
            print(f"    - 路由器是否开启2.4GHz频段")
            print(f"    - WiFi信号是否足够强")
    except Exception as e:
        print(f"  ⚠ 扫描网络失败: {e}")
    
    # 4. 尝试连接
    print(f"\n[4] 连接到 '{WIFI_SSID}'...")
    for attempt in range(3):
        try:
            if attempt > 0:
                print(f"  重试 {attempt + 1}/3...")
            
            print("  发起连接...")
            wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD, timeout=30)
            
            # 等待连接
            print("  等待连接建立...")
            for i in range(15):
                if wifi.radio.connected:
                    print(f"  ✓ 连接建立 ({i+1}秒)")
                    break
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    print(f"    等待中... {i+1}/15秒")
            
            if not wifi.radio.connected:
                print("  ✗ 连接超时")
                continue
            
            # 等待IP地址
            print("  等待DHCP分配IP...")
            for i in range(15):
                ip = wifi.radio.ipv4_address
                if ip and str(ip) != "0.0.0.0":
                    print(f"  ✓ 获得IP地址: {ip} ({i+1}秒)")
                    break
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    print(f"    等待IP... {i+1}/15秒")
            
            # 检查IP
            ip = wifi.radio.ipv4_address
            if not ip or str(ip) == "0.0.0.0":
                print("  ✗ 未获得有效IP地址")
                continue
            
            # 连接成功
            print("\n" + "=" * 60)
            print("✓ WiFi连接成功!")
            print("=" * 60)
            print(f"SSID:       {WIFI_SSID}")
            print(f"IP地址:     {wifi.radio.ipv4_address}")
            
            try:
                print(f"MAC地址:    {wifi.radio.mac_address}")
            except:
                pass
            
            try:
                if hasattr(wifi.radio, 'ap_info') and wifi.radio.ap_info:
                    ap_info = wifi.radio.ap_info
                    if hasattr(ap_info, 'rssi'):
                        print(f"信号强度:   {ap_info.rssi} dBm")
                    if hasattr(ap_info, 'channel'):
                        print(f"频道:       {ap_info.channel}")
            except Exception as e:
                print(f"  (无法获取AP信息: {e})")
            
            # 测试socket
            print("\n[5] 测试Socket...")
            try:
                pool = socketpool.SocketPool(wifi.radio)
                print("  ✓ SocketPool创建成功")
                
                # 尝试创建一个socket
                test_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
                test_socket.close()
                print("  ✓ Socket创建和关闭成功")
            except Exception as e:
                print(f"  ⚠ Socket测试失败: {e}")
            
            print("\n" + "=" * 60)
            print("诊断完成 - 一切正常!")
            print("=" * 60)
            return True
            
        except ConnectionError as e:
            print(f"  ✗ 连接错误: {e}")
            time.sleep(2)
        except OSError as e:
            print(f"  ✗ 系统错误: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"  ✗ 未知错误: {e}")
            import traceback
            traceback.print_exception(e)
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("✗ WiFi连接失败")
    print("=" * 60)
    print("\n可能的问题:")
    print("  1. SSID或密码错误")
    print("  2. WiFi是5GHz网络（Pico只支持2.4GHz）")
    print("  3. 信号太弱")
    print("  4. 路由器限制了连接")
    print("  5. DHCP服务器问题")
    print("\n建议:")
    print("  - 检查路由器设置")
    print("  - 确认WiFi密码")
    print("  - 靠近路由器测试")
    print("  - 重启路由器")
    return False

if __name__ == "__main__":
    test_wifi_connection()
