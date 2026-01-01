/**
 * ServoSliders component
 * Three angle sliders for controlling mechanical arm joints
 */

import React, { useState, useEffect } from 'react'
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
  
  // Local state for slider values (while dragging)
  const [localAngles, setLocalAngles] = useState<Record<number, number>>({})
  const [isDragging, setIsDragging] = useState<Record<number, boolean>>({})
  const [initialized, setInitialized] = useState(false)
  
  // Initialize local angles from config (once)
  useEffect(() => {
    if (servos.length > 0 && !initialized) {
      const initial: Record<number, number> = {}
      servos.forEach(servo => {
        initial[servo.channel] = servo.initial_angle
      })
      setLocalAngles(initial)
      setInitialized(true)
    }
  }, [servos, initialized])
  
  // Update local angles from status when not dragging
  useEffect(() => {
    if (servoStates.length > 0 && initialized) {
      const updated: Record<number, number> = {}
      let hasChanges = false
      
      servoStates.forEach(state => {
        // Only update if not currently dragging this slider
        if (!isDragging[state.channel]) {
          const newAngle = state.current_angle
          if (localAngles[state.channel] !== newAngle) {
            updated[state.channel] = newAngle
            hasChanges = true
          }
        }
      })
      
      if (hasChanges) {
        setLocalAngles(prev => ({ ...prev, ...updated }))
      }
    }
  }, [servoStates, isDragging, initialized, localAngles])
  
  const handleAngleChange = (channel: number, angle: number) => {
    setLocalAngles(prev => ({ ...prev, [channel]: angle }))
    sendCommand({
      action: 'servo',
      channel,
      angle
    })
  }
  
  const handleMouseDown = (channel: number) => {
    setIsDragging(prev => ({ ...prev, [channel]: true }))
  }
  
  const handleMouseUp = (channel: number) => {
    setIsDragging(prev => ({ ...prev, [channel]: false }))
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
        {servos.map((servo) => {
          const displayAngle = localAngles[servo.channel] ?? servo.initial_angle
          
          return (
            <div key={servo.channel} className="slider-item">
              <div className="slider-header">
                <span className="slider-name">{servo.name}</span>
                <span className="slider-value">{displayAngle}°</span>
              </div>
              
              <div className="slider-wrapper">
                <span className="slider-min">{servo.min_angle}°</span>
                <input
                  type="range"
                  min={servo.min_angle}
                  max={servo.max_angle}
                  value={displayAngle}
                  onChange={(e) => handleAngleChange(servo.channel, parseInt(e.target.value))}
                  onMouseDown={() => handleMouseDown(servo.channel)}
                  onMouseUp={() => handleMouseUp(servo.channel)}
                  onTouchStart={() => handleMouseDown(servo.channel)}
                  onTouchEnd={() => handleMouseUp(servo.channel)}
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
