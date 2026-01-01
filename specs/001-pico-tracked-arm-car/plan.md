# Implementation Plan: Pico2W 履带机械臂小车控制系统

**Branch**: `001-pico-tracked-arm-car` | **Date**: 2026-01-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pico-tracked-arm-car/spec.md`

## Summary

基于Raspberry Pi Pico2W的履带机械臂小车远程控制系统。后端使用CircuitPython实现WebSocket实时控制接口和HTTP配置API，前端使用React+TypeScript+Vite构建响应式移动端优先的控制界面。系统采用配置驱动设计，支持3个舵机机械臂、双履带差动转向和底盘旋转功能。

## Technical Context

**Language/Version**: CircuitPython 9.x (backend) + TypeScript 5.x (frontend)  
**Primary Dependencies**: 
- Backend: adafruit_httpserver, adafruit_pca9685, adafruit_motor
- Frontend: React 18, Vite 5, react-use-websocket, zustand  
**Storage**: JSON config file on Pico flash  
**Testing**: Manual integration testing (hardware-dependent)  
**Target Platform**: Raspberry Pi Pico 2W + Modern browsers (Chrome/Firefox/Safari)
**Project Type**: Web (frontend + backend)  
**Performance Goals**: WebSocket control latency <50ms, UI response <100ms  
**Constraints**: Single WebSocket connection, ~180KB heap memory, 2.4GHz WiFi only  
**Scale/Scope**: Single user, 3 servos, 2 track motors, 1 rotation motor

## Constitution Check

*GATE: No constitution defined - proceeding with standard practices.*

✅ No violations - project follows embedded + web development best practices.

## Project Structure

### Documentation (this feature)

```text
specs/001-pico-tracked-arm-car/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technology research notes
├── data-model.md        # Entity and state definitions
├── quickstart.md        # Setup and deployment guide
├── contracts/
│   ├── websocket-api.md # WebSocket message format
│   └── http-api.md      # HTTP endpoint definitions
└── tasks.md             # Task breakdown (Phase 2 - /speckit.tasks)
```

### Source Code (repository root)

```text
app/                          # Backend - deploys to Pico root
├── main.py                   # Entry point, asyncio loop
├── config.json               # Hardware configuration
├── config_loader.py          # Configuration loading/validation
├── servo_controller.py       # PCA9685 servo control
├── motor_controller.py       # TB6612 track motors
├── base_rotation_controller.py  # DRV8837 base rotation
├── websocket_handler.py      # WebSocket message processing
└── http_handler.py           # HTTP routes for status/config

lib/                          # CircuitPython libraries (existing)
├── adafruit_httpserver/      # HTTP + WebSocket server
├── adafruit_pca9685.mpy      # I2C PWM driver
├── adafruit_motor/           # Servo abstractions
└── adafruit_register/        # I2C register utilities

frontend/                     # Frontend - builds to static/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
└── src/
    ├── main.tsx              # React entry point
    ├── App.tsx               # Main app component
    ├── hooks/
    │   ├── useDeviceWebSocket.ts   # WebSocket connection
    │   ├── useContinuousCommand.ts # Press-and-hold logic
    │   └── useDeviceStore.ts       # Zustand state store
    ├── components/
    │   ├── ConnectionStatus.tsx    # WiFi/WS status display
    │   ├── TrackControls.tsx       # D-pad for movement
    │   ├── SpeedSelector.tsx       # Slow/Medium/Fast
    │   ├── ServoSliders.tsx        # Angle sliders per joint
    │   ├── BaseRotation.tsx        # CW/CCW buttons
    │   └── StatusPanel.tsx         # Device state display
    └── styles/
        └── main.css                # Mobile-first responsive CSS

tools/                        # Deployment utilities (existing)
├── deploy.py
├── deploy.bat
└── deploy.sh
```

**Structure Decision**: Web application pattern with `app/` (backend) and `frontend/` (frontend). Backend code deploys directly to Pico root. Frontend builds to `static/` and is served by Pico's HTTP server.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (PC/Mobile)                      │
├─────────────────────────────────────────────────────────────┤
│  React App                                                  │
│  ├── WebSocket Client (real-time control)                   │
│  ├── HTTP Client (config/status queries)                    │
│  └── Zustand Store (local state)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ WiFi (LAN)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Raspberry Pi Pico 2W                       │
├─────────────────────────────────────────────────────────────┤
│  adafruit_httpserver                                        │
│  ├── Static file server (frontend assets)                   │
│  ├── HTTP API (/api/status, /api/config)                    │
│  └── WebSocket endpoint (/ws)                               │
├─────────────────────────────────────────────────────────────┤
│  Application Logic                                          │
│  ├── Config Loader (config.json → runtime config)           │
│  ├── Safety Monitor (2s timeout, auto-stop)                 │
│  └── Command Dispatcher (route WS messages to controllers)  │
├─────────────────────────────────────────────────────────────┤
│  Hardware Controllers                                       │
│  ├── ServoController (I2C → PCA9685 → 3x Servos)            │
│  ├── TrackController (PWM/GPIO → TB6612 → 2x DC Motors)     │
│  └── BaseController (PWM/GPIO → DRV8837 → 1x Worm Motor)    │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **WebSocket for Control**: HTTP latency (100-400ms) unacceptable for real-time control; WebSocket achieves <50ms
2. **Single WS Connection**: Pico memory constraint limits to one active WebSocket; new connection closes existing
3. **Press-and-Hold Pattern**: Continuous commands while button pressed; stops on release or timeout
4. **2-Second Safety Timeout**: Auto-stop motors if no command received (WiFi drop protection)
5. **Config-Driven**: All hardware parameters in `config.json`; no code changes for pin remapping
6. **Frontend on Pico**: Single device deployment; user accesses Pico IP directly

## Related Documents

- [spec.md](spec.md) - Feature specification and requirements
- [research.md](research.md) - Technology research and decisions
- [data-model.md](data-model.md) - Entity definitions and state machines
- [contracts/websocket-api.md](contracts/websocket-api.md) - WebSocket message protocol
- [contracts/http-api.md](contracts/http-api.md) - HTTP endpoint definitions
- [quickstart.md](quickstart.md) - Setup and deployment guide

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
