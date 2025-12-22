# Pico2W PCA9685 舵机控制系统

使用Raspberry Pi Pico2W和PCA9685驱动板通过WiFi控制舵机的CircuitPython项目。

## 功能特点

✅ **基础舵机控制**
- 支持16通道独立控制（PCA9685的所有通道）
- 精确的角度控制
- 平滑移动功能
- 批量控制多个舵机

✅ **角度限位保护**
- 为每个舵机设置独立的角度限位
- 防止舵机超出安全范围
- 动态修改限位配置

✅ **WiFi网络控制**
- HTTP RESTful API接口
- Web可视化控制界面
- 支持远程控制
- 跨平台访问（手机、电脑、平板）

## 硬件连接

### 所需硬件
- Raspberry Pi Pico2W（或Pico W）
- PCA9685 16通道PWM舵机驱动板
- 舵机（1-16个）
- 5V电源（为舵机供电）
- 杜邦线

### 接线说明

**I2C连接（Pico2W → PCA9685）：**
```
Pico2W GP0  →  PCA9685 SDA
Pico2W GP1  →  PCA9685 SCL
Pico2W GND  →  PCA9685 GND
Pico2W 3.3V →  PCA9685 VCC
```

**舵机供电（重要）：**
```
外部5V电源+ →  PCA9685 V+
外部5V电源- →  PCA9685 GND（与Pico2W共地）
```

**舵机连接：**
- 将舵机插入PCA9685的通道0-15
- 注意舵机线序：橙/黄（信号）、红（+5V）、棕/黑（GND）

## 软件安装

### 1. 安装CircuitPython固件

1. 下载Pico2W的CircuitPython固件：
   - 访问 https://circuitpython.org/board/raspberry_pi_pico_w/
   - 下载最新版本（建议9.0.0或更高）

2. 安装固件到Pico2W：
   - 按住BOOTSEL按钮，连接USB
   - 拖放.uf2文件到CIRCUITPY盘符
   - 设备将自动重启

### 2. 安装库文件

项目已包含所需库文件在 `lib/` 目录：
- `adafruit_pca9685.mpy` - PCA9685驱动
- `adafruit_motor/` - 舵机控制库
- `adafruit_register/` - 寄存器操作库

如需更新库，访问：https://circuitpython.org/libraries

### 3. 部署代码

**推荐方式：使用自动部署工具**

```bash
# 增量部署（只复制变化的文件）
python tools/deploy.py

# Windows快捷方式
tools\deploy.bat

# 查看部署状态
python tools/deploy.py --status

# 部署并清理旧文件
python tools/deploy.py --clean
```

部署工具特性：
- ✅ 自动查找Pico设备
- ✅ 增量更新（基于文件哈希）
- ✅ 记录已部署的依赖，避免重复写入
- ✅ 智能跳过未改变的文件，延长闪存寿命
- ✅ 可选清理旧文件

详细说明请查看 [tools/README.md](tools/README.md)

**手动方式（不推荐）：**

将 `app/` 目录下的所有文件和 `lib/` 目录复制到Pico2W的根目录。

## 配置说明

### 方法1：直接修改 code.py

编辑 [app/code.py](app/code.py) 中的配置区域：

```python
# WiFi配置
WIFI_SSID = "your_wifi_ssid"          # 修改为你的WiFi名称
WIFI_PASSWORD = "your_wifi_password"  # 修改为你的WiFi密码

# 舵机配置
SERVO_CONFIG = [
    (0, 0, 180, 500, 2500),    # (通道, 最小角度, 最大角度, 最小脉冲, 最大脉冲)
    (1, 45, 135, 500, 2500),   # 通道1限位45-135度
    (2, 0, 90, 500, 2500),     # 通道2限位0-90度
]
```

### 方法2：使用配置文件

1. 编辑 [app/config.json](app/config.json)：

```json
{
    "wifi": {
        "ssid": "your_wifi_ssid",
        "password": "your_wifi_password"
    },
    "server": {
        "port": 80
    },
    "servos": [
        {
            "channel": 0,
            "name": "Servo 1",
            "min_angle": 0,
            "max_angle": 180,
            "min_pulse": 500,
            "max_pulse": 2500,
            "initial_angle": 90
        }
    ]
}
```

2. 在Pico2W上重命名启动文件（部署后）：
   - 将 `code.py` 重命名为 `code_backup.py`
   - 将 `code_with_config.py` 重命名为 `code.py`

## 使用方法

### 启动系统

1. 确保配置正确
2. 连接舵机和电源
3. 重启Pico2W或按Ctrl+D重新加载
4. 查看串口输出获取IP地址

输出示例：
```
==================================================
Pico2W PCA9685舵机控制系统
==================================================
WiFi连接成功!
IP地址: 192.168.1.100
✅ 系统启动成功！
📱 控制界面: http://192.168.1.100:80
```

### Web控制界面

在浏览器访问显示的IP地址，使用可视化界面控制舵机：

- 🎚️ 滑块调节角度
- ▶️ 点击"设置"立即移动
- 🎯 点击"平滑移动"缓慢移动
- 🔄 "全部居中"将所有舵机移到中心
- 🔌 "禁用所有"停止PWM信号

### API接口

#### 获取所有舵机信息
```bash
GET http://192.168.1.100/api/info
```

