# Quickstart Guide: Pico2W 履带机械臂小车

## Prerequisites

### Hardware
- Raspberry Pi Pico 2W (已刷入 CircuitPython 10.x)
- PCA9685 PWM驱动板 + 3个舵机
- TB6612FNG 电机驱动板 + 2个直流电机（履带）
- DRV8837 电机驱动板 + 1个蜗轮蜗杆电机（底盘旋转）
- 5V/3A 以上电源

### Software
- Node.js 18+ (用于前端构建)
- Python 3.11+ (用于部署脚本)
- circup (CircuitPython库管理器): `pip install circup`

---

## 1. Hardware Setup (接线)

按照以下接线表连接：

| Pico 引脚 | 连接目标 | 功能 |
|-----------|---------|------|
| GP0 | PCA9685 - SDA | I2C数据线 |
| GP1 | PCA9685 - SCL | I2C时钟线 |
| GP6 | TB6612 - PWMA | 左履带速度 |
| GP7 | TB6612 - AIN1 | 左履带方向1 |
| GP8 | TB6612 - AIN2 | 左履带方向2 |
| GP9 | TB6612 - PWMB | 右履带速度 |
| GP10 | TB6612 - BIN1 | 右履带方向1 |
| GP11 | TB6612 - BIN2 | 右履带方向2 |
| GP12 | TB6612 - STBY | 履带驱动器使能 |
| GP13 | DRV8837 - SLEEP | 底盘旋转休眠控制 |
| GP14 | DRV8837 - IN1 | 底盘旋转控制1 |
| GP15 | DRV8837 - IN2 | 底盘旋转控制2 |

**舵机连接到PCA9685**:
- Channel 0: 机械臂关节1
- Channel 1: 机械臂关节2  
- Channel 2: 机械臂夹爪

---

## 2. Install CircuitPython Libraries

```bash
# 连接Pico到电脑USB
circup install adafruit_httpserver adafruit_pca9685 adafruit_motor
```

验证 `lib/` 目录包含：
- `adafruit_httpserver/`
- `adafruit_pca9685.mpy`
- `adafruit_motor/`
- `adafruit_register/` (依赖)

---

## 3. Configure WiFi

编辑 `app/config.json`：

```json
{
  "wifi": {
    "ssid": "你的WiFi名称",
    "password": "你的WiFi密码"
  }
}
```

---

## 4. Build Frontend

```bash
cd frontend
npm install
npm run build
```

构建产物在 `frontend/dist/`，将被部署到Pico。

---

## 5. Deploy to Pico

```bash
# Windows
tools\deploy.bat

# Linux/macOS
./tools/deploy.sh
```

或手动复制：
1. 复制 `app/*` 到 Pico 根目录
2. 复制 `lib/*` 到 Pico `lib/` 目录
3. 复制 `frontend/dist/*` 到 Pico `static/` 目录

---

## 6. Run

1. 断开USB，使用外部电源供电
2. 等待~10秒，Pico连接WiFi
3. 在路由器管理页查找Pico的IP地址
4. 浏览器访问: `http://<Pico-IP>/`

---

## Quick Test

### 串口调试

Windows:
```powershell
# 查找COM端口
Get-WmiObject Win32_SerialPort | Select-Object DeviceID, Description

# 使用PuTTY或其他终端连接 COM端口，波特率 115200
```

macOS/Linux:
```bash
screen /dev/tty.usbmodem* 115200
```

### API测试

```bash
# 获取状态
curl http://<Pico-IP>/api/status

# 获取配置
curl http://<Pico-IP>/api/config
```

### WebSocket测试 (浏览器控制台)

```javascript
const ws = new WebSocket('ws://<Pico-IP>/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({ action: 'track', command: 'forward', speed: 'slow' }));
};
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## Troubleshooting

| 问题 | 解决方案 |
|------|----------|
| WiFi连接失败 | 检查SSID/密码，确保2.4GHz网络 |
| 舵机不动 | 检查I2C接线，验证PCA9685地址(默认0x40) |
| 履带不动 | 检查STBY引脚是否拉高，电源是否充足 |
| 网页打不开 | 确认IP地址正确，防火墙允许80端口 |
| 控制延迟高 | 使用WebSocket而非HTTP，检查WiFi信号 |

---

## Development Workflow

```bash
# 前端开发 (热重载)
cd frontend
npm run dev
# 修改 vite.config.js 中的 proxy 指向 Pico IP

# 后端修改后重新部署
tools/deploy.bat
# Pico 自动重启
```
