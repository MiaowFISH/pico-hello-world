/**
 * SpeedSelector component
 * Speed preset selector (slow/medium/fast)
 */

import React from 'react'
import { useDeviceStore } from '../hooks/useDeviceStore'

export const SpeedSelector: React.FC = () => {
  const { selectedSpeed, setSelectedSpeed, config } = useDeviceStore()
  
  const speedPresets = config?.speed_presets || {
    slow: 30,
    medium: 60,
    fast: 100
  }
  
  return (
    <div className="speed-selector">
      <div className="speed-label">速度:</div>
      <div className="speed-buttons">
        <button
          className={`speed-button ${selectedSpeed === 'slow' ? 'active' : ''}`}
          onClick={() => setSelectedSpeed('slow')}
        >
          慢 ({speedPresets.slow}%)
        </button>
        <button
          className={`speed-button ${selectedSpeed === 'medium' ? 'active' : ''}`}
          onClick={() => setSelectedSpeed('medium')}
        >
          中 ({speedPresets.medium}%)
        </button>
        <button
          className={`speed-button ${selectedSpeed === 'fast' ? 'active' : ''}`}
          onClick={() => setSelectedSpeed('fast')}
        >
          快 ({speedPresets.fast}%)
        </button>
      </div>
    </div>
  )
}
