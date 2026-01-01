# WebSocket API Contract

**Protocol**: WebSocket  
**Endpoint**: `ws://<device-ip>/ws`  
**Purpose**: Real-time control commands (低延迟 <50ms)

## Connection

### Handshake
- Standard WebSocket upgrade from HTTP
- Single connection per device (new connection closes existing)

### Heartbeat
- Client sends `ping` every 25 seconds
- Server responds with `pong`
- Connection timeout: 60 seconds without activity

---

## Message Format

All messages are JSON objects with `action` field.

### Client → Server (Commands)

#### 1. Track Control (履带控制)
```json
{
  "action": "track",
  "left": 60,      // -100 to 100 (negative = reverse)
  "right": 60     // -100 to 100
}
```

**Shorthand Commands**:
```json
{ "action": "track", "command": "forward", "speed": "medium" }
{ "action": "track", "command": "backward", "speed": "medium" }
{ "action": "track", "command": "left", "speed": "medium" }
{ "action": "track", "command": "right", "speed": "medium" }
{ "action": "track", "command": "stop" }
```

**Speed Presets**: `slow` (30%), `medium` (60%), `fast` (100%)

---

#### 2. Servo Control (舵机控制)
```json
{
  "action": "servo",
  "channel": 0,     // 0-2 for arm joints
  "angle": 90       // Will be clamped to configured min/max
}
```

**Batch Update**:
```json
{
  "action": "servo_batch",
  "angles": [90, 60, 90]  // [joint1, joint2, gripper]
}
```

**Reset to Initial**:
```json
{
  "action": "servo_reset"
}
```

---

#### 3. Base Rotation Control (底盘旋转)
```json
{
  "action": "base",
  "direction": "cw",   // "cw", "ccw", "stop"
  "speed": 80          // 0-100 (optional, default 100)
}
```

---

#### 4. Ping (心跳)
```json
{
  "action": "ping"
}
```

---

### Server → Client (Responses)

#### Command Acknowledgment
```json
{
  "status": "ok",
  "action": "track",
  "timestamp": 1704067200000
}
```

#### Error Response
```json
{
  "status": "error",
  "action": "servo",
  "error": "angle_out_of_range",
  "message": "Angle 200 exceeds max 150 for channel 0",
  "clamped_value": 150
}
```

#### Pong (心跳响应)
```json
{
  "status": "pong",
  "timestamp": 1704067200000
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `invalid_action` | Unknown action type |
| `invalid_json` | Malformed JSON message |
| `angle_out_of_range` | Servo angle outside configured limits |
| `speed_out_of_range` | Speed value outside -100~100 |
| `channel_not_found` | Servo channel doesn't exist |

---

## Safety Behavior

1. **Command Timeout**: If no command received for 2 seconds, tracks and base rotation automatically stop
2. **Connection Lost**: Same as timeout - all motors stop, servos hold position
3. **Angle Clamping**: Out-of-range angles are automatically clamped and acknowledged with `clamped_value`
