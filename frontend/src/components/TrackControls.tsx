/**
 * TrackControls component
 * D-pad style direction buttons for tracked vehicle control
 */

import React from 'react'
import { useContinuousCommand } from '../hooks/useContinuousCommand'
import { useDeviceStore } from '../hooks/useDeviceStore'

interface TrackControlsProps {
  sendCommand: (command: object) => void
  disabled?: boolean
}

export const TrackControls: React.FC<TrackControlsProps> = ({
  sendCommand,
  disabled = false
}) => {
  const { selectedSpeed } = useDeviceStore()
  const { start: startCommand, stop: stopCommand } = useContinuousCommand(sendCommand)
  
  const handlePress = (command: string) => {
    if (disabled) return
    startCommand({
      action: 'track',
      command,
      speed: selectedSpeed
    })
  }
  
  const handleRelease = () => {
    if (disabled) return
    // Send stop command
    sendCommand({
      action: 'track',
      command: 'stop'
    })
    stopCommand()
  }
  
  return (
    <div className="track-controls">
      <div className="controls-label">履带控制</div>
      
      <div className="dpad">
        <div className="dpad-row">
          <div className="dpad-spacer"></div>
          <button
            className="dpad-button dpad-up"
            onMouseDown={() => handlePress('forward')}
            onMouseUp={handleRelease}
            onMouseLeave={handleRelease}
            onTouchStart={(e) => {
              e.preventDefault()
              handlePress('forward')
            }}
            onTouchEnd={(e) => {
              e.preventDefault()
              handleRelease()
            }}
            disabled={disabled}
          >
            ▲
          </button>
          <div className="dpad-spacer"></div>
        </div>
        
        <div className="dpad-row">
          <button
            className="dpad-button dpad-left"
            onMouseDown={() => handlePress('left')}
            onMouseUp={handleRelease}
            onMouseLeave={handleRelease}
            onTouchStart={(e) => {
              e.preventDefault()
              handlePress('left')
            }}
            onTouchEnd={(e) => {
              e.preventDefault()
              handleRelease()
            }}
            disabled={disabled}
          >
            ◄
          </button>
          <button
            className="dpad-button dpad-center"
            onClick={() => sendCommand({ action: 'track', command: 'stop' })}
            disabled={disabled}
          >
            ■
          </button>
          <button
            className="dpad-button dpad-right"
            onMouseDown={() => handlePress('right')}
            onMouseUp={handleRelease}
            onMouseLeave={handleRelease}
            onTouchStart={(e) => {
              e.preventDefault()
              handlePress('right')
            }}
            onTouchEnd={(e) => {
              e.preventDefault()
              handleRelease()
            }}
            disabled={disabled}
          >
            ►
          </button>
        </div>
        
        <div className="dpad-row">
          <div className="dpad-spacer"></div>
          <button
            className="dpad-button dpad-down"
            onMouseDown={() => handlePress('backward')}
            onMouseUp={handleRelease}
            onMouseLeave={handleRelease}
            onTouchStart={(e) => {
              e.preventDefault()
              handlePress('backward')
            }}
            onTouchEnd={(e) => {
              e.preventDefault()
              handleRelease()
            }}
            disabled={disabled}
          >
            ▼
          </button>
          <div className="dpad-spacer"></div>
        </div>
      </div>
    </div>
  )
}
