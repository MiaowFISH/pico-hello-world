# HTTP API Contract

**Protocol**: HTTP/1.1  
**Base URL**: `http://<device-ip>`  
**Purpose**: Configuration queries and status retrieval (非实时操作)

---

## Endpoints

### 1. GET / (Frontend)

Serve the built frontend static files.

**Response**: HTML page (index.html)

---

### 2. GET /api/status

Get current device status.

**Response** (200 OK):
```json
{
  "wifi": {
    "connected": true,
    "ssid": "mi-router-ax3000t-2g-0fdbd",
    "ip_address": "192.168.1.100",
    "rssi": -45
  },
  "servos": [
    {
      "channel": 0,
      "name": "机械臂关节1",
      "current_angle": 90,
      "min_angle": 70,
      "max_angle": 150
    },
    {
      "channel": 1,
      "name": "机械臂关节2",
      "current_angle": 60,
      "min_angle": 50,
      "max_angle": 90
    },
    {
      "channel": 2,
      "name": "机械臂夹爪",
      "current_angle": 90,
      "min_angle": 45,
      "max_angle": 135
    }
  ],
  "tracks": {
    "left_speed": 0,
    "right_speed": 0,
    "enabled": true
  },
  "base_rotation": {
    "direction": "stop",
    "speed": 0,
    "sleeping": true
  },
  "last_command_ms": 5000,
  "uptime_ms": 120000,
  "errors": []
}
```

---

### 3. GET /api/config

Get device configuration (for frontend initialization).

**Response** (200 OK):
```json
{
  "servos": [
    {
      "channel": 0,
      "name": "机械臂关节1",
      "min_angle": 70,
      "max_angle": 150,
      "initial_angle": 90
    },
    {
      "channel": 1,
      "name": "机械臂关节2",
      "min_angle": 50,
      "max_angle": 90,
      "initial_angle": 60
    },
    {
      "channel": 2,
      "name": "机械臂夹爪",
      "min_angle": 45,
      "max_angle": 135,
      "initial_angle": 90
    }
  ],
  "speed_presets": {
    "slow": 30,
    "medium": 60,
    "fast": 100
  },
  "safety": {
    "command_timeout_ms": 2000
  }
}
```

**Note**: WiFi password is NOT included for security.

---

### 4. GET /api/health

Simple health check endpoint.

**Response** (200 OK):
```json
{
  "status": "ok",
  "uptime_ms": 120000
}
```

---

## Static File Serving

| Path | Description |
|------|-------------|
| `/` | index.html |
| `/assets/*` | JavaScript, CSS bundles |
| `/favicon.ico` | Favicon (optional) |

**Content-Type Headers**:
- `.html` → `text/html`
- `.js` → `application/javascript`
- `.css` → `text/css`
- `.json` → `application/json`
- `.ico` → `image/x-icon`

---

## Error Responses

### 404 Not Found
```json
{
  "error": "not_found",
  "path": "/api/unknown"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "I2C communication failed"
}
```

---

## CORS Headers

For development (frontend on different port):
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Note**: In production, frontend is served from same origin, CORS not required.
