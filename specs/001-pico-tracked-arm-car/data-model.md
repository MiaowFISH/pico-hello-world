# Data Model: Pico2W 履带机械臂小车控制系统

**Date**: 2026-01-01  
**Branch**: `001-pico-tracked-arm-car`

## Entity Definitions

### 1. SystemConfig (系统配置)

系统启动时从 `config.json` 加载的完整配置。

```
SystemConfig
├── wifi: WifiConfig
├── server: ServerConfig
├── i2c: I2CConfig
├── pca9685: PCA9685Config
├── servos: ServoConfig[]
├── motors: MotorConfig
└── safety: SafetyConfig
```

**WifiConfig**:
| Field | Type | Description |
|-------|------|-------------|
| ssid | string | WiFi网络名称 |
| password | string | WiFi密码 |

**ServerConfig**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| port | int | 80 | HTTP服务器端口 |

**I2CConfig**:
| Field | Type | Description |
|-------|------|-------------|
| sda_pin | string | I2C SDA引脚 (e.g., "GP0") |
| scl_pin | string | I2C SCL引脚 (e.g., "GP1") |

**PCA9685Config**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| frequency | int | 50 | PWM频率 (Hz) |

---

### 2. ServoConfig (舵机配置)

单个舵机的配置参数。

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| channel | int | 0-15 | PCA9685通道号 |
| name | string | - | 舵机名称（显示用） |
| min_angle | int | 0-180 | 最小安全角度 |
| max_angle | int | 0-180 | 最大安全角度 |
| min_pulse | int | 500-2500 | 最小脉宽 (μs) |
| max_pulse | int | 500-2500 | 最大脉宽 (μs) |
| initial_angle | int | min-max | 上电初始角度 |

**Validation Rules**:
- `min_angle < max_angle`
- `min_pulse < max_pulse`
- `initial_angle` ∈ [min_angle, max_angle]

---

### 3. MotorConfig (电机配置)

履带和底盘旋转电机的引脚配置。

**TracksConfig** (TB6612FNG):
| Field | Type | Description |
|-------|------|-------------|
| pwma_pin | string | 左履带PWM引脚 |
| ain1_pin | string | 左履带方向1 |
| ain2_pin | string | 左履带方向2 |
| pwmb_pin | string | 右履带PWM引脚 |
| bin1_pin | string | 右履带方向1 |
| bin2_pin | string | 右履带方向2 |
| stby_pin | string | 驱动器使能引脚 |

**BaseRotationConfig** (DRV8837):
| Field | Type | Description |
|-------|------|-------------|
| in1_pin | string | 方向控制1 |
| in2_pin | string | 方向控制2 |
| sleep_pin | string | 休眠控制引脚 |

---

### 4. SafetyConfig (安全配置)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| command_timeout_ms | int | 2000 | 无命令超时停止 (ms) |
| idle_sleep_ms | int | 5000 | 空闲后DRV8837休眠 (ms) |

---

### 5. ServoState (舵机状态)

运行时单个舵机的状态。

| Field | Type | Description |
|-------|------|-------------|
| channel | int | 通道号 |
| name | string | 舵机名称 |
| current_angle | int | 当前角度 |
| min_angle | int | 最小角度（来自配置） |
| max_angle | int | 最大角度（来自配置） |

---

### 6. TrackState (履带状态)

运行时履带电机组的状态。

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| left_speed | int | -100~100 | 左履带速度（负=后退） |
| right_speed | int | -100~100 | 右履带速度（负=后退） |
| enabled | bool | - | STBY引脚状态 |

---

### 7. BaseRotationState (底盘旋转状态)

| Field | Type | Description |
|-------|------|-------------|
| direction | enum | "cw" / "ccw" / "stop" |
| speed | int | 0-100 速度百分比 |
| sleeping | bool | 是否处于休眠模式 |

---

### 8. DeviceStatus (设备状态)

系统整体状态，用于状态查询API响应。

```
DeviceStatus
├── wifi: WifiStatus
├── servos: ServoState[]
├── tracks: TrackState
├── base_rotation: BaseRotationState
├── last_command_ms: int
└── errors: string[]
```

**WifiStatus**:
| Field | Type | Description |
|-------|------|-------------|
| connected | bool | WiFi是否已连接 |
| ssid | string | 当前连接的SSID |
| ip_address | string | 设备IP地址 |
| rssi | int | 信号强度 (dBm) |

---

## State Transitions

### 履带电机状态转换

```
                ┌─────────┐
                │  IDLE   │
                └────┬────┘
                     │ command received
                     ▼
              ┌──────────────┐
    ┌─────────│   RUNNING    │─────────┐
    │         └──────────────┘         │
    │ stop         │                   │ timeout (2s)
    │ command      │ speed=0           │ no command
    ▼              ▼                   ▼
┌─────────┐   ┌─────────┐        ┌─────────┐
│  IDLE   │   │  IDLE   │        │  IDLE   │
│(normal) │   │(normal) │        │ (safe)  │
└─────────┘   └─────────┘        └─────────┘
```

### DRV8837 休眠状态转换

```
┌─────────┐  command   ┌─────────┐  idle>5s  ┌─────────┐
│ SLEEPING│──received──│ ACTIVE  │───────────│ SLEEPING│
└─────────┘            └─────────┘           └─────────┘
     ▲                      │
     │    stop command      │
     └──────────────────────┘
```

---

## Configuration File Schema

完整的 `config.json` 结构：

```json
{
  "wifi": {
    "ssid": "string",
    "password": "string"
  },
  "server": {
    "port": 80
  },
  "i2c": {
    "sda_pin": "GP0",
    "scl_pin": "GP1"
  },
  "pca9685": {
    "frequency": 50
  },
  "servos": [
    {
      "channel": 0,
      "name": "机械臂关节1",
      "min_angle": 70,
      "max_angle": 150,
      "min_pulse": 500,
      "max_pulse": 2500,
      "initial_angle": 90
    }
  ],
  "motors": {
    "tracks": {
      "pwma_pin": "GP6",
      "ain1_pin": "GP7",
      "ain2_pin": "GP8",
      "pwmb_pin": "GP9",
      "bin1_pin": "GP10",
      "bin2_pin": "GP11",
      "stby_pin": "GP12"
    },
    "base_rotation": {
      "in1_pin": "GP14",
      "in2_pin": "GP15",
      "sleep_pin": "GP13"
    }
  },
  "safety": {
    "command_timeout_ms": 2000,
    "idle_sleep_ms": 5000
  },
  "speed_presets": {
    "slow": 30,
    "medium": 60,
    "fast": 100
  }
}
```
