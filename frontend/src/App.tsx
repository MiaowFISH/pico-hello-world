/**
 * Main App component
 * Mobile-first responsive layout for robot control interface
 */

import { useEffect } from 'react'
import { useDeviceWebSocket } from './hooks/useDeviceWebSocket'
import { useDeviceStore } from './hooks/useDeviceStore'
import { ConnectionStatus } from './components/ConnectionStatus'
import { TrackControls } from './components/TrackControls'
import { SpeedSelector } from './components/SpeedSelector'

function App() {
  const {
    deviceIp,
    setConfig,
    setStatus,
    setErrorMessage,
    setWsConnected,
    errorMessage
  } = useDeviceStore()
  
  // WebSocket connection
  const {
    sendCommand,
    isConnected,
    connectionStatus
  } = useDeviceWebSocket(deviceIp, {
    onMessage: (message) => {
      if (message.status === 'error') {
        setErrorMessage(message.message || 'Unknown error')
      }
    },
    onOpen: () => {
      setWsConnected(true)
      setErrorMessage(null)
    },
    onClose: () => {
      setWsConnected(false)
    },
    onError: () => {
      setErrorMessage('WebSocket connection error')
    }
  })
  
  // Load device configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch(`http://${deviceIp}/api/config`)
        if (response.ok) {
          const config = await response.json()
          setConfig(config)
        }
      } catch (error) {
        console.error('Failed to load config:', error)
        setErrorMessage('Failed to load device configuration')
      }
    }
    
    loadConfig()
  }, [deviceIp, setConfig, setErrorMessage])
  
  // Poll device status every 2 seconds
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await fetch(`http://${deviceIp}/api/status`)
        if (response.ok) {
          const status = await response.json()
          setStatus(status)
        }
      } catch (error) {
        console.error('Failed to poll status:', error)
      }
    }
    
    // Initial poll
    pollStatus()
    
    // Set up polling interval
    const interval = setInterval(pollStatus, 2000)
    
    return () => clearInterval(interval)
  }, [deviceIp, setStatus])
  
  return (
    <div className="app">
      <header className="app-header">
        <h1>🤖 履带机械臂小车</h1>
        <ConnectionStatus
          wsConnectionStatus={connectionStatus}
          isWsConnected={isConnected}
        />
      </header>
      
      <main className="app-main">
        {errorMessage && (
          <div className="error-banner">
            ⚠️ {errorMessage}
          </div>
        )}
        
        {!isConnected ? (
          <div className="connection-warning-box">
            <p>⚠️ WebSocket not connected</p>
            <p>Waiting for connection to {deviceIp}...</p>
          </div>
        ) : (
          <>
            <SpeedSelector />
            <TrackControls
              sendCommand={sendCommand}
              disabled={!isConnected}
            />
            
            <div className="info-section">
              <h3>阶段 3: 履带控制 (User Story 1) - 已实现 ✅</h3>
              <p>下一阶段:</p>
              <ul>
                <li>Phase 4: Servo Sliders (User Story 2)</li>
                <li>Phase 5: Base Rotation (User Story 3)</li>
                <li>Phase 6: Status Panel (User Story 4)</li>
              </ul>
            </div>
          </>
        )}
      </main>
      
      <footer className="app-footer">
        <p>Pico2W Control System v2.0</p>
      </footer>
    </div>
  )
}

export default App
