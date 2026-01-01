# Research Notes: Pico2W 履带机械臂小车控制系统

**Date**: 2026-01-01  
**Branch**: `001-pico-tracked-arm-car`

## Research Topics

### 1. CircuitPython WebSocket Server

**Decision**: Use `adafruit_httpserver` library (v4.7+)

**Rationale**:
- Official Adafruit library, actively maintained
- Integrated HTTP + WebSocket in single package
- Native `socketpool` support for Pico W WiFi
- Well-documented asyncio patterns

**Alternatives Considered**:
- Raw socket implementation - would require implementing RFC 6455 from scratch
- MicroPython websocket libs - not compatible with CircuitPython
- Third-party libs - none exist for CircuitPython

**Key Implementation Patterns**:
```python
from adafruit_httpserver import Server, Websocket, Request, Response
import asyncio

# Single WebSocket connection (memory constraint)
websocket: Websocket = None

async def handle_websocket():
    while True:
        if websocket is not None:
            data = websocket.receive(fail_silently=True)
            if data:
                process_command(data)
        await asyncio.sleep(0)  # Yield immediately for low latency
```

**Limitations**:
- Single WebSocket connection only (limited sockets on Pico)
- Memory: ~150-180KB available heap after WiFi stack (Pico W)
- Latency floor: 10-20ms minimum (WiFi + TCP overhead)
- Use `fail_silently=True` to prevent crashes on disconnect

---

### 2. PCA9685 Servo Control

**Decision**: Continue using `adafruit_pca9685` + `adafruit_motor.servo`

**Rationale**:
- Already optimal - official Adafruit libraries
- High-level API abstracts pulse width math
- Existing `servo_controller.py` follows best practices

**Code Pattern**:
```python
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

pca = PCA9685(i2c)
pca.frequency = 50  # Standard servo frequency

servo0 = servo.Servo(
    pca.channels[0],
    min_pulse=500,   # μs for 0°
    max_pulse=2500,  # μs for 180°
)
servo0.angle = 90  # Set directly in degrees
```

**Limitations**:
- All 16 channels share one frequency (50Hz for servos)
- I2C latency ~20ms when setting multiple servos
- No position feedback from standard servos

---

### 3. TB6612FNG Motor Driver (Tracks)

**Decision**: GPIO PWM + digital direction pins

**Rationale**:
- Simple control pattern: PWM for speed, digital for direction
- Existing `motor_controller.py` implementation is correct

**Control Logic**:
| Action | IN1 | IN2 | PWM |
|--------|-----|-----|-----|
| Forward | HIGH | LOW | Speed% |
| Reverse | LOW | HIGH | Speed% |
| Brake | LOW | LOW | 0 |

**Differential Steering**:
```python
def differential_drive(speed, turn):
    left = speed + turn
    right = speed - turn
    # Normalize to -100..100
    max_val = max(abs(left), abs(right), 100)
    return (left * 100 // max_val, right * 100 // max_val)
```

---

### 4. DRV8837 Motor Driver (Base Rotation)

**Decision**: Dual PWM mode (IN1/IN2 both PWM-capable)

**Rationale**:
- Simpler than PHASE/ENABLE mode
- Native sleep pin for power saving

**Control Logic**:
| Action | IN1 | IN2 |
|--------|-----|-----|
| CW | PWM | 0 |
| CCW | 0 | PWM |
| Brake | HIGH | HIGH |
| Coast | 0 | 0 |

**Sleep Mode**: Pull nSLEEP LOW when idle (existing implementation correct)

---

### 5. React + TypeScript WebSocket Frontend

**Decision**: Use `react-use-websocket` + `zustand` + custom Press-and-Hold hooks

**Rationale**:
- `react-use-websocket`: Built-in reconnection, heartbeat, TypeScript support
- `zustand`: Lightweight state management, no providers
- Custom hooks: Clean separation of WebSocket and control logic

**Key Libraries**:
```json
{
  "react-use-websocket": "^4.13.0",
  "zustand": "^5.0.0"
}
```

**Press-and-Hold Pattern**:
```typescript
const useContinuousCommand = (sendCommand: Function, command: string) => {
  const intervalRef = useRef<number | null>(null);
  
  const start = () => {
    sendCommand(command);
    intervalRef.current = setInterval(() => sendCommand(command), 100);
  };
  
  const stop = () => {
    clearInterval(intervalRef.current!);
    sendCommand('stop');
  };
  
  return { onMouseDown: start, onMouseUp: stop, onTouchStart: start, onTouchEnd: stop };
};
```

**Mobile UX**:
- `touch-action: none` on control elements
- Minimum 44x44px touch targets
- `navigator.vibrate(50)` for haptic feedback

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| WebSocket library for CircuitPython? | `adafruit_httpserver` v4.7+ |
| Achievable latency target? | 30-50ms practical (10-20ms floor) |
| Single or multiple WS connections? | Single only (Pico memory constraint) |
| PWM frequency for motors? | 1000Hz (current) or up to 20kHz for quieter operation |
| Frontend state management? | Zustand (lightweight, no providers) |

---

## Technology Stack Summary

| Component | Technology | Version/Notes |
|-----------|------------|---------------|
| **Backend Runtime** | CircuitPython | 9.x on Pico 2W |
| **HTTP/WS Server** | adafruit_httpserver | 4.7+ with WebSocket |
| **Servo Driver** | adafruit_pca9685 + adafruit_motor | Already in lib/ |
| **Motor PWM** | pwmio (built-in) | 1000Hz frequency |
| **Frontend Framework** | React + TypeScript | Vite bundler |
| **WebSocket Client** | react-use-websocket | 4.13+ |
| **State Management** | Zustand | 5.0+ |
| **Styling** | CSS (responsive) | Mobile-first |
