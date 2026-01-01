/**
 * BaseRotation component
 * CW/CCW buttons for base rotation control
 */

import React from 'react'
import { useContinuousCommand } from '../hooks/useContinuousCommand'

interface BaseRotationProps {
  sendCommand: (command: object) => void
  disabled?: boolean
}

export const BaseRotation: React.FC<BaseRotationProps> = ({
  sendCommand,
  disabled = false
}) => {
  const { start: startCommand, stop: stopCommand } = useContinuousCommand(sendCommand)
  
  const handlePress = (direction: 'cw' | 'ccw') => {
    if (disabled) return
    startCommand({
      action: 'base',
      direction,
      speed: 80
    })
  }
  
  const handleRelease = () => {
    if (disabled) return
    sendCommand({
      action: 'base',
      direction: 'stop',
      speed: 0
    })
    stopCommand()
  }
  
  return (
    <div className="base-rotation">
      <div className="controls-label">底盘旋转</div>
      
      <div className="rotation-buttons">
        <button
          className="rotation-button rotation-ccw"
          onMouseDown={() => handlePress('ccw')}
          onMouseUp={handleRelease}
          onMouseLeave={handleRelease}
          onTouchStart={(e) => {
            e.preventDefault()
            handlePress('ccw')
          }}
          onTouchEnd={(e) => {
            e.preventDefault()
            handleRelease()
          }}
          disabled={disabled}
        >
          <span className="rotation-icon">↶</span>
          <span className="rotation-label">逆时针</span>
        </button>
        
        <button
          className="rotation-button rotation-stop"
          onClick={() => sendCommand({ action: 'base', direction: 'stop', speed: 0 })}
          disabled={disabled}
        >
          <span className="rotation-icon">■</span>
          <span className="rotation-label">停止</span>
        </button>
        
        <button
          className="rotation-button rotation-cw"
          onMouseDown={() => handlePress('cw')}
          onMouseUp={handleRelease}
          onMouseLeave={handleRelease}
          onTouchStart={(e) => {
            e.preventDefault()
            handlePress('cw')
          }}
          onTouchEnd={(e) => {
            e.preventDefault()
            handleRelease()
          }}
          disabled={disabled}
        >
          <span className="rotation-icon">↷</span>
          <span className="rotation-label">顺时针</span>
        </button>
      </div>
      
      <div className="rotation-hint">
        按住按钮持续旋转，松开自动停止
      </div>
    </div>
  )
}