响应示例：
```json
{
    "success": true,
    "servos": {
        "0": {
            "current_angle": 90,
            "limits": [0, 180],
            "min_angle": 0,
            "max_angle": 180
        }
    }
}
```

#### 获取单个舵机状态
```bash
GET http://192.168.1.100/api/servo/0
```

#### 设置舵机角度
```bash
POST http://192.168.1.100/api/servo/0
Content-Type: application/json

{
    "angle": 90,
    "smooth": false
}
```

#### 设置舵机限位
```bash
POST http://192.168.1.100/api/servo/0
Content-Type: application/json

{
    "limits": {
        "min": 0,
        "max": 180
    }
}
```

#### 所有舵机归中
```bash
POST http://192.168.1.100/api/center
```

#### 禁用舵机
```bash
POST http://192.168.1.100/api/disable

# 或禁用指定通道
Content-Type: application/json
{
    "channel": 0
}
```

### Python控制示例

```python
import requests

BASE_URL = "http://192.168.1.100"

# 设置舵机角度
requests.post(f"{BASE_URL}/api/servo/0", 
              json={"angle": 90, "smooth": True})

# 获取舵机信息
info = requests.get(f"{BASE_URL}/api/info").json()
print(info)

# 所有舵机归中
requests.post(f"{BASE_URL}/api/center")
```

## 代码模块说明

### servo_controller.py
舵机控制核心模块，提供：
- `ServoController` 类：管理PCA9685和舵机
- `add_servo()`: 添加舵机配置
- `set_angle()`: 设置舵机角度（支持平滑移动）
- `set_limits()`: 设置角度限位
- `center_all()`: 所有舵机归中
- `disable()`: 禁用舵机

### web_server.py
网络服务器模块，提供：
- `WebServer` 类：HTTP服务器
- `connect_wifi()`: WiFi连接
- RESTful API接口
- HTML控制界面

### code.py
主程序，负责：
- 初始化硬件
- 配置舵机
- 启动Web服务器
- 主循环处理请求

## 调试工具

### 串口监控
```bash
python tools/monitor.py
```

### 文件监控和自动部署
```bash
python tools/watcher.py
```

## 故障排除

### WiFi连接失败
- 检查SSID和密码是否正确
- 确认WiFi是2.4GHz网络（Pico2W不支持5GHz）
- 检查信号强度

### 舵机不动
- 检查舵机电源（需要独立5V供电）
- 确认I2C接线正确
- 检查舵机通道配置
- 查看串口输出的错误信息

### 舵机抖动
- 检查电源供应是否充足
- 降低同时移动的舵机数量
- 调整脉冲宽度参数（min_pulse, max_pulse）

### 角度不准确
- 校准脉冲宽度参数
- 不同舵机品牌的脉冲范围可能不同
- 常见范围：500-2500us或1000-2000us

### Web界面无法访问
- 确认Pico2W已连接WiFi
- 检查电脑/手机与Pico2W在同一网络
- 尝试ping IP地址
- 检查防火墙设置

### 部署失败
- 确认Pico已连接并显示为CIRCUITPY盘符
- 检查是否有其他程序占用Pico（关闭串口监控）
- 使用 `python tools/deploy.py --force` 强制重新部署
- 查看详细错误信息

## 高级功能

### 自定义脉冲宽度
不同品牌的舵机可能需要不同的脉冲宽度：

```python
# SG90舵机: 500-2400us
controller.add_servo(0, 0, 180, 500, 2400)

# MG996R舵机: 1000-2000us
controller.add_servo(1, 0, 180, 1000, 2000)
```

### 平滑移动控制
```python
# 快速移动
controller.set_angle(0, 90, smooth=False)

# 慢速平滑移动
controller.set_angle(0, 90, smooth=True, step=2, delay=0.05)
```

### 批量控制
```python
# 同时设置多个舵机
angles = {0: 45, 1: 90, 2: 135}
controller.set_multiple(angles, smooth=True)
```

## 项目结构

```
pico-hello-world/
├── app/                       # 应用代码（将被部署到Pico）
│   ├── code.py               # 主程序（硬编码配置）
│   ├── code_with_config.py   # 主程序（配置文件版）
│   ├── servo_controller.py   # 舵机控制模块
│   ├── web_server.py        # Web服务器模块
│   └── config.json          # 配置文件
├── lib/                      # CircuitPython库（将被部署到Pico）
│   ├── adafruit_pca9685.mpy
│   ├── adafruit_motor/
│   └── adafruit_register/
├── tools/                    # 开发工具（本地使用）
│   ├── deploy.py            # 智能部署脚本
│   ├── deploy.bat           # Windows快捷方式
│   ├── deploy.sh            # Linux/macOS快捷方式
│   └── README.md            # 工具说明文档
├── README.md                # 项目说明文档
└── pyproject.toml           # Python项目配置
```

## 许可证

MIT License

## 参考资料

- [CircuitPython Documentation](https://docs.circuitpython.org/)
- [Adafruit PCA9685 Guide](https://learn.adafruit.com/16-channel-pwm-servo-driver)
- [Raspberry Pi Pico W Documentation](https://www.raspberrypi.com/documentation/microcontrollers/)

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0 (2025-12-23)
- ✅ 初始版本
- ✅ 基础舵机控制功能
- ✅ 角度限位保护
- ✅ WiFi网络控制
- ✅ Web可视化界面
- ✅ RESTful API
