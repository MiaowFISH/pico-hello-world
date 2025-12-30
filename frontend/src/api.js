import axios from 'axios'

// 配置axios基础URL
const API_BASE_URL = import.meta.env.DEV 
  ? '/api'  // 开发环境使用代理
  : 'http://192.168.1.200/api'  // 生产环境直接访问Pico IP

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API方法
export default {
  // 获取所有状态
  getStatus() {
    return api.get('/status')
  },

  // 获取舵机信息
  getServoInfo() {
    return api.get('/info')
  },

  // 控制舵机
  setServoAngle(channel, angle, smooth = false) {
    return api.post(`/servo/${channel}`, { angle, smooth })
  },

  // 设置舵机限位
  setServoLimits(channel, minAngle, maxAngle) {
    return api.post(`/servo/${channel}`, {
      limits: { min: minAngle, max: maxAngle }
    })
  },

  // 居中所有舵机
  centerAllServos() {
    return api.get('/center')
  },

  // 禁用舵机
  disableServos(channel = null) {
    return api.post('/disable', channel ? { channel } : {})
  },

  // 控制履带
  controlTracks(action, speed = 50, leftSpeed = 0, rightSpeed = 0) {
    const data = { action, speed }
    if (action === 'set') {
      data.left_speed = leftSpeed
      data.right_speed = rightSpeed
    }
    return api.post('/tracks', data)
  },

  // 控制底盘旋转
  controlBase(action, speed = 50, rotationSpeed = 0) {
    const data = { action, speed }
    if (action === 'set') {
      data.rotation_speed = rotationSpeed
    }
    return api.post('/base', data)
  },

  // 紧急停止
  emergencyStop() {
    return api.post('/emergency_stop')
  }
}
