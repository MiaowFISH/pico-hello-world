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
    
    def __init__(self, servo_controller, port=80):
        """
        初始化Web服务器
        
        Args:
            servo_controller: ServoController实例
            port: 服务器端口号
        """
        self.servo_controller = servo_controller
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
            return self._html_response()
        elif path == '/api/info':
            return self._handle_info()
        elif path.startswith('/api/servo/'):
            return self._handle_servo(method, path, request)
        elif path == '/api/center':
            return self._handle_center()
        elif path == '/api/disable':
            return self._handle_disable(request)
        else:
            return self._error_response(404, "Not Found")
    
    def _handle_info(self):
        """获取所有舵机信息"""
        info = self.servo_controller.get_servo_info()
        return self._json_response({"success": True, "servos": info})
    
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
            angle = self.servo_controller.get_angle(channel)
            limits = self.servo_controller.get_limits(channel)
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
                success = self.servo_controller.set_angle(channel, angle, smooth)
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
                success = self.servo_controller.set_limits(
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
        results = self.servo_controller.center_all()
        return self._json_response({"success": True, "results": results})
    
    def _handle_disable(self, request):
        """禁用舵机"""
        body = self._get_request_body(request)
        if body:
            try:
                data = json.loads(body)
                channel = data.get('channel')
                self.servo_controller.disable(channel)
            except:
                pass
        else:
            self.servo_controller.disable()
        return self._json_response({"success": True})
    
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
    
    def _html_response(self):
        """生成HTML控制界面"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>舵机控制面板</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; }
        .servo { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .servo h3 { margin-top: 0; }
        input[type="range"] { width: 100%; }
        button { padding: 8px 15px; margin: 5px; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 4px; }
        button:hover { background: #45a049; }
        .info { font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 舵机控制面板</h1>
        <button onclick="loadServos()">刷新状态</button>
        <button onclick="centerAll()">全部居中</button>
        <button onclick="disableAll()">禁用所有</button>
        <div id="servos"></div>
    </div>
    <script>
        async function loadServos() {
            const res = await fetch('/api/info');
            const data = await res.json();
            const container = document.getElementById('servos');
            container.innerHTML = '';
            for (const [ch, info] of Object.entries(data.servos)) {
                const div = document.createElement('div');
                div.className = 'servo';
                div.innerHTML = `
                    <h3>通道 ${ch}</h3>
                    <div class="info">当前角度: <span id="angle-${ch}">${info.current_angle || 'N/A'}</span>°</div>
                    <div class="info">限位: ${info.min_angle}° - ${info.max_angle}°</div>
                    <input type="range" id="slider-${ch}" min="${info.min_angle}" max="${info.max_angle}" value="${info.current_angle || (info.min_angle + info.max_angle)/2}" oninput="updateAngle(${ch}, this.value)">
                    <button onclick="setAngle(${ch}, document.getElementById('slider-${ch}').value, false)">设置</button>
                    <button onclick="setAngle(${ch}, document.getElementById('slider-${ch}').value, true)">平滑移动</button>
                `;
                container.appendChild(div);
            }
        }
        function updateAngle(ch, val) {
            document.getElementById('angle-' + ch).textContent = val;
        }
        async function setAngle(ch, angle, smooth) {
            await fetch('/api/servo/' + ch, {
                method: 'POST',
                body: JSON.stringify({angle: parseFloat(angle), smooth: smooth})
            });
            setTimeout(loadServos, 500);
        }
        async function centerAll() {
            await fetch('/api/center');
            setTimeout(loadServos, 500);
        }
        async function disableAll() {
            await fetch('/api/disable', {method: 'POST'});
        }
        loadServos();
    </script>
</body>
</html>"""
        # 计算UTF-8编码后的字节长度
        html_bytes = html.encode('utf-8')
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html_bytes)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        # 返回完整响应（头部 + 正文）
        return response + html
