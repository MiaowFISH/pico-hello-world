<template>
  <div class="app-container">
    <header class="header card">
      <h1>🤖 履带机械臂小车控制面板</h1>
      <div class="header-controls">
        <button @click="refreshStatus" class="btn-primary" :disabled="loading">
          {{ loading ? '刷新中...' : '🔄 刷新状态' }}
        </button>
        <button @click="emergencyStop" class="btn-danger">
          🛑 紧急停止
        </button>
      </div>
      <div v-if="connectionError" class="error-message">
        ⚠️ 连接失败: {{ connectionError }}
      </div>
    </header>

    <div class="control-grid">
      <!-- 履带控制 -->
      <div class="card">
        <h2>🚜 履带控制</h2>
        <div class="track-controls">
          <div class="joystick-buttons">
            <div class="button-row">
              <button @click="moveForward" class="btn-success control-btn">
                ⬆️ 前进
              </button>
            </div>
            <div class="button-row">
              <button @click="turnLeft" class="btn-warning control-btn">
                ⬅️ 左转
              </button>
              <button @click="stopTracks" class="btn-danger control-btn">
                ⏹️ 停止
              </button>
              <button @click="turnRight" class="btn-warning control-btn">
                ➡️ 右转
              </button>
            </div>
            <div class="button-row">
              <button @click="moveBackward" class="btn-success control-btn">
                ⬇️ 后退
              </button>
            </div>
          </div>
          
          <div class="speed-control">
            <label>速度: {{ trackSpeed }}%</label>
            <input 
              type="range" 
              v-model.number="trackSpeed" 
              min="0" 
              max="100" 
              step="5"
            >
          </div>

          <div class="manual-control">
            <h3>差动控制</h3>
            <div class="dual-slider">
              <div class="slider-group">
                <label>左履带: {{ leftTrackSpeed }}%</label>
                <input 
                  type="range" 
                  v-model.number="leftTrackSpeed" 
                  min="-100" 
                  max="100" 
                  step="5"
                >
              </div>
              <div class="slider-group">
                <label>右履带: {{ rightTrackSpeed }}%</label>
                <input 
                  type="range" 
                  v-model.number="rightTrackSpeed" 
                  min="-100" 
                  max="100" 
                  step="5"
                >
              </div>
              <button @click="setDifferential" class="btn-primary">
                应用差动控制
              </button>
            </div>
          </div>

          <div v-if="trackStatus" class="status-display">
            <div class="status-item">
              <span>左履带:</span>
              <span class="status-value">{{ trackStatus.left_speed }}%</span>
            </div>
            <div class="status-item">
              <span>右履带:</span>
              <span class="status-value">{{ trackStatus.right_speed }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底盘旋转控制 -->
      <div class="card">
        <h2>🔄 底盘旋转</h2>
        <div class="base-controls">
          <div class="rotation-buttons">
            <button @click="rotateCW" class="btn-primary control-btn">
              ↻ 顺时针
            </button>
            <button @click="stopBase" class="btn-danger control-btn">
              ⏹️ 停止
            </button>
            <button @click="rotateCCW" class="btn-primary control-btn">
              ↺ 逆时针
            </button>
          </div>

          <div class="speed-control">
            <label>旋转速度: {{ baseSpeed }}%</label>
            <input 
              type="range" 
              v-model.number="baseSpeed" 
              min="0" 
              max="100" 
              step="5"
            >
          </div>

          <div v-if="baseStatus" class="status-display">
            <div class="status-item">
              <span>当前速度:</span>
              <span class="status-value">{{ baseStatus.speed }}%</span>
            </div>
            <div class="status-item">
              <span>状态:</span>
              <span class="status-value">{{ baseStatus.enabled ? '✅ 工作中' : '⏸️ 休眠' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 机械臂舵机控制 -->
      <div class="card servo-control">
        <h2>🦾 机械臂控制</h2>
        <div class="servo-actions">
          <button @click="centerAllServos" class="btn-success">
            🎯 全部居中
          </button>
          <button @click="disableAllServos" class="btn-secondary">
            🔌 禁用舵机
          </button>
        </div>

        <div v-if="servos && Object.keys(servos).length > 0" class="servos-list">
          <div 
            v-for="(servo, channel) in servos" 
            :key="channel" 
            class="servo-item"
          >
            <h3>舵机 {{ channel }}</h3>
            <div class="servo-info">
              <span>当前角度: <strong>{{ servo.current_angle || 'N/A' }}°</strong></span>
              <span>限位: {{ servo.min_angle }}° - {{ servo.max_angle }}°</span>
            </div>
            <div class="servo-slider">
              <input 
                type="range" 
                :min="servo.min_angle" 
                :max="servo.max_angle" 
                v-model.number="servoAngles[channel]"
                @input="updateServoDisplay(channel)"
              >
              <span class="angle-display">{{ servoAngles[channel] }}°</span>
            </div>
            <div class="servo-buttons">
              <button 
                @click="setServoAngle(channel, false)" 
                class="btn-primary btn-sm"
              >
                快速设置
              </button>
              <button 
                @click="setServoAngle(channel, true)" 
                class="btn-success btn-sm"
              >
                平滑移动
              </button>
            </div>
          </div>
        </div>
        <div v-else class="no-servos">
          暂无舵机配置
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import api from './api.js'

export default {
  name: 'App',
  setup() {
    const loading = ref(false)
    const connectionError = ref(null)
    const servos = ref({})
    const servoAngles = ref({})
    const trackStatus = ref(null)
    const baseStatus = ref(null)
    
    const trackSpeed = ref(50)
    const baseSpeed = ref(50)
    const leftTrackSpeed = ref(0)
    const rightTrackSpeed = ref(0)

    // 刷新状态
    const refreshStatus = async () => {
      if (loading.value) return
      
      loading.value = true
      connectionError.value = null

      try {
        // 只调用一个接口获取所有状态，避免并发请求导致CircuitPython服务器崩溃
        const statusRes = await api.getStatus()

        if (statusRes.success) {
          // 更新履带和底盘状态
          trackStatus.value = statusRes.status.tracks
          baseStatus.value = statusRes.status.base_rotation
          
          // 更新舵机状态
          if (statusRes.status.servos) {
            servos.value = statusRes.status.servos
            // 初始化舵机角度
            Object.keys(statusRes.status.servos).forEach(channel => {
              const servo = statusRes.status.servos[channel]
              servoAngles.value[channel] = servo.current_angle || 
                Math.round((servo.min_angle + servo.max_angle) / 2)
            })
          }
        }
      } catch (error) {
        connectionError.value = error.message || '无法连接到设备'
        console.error('Refresh error:', error)
      } finally {
        loading.value = false
      }
    }

    // 履带控制
    const moveForward = async () => {
      try {
        await api.controlTracks('forward', trackSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Forward error:', error)
      }
    }

    const moveBackward = async () => {
      try {
        await api.controlTracks('backward', trackSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Backward error:', error)
      }
    }

    const turnLeft = async () => {
      try {
        await api.controlTracks('left', trackSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Turn left error:', error)
      }
    }

    const turnRight = async () => {
      try {
        await api.controlTracks('right', trackSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Turn right error:', error)
      }
    }

    const stopTracks = async () => {
      try {
        await api.controlTracks('stop')
        await refreshStatus()
      } catch (error) {
        console.error('Stop tracks error:', error)
      }
    }

    const setDifferential = async () => {
      try {
        await api.controlTracks('set', 0, leftTrackSpeed.value, rightTrackSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Differential control error:', error)
      }
    }

    // 底盘旋转控制
    const rotateCW = async () => {
      try {
        await api.controlBase('cw', baseSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Rotate CW error:', error)
      }
    }

    const rotateCCW = async () => {
      try {
        await api.controlBase('ccw', baseSpeed.value)
        await refreshStatus()
      } catch (error) {
        console.error('Rotate CCW error:', error)
      }
    }

    const stopBase = async () => {
      try {
        await api.controlBase('stop')
        await refreshStatus()
      } catch (error) {
        console.error('Stop base error:', error)
      }
    }

    // 舵机控制
    const setServoAngle = async (channel, smooth) => {
      try {
        const angle = servoAngles.value[channel]
        await api.setServoAngle(channel, angle, smooth)
        setTimeout(refreshStatus, 300)
      } catch (error) {
        console.error('Set servo angle error:', error)
      }
    }

    const updateServoDisplay = (channel) => {
      // 实时更新显示，不发送请求
    }

    const centerAllServos = async () => {
      try {
        await api.centerAllServos()
        await refreshStatus()
      } catch (error) {
        console.error('Center servos error:', error)
      }
    }

    const disableAllServos = async () => {
      try {
        await api.disableServos()
        await refreshStatus()
      } catch (error) {
        console.error('Disable servos error:', error)
      }
    }

    // 紧急停止
    const emergencyStop = async () => {
      try {
        await api.emergencyStop()
        await refreshStatus()
      } catch (error) {
        console.error('Emergency stop error:', error)
      }
    }

    // 生命周期
    onMounted(() => {
      refreshStatus()
    })

    onUnmounted(() => {
      // 清理工作（如果有需要）
    })

    return {
      loading,
      connectionError,
      servos,
      servoAngles,
      trackStatus,
      baseStatus,
      trackSpeed,
      baseSpeed,
      leftTrackSpeed,
      rightTrackSpeed,
      refreshStatus,
      moveForward,
      moveBackward,
      turnLeft,
      turnRight,
      stopTracks,
      setDifferential,
      rotateCW,
      rotateCCW,
      stopBase,
      setServoAngle,
      updateServoDisplay,
      centerAllServos,
      disableAllServos,
      emergencyStop
    }
  }
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-size: 32px;
  color: #2d3748;
  margin-bottom: 20px;
  text-align: center;
}

.header-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #fed7d7;
  color: #c53030;
  border-radius: 8px;
  text-align: center;
}

.control-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.card h2 {
  font-size: 24px;
  color: #2d3748;
  margin-bottom: 20px;
  border-bottom: 3px solid #667eea;
  padding-bottom: 10px;
}

/* 履带控制 */
.track-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.joystick-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.button-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.control-btn {
  min-width: 100px;
  padding: 15px 20px;
  font-size: 18px;
}

.speed-control {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.speed-control label {
  font-weight: 600;
  color: #4a5568;
}

.manual-control h3 {
  font-size: 18px;
  color: #4a5568;
  margin-bottom: 15px;
}

.dual-slider {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-group label {
  font-weight: 600;
  color: #4a5568;
  font-size: 14px;
}

/* 底盘控制 */
.base-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.rotation-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

/* 状态显示 */
.status-display {
  background: #f7fafc;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.status-item span:first-child {
  color: #718096;
}

.status-value {
  font-weight: 700;
  color: #2d3748;
}

/* 舵机控制 */
.servo-control {
  grid-column: 1 / -1;
}

.servo-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.servos-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.servo-item {
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  background: #f7fafc;
}

.servo-item h3 {
  font-size: 18px;
  color: #2d3748;
  margin-bottom: 12px;
}

.servo-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #4a5568;
}

.servo-info strong {
  color: #667eea;
  font-size: 16px;
}

.servo-slider {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.angle-display {
  min-width: 50px;
  font-weight: 700;
  font-size: 18px;
  color: #667eea;
  text-align: right;
}

.servo-buttons {
  display: flex;
  gap: 10px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

.no-servos {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
  font-size: 16px;
}

@media (max-width: 768px) {
  .control-grid {
    grid-template-columns: 1fr;
  }

  .header h1 {
    font-size: 24px;
  }

  .control-btn {
    min-width: 80px;
    padding: 12px 16px;
    font-size: 16px;
  }
}
</style>
