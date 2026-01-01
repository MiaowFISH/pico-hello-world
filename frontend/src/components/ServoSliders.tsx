/**
 * ServoSliders component
 * Three angle sliders for controlling mechanical arm joints
 */

import React from 'react'
import { useDeviceStore } from '../hooks/useDeviceStore'

interface ServoSlidersProps {
  sendCommand: (command: object) => void
  disabled?: boolean
}

export const ServoSliders: React.FC<ServoSlidersProps> = ({
  sendCommand,
  disabled = false
}) => {
  const { config, status } = useDeviceStore()
  
  const servos = config?.servos || []
  const servoStates = status?.servos || []
  
  const handleAngleChange = (channel: number, angle: number) => {
    sendCommand({
      action: 'servo',
      channel,
      angle
    })
  }
  
  const handleReset = () => {
    sendCommand({
      action: 'servo_reset'
    })
  }
  
  if (servos.length === 0) {
    return (
      <div className="servo-sliders">
        <div className="controls-label">机械臂控制</div>
        <div className="loading-message">加载配置中...</div>
      </div>
    )
  }
  
  return (
    <div className="servo-sliders">
      <div className="controls-label">机械臂控制</div>
      
      <div className="sliders-container">
        {servos.map((servo, index) => {
          const currentState = servoStates.find(s => s.channel === servo.channel)
          const currentAngle = currentState?.current_angle ?? servo.initial_angle
          
          return (
            <div key={servo.channel} className="slider-item">
              <div className="slider-header">
                <span className="slider-name">{servo.name}</span>
                <span className="slider-value">{currentAngle}°</span>
              </div>
              
              <div className="slider-wrapper">
                <span className="slider-min">{servo.min_angle}°</span>
                <input
                  type="range"
                  min={servo.min_angle}
                  max={servo.max_angle}
                  value={currentAngle}
                  onChange={(e) => handleAngleChange(servo.channel, parseInt(e.target.value))}
                  disabled={disabled}
                  className="servo-slider"
                />
                <span className="slider-max">{servo.max_angle}°</span>
              </div>
            </div>
          )
        })}
      </div>
      
      <button
        className="reset-button"
        onClick={handleReset}
        disabled={disabled}
      >
        🔄 复位到初始角度
      </button>
    </div>
  )
}
