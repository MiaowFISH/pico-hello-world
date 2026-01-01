/**
 * StatusPanel component
 * Display real-time system status including WiFi, servo angles, motor states
 */

import React from 'react'
import { useDeviceStore } from '../hooks/useDeviceStore'

export const StatusPanel: React.FC = () => {
  const { status } = useDeviceStore()
  
  if (!status) {
    return (
      <div className="status-panel">
        <div className="controls-label">系统状态</div>
        <div className="loading-message">加载状态中...</div>
      </div>
    )
  }
  
  const { wifi, servos, tracks, base_rotation, errors } = status
  
  return (
    <div className="status-panel">
      <div className="controls-label">系统状态</div>
      
      <div className="status-sections">
        {/* WiFi Status */}
        <div className="status-section">
          <h4 className="status-section-title">📡 WiFi 连接</h4>
          <div className="status-items">
            <div className="status-item">
              <span className="status-key">状态:</span>
              <span className={`status-value ${wifi.connected ? 'connected' : 'disconnected'}`}>
                {wifi.connected ? '已连接' : '未连接'}
              </span>
            </div>
            {wifi.connected && (
              <>
                <div className="status-item">
                  <span className="status-key">SSID:</span>
                  <span className="status-value">{wifi.ssid}</span>
                </div>
                <div className="status-item">
                  <span className="status-key">IP:</span>
                  <span className="status-value status-mono">{wifi.ip_address}</span>
                </div>
                {wifi.rssi && (
                  <div className="status-item">
                    <span className="status-key">信号:</span>
                    <span className="status-value">{wifi.rssi} dBm</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        
        {/* Servo Status */}
        <div className="status-section">
          <h4 className="status-section-title">🦾 舵机状态</h4>
          <div className="status-items">
            {servos.map((servo) => (
              <div key={servo.channel} className="status-item">
                <span className="status-key">{servo.name}:</span>
                <span className="status-value status-highlight">
                  {servo.current_angle}° 
                  <span className="status-range">
                    ({servo.min_angle}°-{servo.max_angle}°)
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Track Motor Status */}
        <div className="status-section">
          <h4 className="status-section-title">🚗 履带状态</h4>
          <div className="status-items">
            <div className="status-item">
              <span className="status-key">左履带:</span>
              <span className={`status-value ${tracks.left_speed !== 0 ? 'status-active' : ''}`}>
                {tracks.left_speed > 0 ? '前进' : tracks.left_speed < 0 ? '后退' : '停止'} 
                ({Math.abs(tracks.left_speed)}%)
              </span>
            </div>
            <div className="status-item">
              <span className="status-key">右履带:</span>
              <span className={`status-value ${tracks.right_speed !== 0 ? 'status-active' : ''}`}>
                {tracks.right_speed > 0 ? '前进' : tracks.right_speed < 0 ? '后退' : '停止'} 
                ({Math.abs(tracks.right_speed)}%)
              </span>
            </div>
            <div className="status-item">
              <span className="status-key">驱动器:</span>
              <span className={`status-value ${tracks.enabled ? 'connected' : 'disconnected'}`}>
                {tracks.enabled ? '启用' : '待机'}
              </span>
            </div>
          </div>
        </div>
        
        {/* Base Rotation Status */}
        <div className="status-section">
          <h4 className="status-section-title">🔄 底盘旋转</h4>
          <div className="status-items">
            <div className="status-item">
              <span className="status-key">方向:</span>
              <span className={`status-value ${base_rotation.direction !== 'stop' ? 'status-active' : ''}`}>
                {base_rotation.direction === 'cw' ? '顺时针' : 
                 base_rotation.direction === 'ccw' ? '逆时针' : '停止'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-key">速度:</span>
              <span className="status-value">{base_rotation.speed}%</span>
            </div>
            <div className="status-item">
              <span className="status-key">电机:</span>
              <span className={`status-value ${!base_rotation.sleeping ? 'connected' : 'disconnected'}`}>
                {base_rotation.sleeping ? '休眠' : '活动'}
              </span>
            </div>
          </div>
        </div>
        
        {/* Errors */}
        {errors && errors.length > 0 && (
          <div className="status-section status-errors">
            <h4 className="status-section-title">⚠️ 错误信息</h4>
            <div className="error-list">
              {errors.map((error, index) => (
                <div key={index} className="error-item">
                  {error}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
