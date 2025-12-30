"""
网络服务器模块
提供HTTP API接口控制舵机
"""
import wifi
import socketpool
import json
import time


class WebServer:
    """Web服务器类，提供HTTP API接口"""
    
    def __init__(self, vehicle_controller, port=80):
        """
        初始化Web服务器
        
        Args:
            vehicle_controller: VehicleController实例
            port: 服务器端口号
        """
        self.vehicle = vehicle_controller
        self.port = port
        self.pool = None
        self.server_socket = None
        self.running = False
        
    def connect_wifi(self, ssid, password, timeout=30, retries=3):
        """
        连接到WiFi网络
        
        Args:
            ssid: WiFi名称
            password: WiFi密码
            timeout: 超时时间（秒）
            retries: 重试次数
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        print(f"正在连接到WiFi: {ssid}")
        
        # 检查是否已连接
        if wifi.radio.connected:
            print("WiFi已连接，断开现有连接...")
            try:
                wifi.radio.stop_station()
                time.sleep(1)
            except:
                pass
        
        # 尝试连接
        for attempt in range(retries):
            try:
                if attempt > 0:
                    print(f"重试连接 ({attempt + 1}/{retries})...")
                
                # 连接WiFi
                wifi.radio.connect(ssid, password, timeout=timeout)
                
                # 等待连接建立
                print("等待连接建立...")
                for i in range(10):
                    if wifi.radio.connected:
                        break
                    time.sleep(1)
                    print(f"  等待中... {i+1}/10")
                
                # 检查连接状态
                if not wifi.radio.connected:
                    print(f"连接超时，WiFi未连接")
                    continue
                
                # 等待获取IP地址
                print("等待获取IP地址...")
                for i in range(10):
                    ip_address = wifi.radio.ipv4_address
                    if ip_address and str(ip_address) != "0.0.0.0":
                        break
                    time.sleep(1)
                    print(f"  等待IP... {i+1}/10")
                
                # 获取IP地址
                ip_address = wifi.radio.ipv4_address
                if not ip_address or str(ip_address) == "0.0.0.0":
                    print("未能获取IP地址")
                    continue
                
                # 创建socket池
                self.pool = socketpool.SocketPool(wifi.radio)
                
                # 显示连接信息
                print(f"WiFi连接成功!")
                print(f"IP地址: {ip_address}")
                try:
                    print(f"MAC地址: {wifi.radio.mac_address}")
                except:
                    pass
                try:
                    if hasattr(wifi.radio, 'ap_info') and wifi.radio.ap_info:
                        print(f"信号强度: {wifi.radio.ap_info.rssi} dBm")
                except:
                    pass
                
                return True
                
            except ConnectionError as e:
                print(f"连接错误 (尝试 {attempt + 1}/{retries}): {e}")
                time.sleep(2)
            except OSError as e:
                print(f"系统错误 (尝试 {attempt + 1}/{retries}): {e}")
                time.sleep(2)
            except Exception as e:
                print(f"未知错误 (尝试 {attempt + 1}/{retries}): {e}")
                import traceback
                traceback.print_exception(e)
                time.sleep(2)
        
        print(f"WiFi连接失败，已尝试 {retries} 次")
        return False
    
    def start(self):
        """启动HTTP服务器"""
        if self.pool is None:
            print("错误: 请先连接WiFi")
            return False
        
        try:
            # 创建socket
            self.server_socket = self.pool.socket(
                self.pool.AF_INET, 
                self.pool.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                self.pool.SOL_SOCKET, 
                self.pool.SO_REUSEADDR, 
                1
            )
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)  # 1秒超时，允许定期检查
            
            self.running = True
            print(f"HTTP服务器启动成功，监听端口: {self.port}")
            print(f"访问地址: http://{wifi.radio.ipv4_address}:{self.port}")
            return True
        except Exception as e:
            print(f"服务器启动失败: {e}")
            return False
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("服务器已停止")
    
    def handle_request(self):
        """
        处理一个HTTP请求
        
        Returns:
            bool: 如果处理了请求返回True，超时返回False
        """
        if not self.running:
            return False
        
        client_socket = None
        try:
            # 接受连接（带超时）
            client_socket, client_addr = self.server_socket.accept()
            client_socket.settimeout(5.0)
            
            # 读取请求 - CircuitPython使用recv_into
            request_bytes = b""
            try:
                buffer = bytearray(1024)
                while True:
                    try:
                        # CircuitPython的recv_into需要buffer和bufsize两个参数
                        nbytes = client_socket.recv_into(buffer, 1024)
                        if not nbytes or nbytes == 0:
                            break
                        
                        request_bytes += bytes(buffer[:nbytes])
                        
                        # 检测到请求头结束
                        if b"\r\n\r\n" in request_bytes:
                            break
                        
                        # 限制大小防止内存溢出
                        if len(request_bytes) > 8192:
                            break
                            
                    except OSError as e:
                        # 超时或连接关闭
                        if e.errno in (116, 11):  # ETIMEDOUT or EAGAIN
                            break
                        raise
                
                request_text = request_bytes.decode('utf-8', 'ignore')
                
            except OSError:
                request_text = ""  # 超时或连接关闭
            except Exception as e:
                print(f"读取请求时出错: {e}")
                request_text = ""
            
            if request_text.strip():
                # 解析并处理请求
                response = self._process_request(request_text)
                try:
                    # 发送响应 - CircuitPython使用send，分块发送大数据
                    response_bytes = response.encode('utf-8')
                    total_sent = 0
                    chunk_size = 1024
                    
                    while total_sent < len(response_bytes):
                        chunk = response_bytes[total_sent:total_sent + chunk_size]
                        sent = client_socket.send(chunk)
                        if sent == 0:
                            break
                        total_sent += sent
                        
                except Exception as e:
                    print(f"发送响应失败: {e}")
            
            return True
            
        except OSError as e:
            # 超时是正常的，允许主循环继续运行
            if hasattr(e, 'errno') and e.errno == 116:  # ETIMEDOUT
                return False
            # 其他错误也忽略，继续运行
            return False
        except Exception as e:
            print(f"处理请求时出错: {e}")
            return False
        finally:
            # 确保关闭socket
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
    
    def _process_request(self, request):
        """
        处理HTTP请求
        
        Args:
            request: HTTP请求字符串
        
        Returns:
            str: HTTP响应
        """
        lines = request.split('\r\n')
        if not lines:
            return self._error_response(400, "Bad Request")
        
        # 解析请求行
        parts = lines[0].split(' ')
        if len(parts) < 2:
            return self._error_response(400, "Bad Request")
        
        method = parts[0]
        path = parts[1]
        
        print(f"收到请求: {method} {path}")
        
        # 路由处理
        if path == '/' or path == '/index.html':
            return self._static_response()
        elif path == '/api/status':
            return self._handle_status()
        elif path == '/api/info':
            return self._handle_info()
        elif path.startswith('/api/servo/'):
            return self._handle_servo(method, path, request)
        elif path == '/api/center':
            return self._handle_center()
        elif path == '/api/disable':
            return self._handle_disable(request)
        elif path.startswith('/api/tracks'):
            return self._handle_tracks(method, request)
        elif path.startswith('/api/base'):
            return self._handle_base(method, request)
        elif path == '/api/emergency_stop':
            return self._handle_emergency_stop()
        else:
            return self._error_response(404, "Not Found")
    
    def _handle_info(self):
        """获取所有舵机信息"""
        info = self.vehicle.get_servo_info()
        return self._json_response({"success": True, "servos": info})
    
    def _handle_status(self):
        """获取所有状态信息"""
        status = self.vehicle.get_all_status()
        return self._json_response({"success": True, "status": status})
    
    def _handle_servo(self, method, path, request):
        """处理舵机控制请求"""
        # 解析路径: /api/servo/{channel}
        parts = path.split('/')
        if len(parts) < 4:
            return self._error_response(400, "Invalid path")
        
        try:
            channel = int(parts[3])
        except ValueError:
            return self._error_response(400, "Invalid channel")
        
        if method == 'GET':
            # 获取舵机状态
            angle = self.vehicle.get_servo_angle(channel)
            limits = self.vehicle.servo_ctrl.get_limits(channel)
            if limits is None:
                return self._json_response({
                    "success": False, 
                    "error": "Servo not configured"
                })
            return self._json_response({
                "success": True,
                "channel": channel,
                "angle": angle,
                "limits": {"min": limits[0], "max": limits[1]}
            })
        
        elif method == 'POST':
            # 设置舵机角度
            # 解析JSON body
            body = self._get_request_body(request)
            if not body:
                return self._error_response(400, "Missing request body")
            
            try:
                data = json.loads(body)
            except:
                return self._error_response(400, "Invalid JSON")
            
            if 'angle' in data:
                # 设置角度
                angle = data['angle']
                smooth = data.get('smooth', False)
                success = self.vehicle.set_servo_angle(channel, angle, smooth)
                return self._json_response({
                    "success": success,
                    "channel": channel,
                    "angle": angle if success else None
                })
            
            elif 'limits' in data:
                # 设置限位
                limits = data['limits']
                min_angle = limits.get('min')
                max_angle = limits.get('max')
                if min_angle is None or max_angle is None:
                    return self._error_response(400, "Invalid limits")
                success = self.vehicle.servo_ctrl.set_limits(
                    channel, min_angle, max_angle
                )
                return self._json_response({
                    "success": success,
                    "channel": channel,
                    "limits": {"min": min_angle, "max": max_angle}
                })
            
            else:
                return self._error_response(400, "Missing angle or limits")
        
        else:
            return self._error_response(405, "Method Not Allowed")
    
    def _handle_center(self):
        """将所有舵机移到中心位置"""
        results = self.vehicle.center_all_servos()
        return self._json_response({"success": True, "results": results})
    
    def _handle_disable(self, request):
        """禁用舵机"""
        body = self._get_request_body(request)
        if body:
            try:
                data = json.loads(body)
                channel = data.get('channel')
                self.vehicle.disable_servos(channel)
            except:
                pass
        else:
            self.vehicle.disable_servos()
        return self._json_response({"success": True})
    
    def _handle_tracks(self, method, request):
        """处理履带控制请求"""
        if method != 'POST':
            return self._error_response(405, "Method Not Allowed")
        
        body = self._get_request_body(request)
        if not body:
            return self._error_response(400, "Missing request body")
        
        try:
            data = json.loads(body)
        except:
            return self._error_response(400, "Invalid JSON")
        
        action = data.get('action')
        speed = data.get('speed', 50)
        
        if action == 'forward':
            self.vehicle.move_forward(speed)
        elif action == 'backward':
            self.vehicle.move_backward(speed)
        elif action == 'left':
            self.vehicle.turn_left(speed)
        elif action == 'right':
            self.vehicle.turn_right(speed)
        elif action == 'stop':
            self.vehicle.stop_tracks()
        elif action == 'set':
            left = data.get('left_speed', 0)
            right = data.get('right_speed', 0)
            self.vehicle.set_track_speeds(left, right)
        else:
            return self._error_response(400, "Invalid action")
        
        status = self.vehicle.get_track_status()
        return self._json_response({"success": True, "status": status})
    
    def _handle_base(self, method, request):
        """处理底盘旋转控制请求"""
        if method != 'POST':
            return self._error_response(405, "Method Not Allowed")
        
        body = self._get_request_body(request)
        if not body:
            return self._error_response(400, "Missing request body")
        
        try:
            data = json.loads(body)
        except:
            return self._error_response(400, "Invalid JSON")
        
        action = data.get('action')
        speed = data.get('speed', 50)
        
        if action == 'cw':
            self.vehicle.rotate_base_cw(speed)
        elif action == 'ccw':
            self.vehicle.rotate_base_ccw(speed)
        elif action == 'stop':
            self.vehicle.stop_base()
        elif action == 'set':
            rotation_speed = data.get('rotation_speed', 0)
            self.vehicle.set_base_rotation(rotation_speed)
        else:
            return self._error_response(400, "Invalid action")
        
        status = self.vehicle.get_base_status()
        return self._json_response({"success": True, "status": status})
    
    def _handle_emergency_stop(self):
        """紧急停止所有运动"""
        self.vehicle.emergency_stop()
        return self._json_response({"success": True, "message": "Emergency stop executed"})
    
    def _get_request_body(self, request):
        """从请求中提取body"""
        parts = request.split('\r\n\r\n', 1)
        if len(parts) == 2:
            return parts[1]
        return None
    
    def _json_response(self, data):
        """生成JSON响应"""
        body = json.dumps(data)
        body_bytes = body.encode('utf-8')
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        return response + body
    
    def _error_response(self, code, message):
        """生成错误响应"""
        body = json.dumps({"success": False, "error": message})
        body_bytes = body.encode('utf-8')
        response = (
            f"HTTP/1.1 {code} {message}\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        return response + body
    
    def _static_response(self):
        """返回简单的API说明页面"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        h1 { color: #333; }
        code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
        pre { background: #f0f0f0; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 履带机械臂小车 API</h1>
        <p>欢迎使用履带机械臂小车控制系统！</p>
        <h2>可用的API接口：</h2>
        <ul>
            <li><code>GET /api/status</code> - 获取所有状态</li>
            <li><code>GET /api/info</code> - 获取舵机信息</li>
            <li><code>POST /api/tracks</code> - 控制履带</li>
            <li><code>POST /api/base</code> - 控制底盘旋转</li>
            <li><code>POST /api/servo/{channel}</code> - 控制舵机</li>
            <li><code>POST /api/emergency_stop</code> - 紧急停止</li>
        </ul>
        <p>请使用独立的前端应用来控制小车。</p>
    </div>
</body>
</html>"""
        html_bytes = html.encode('utf-8')
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html_bytes)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        return response + html
