/**
 * ConnectionStatus component
 * Displays WiFi and WebSocket connection status
 */

import React from 'react'
import { useDeviceStore } from '../hooks/useDeviceStore'

interface ConnectionStatusProps {
  wsConnectionStatus: string
  isWsConnected: boolean
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  wsConnectionStatus,
  isWsConnected
}) => {
  const { status, deviceIp } = useDeviceStore()
  
  const wifiConnected = status?.wifi?.connected ?? false
  const wifiSsid = status?.wifi?.ssid ?? '---'
  const wifiIp = status?.wifi?.ip_address ?? '---'
  const wifiRssi = status?.wifi?.rssi
  
  // Signal strength indicator
  const getSignalStrength = (rssi: number | null | undefined) => {
    if (!rssi) return '?'
    if (rssi >= -50) return '▂▄▆█' // Excellent
    if (rssi >= -60) return '▂▄▆' // Good
    if (rssi >= -70) return '▂▄' // Fair
    return '▂' // Weak
  }
  
  return (
    <div className="connection-status">
      <div className="status-row">
        <div className={`status-indicator ${isWsConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          <span className="status-label">WebSocket: {wsConnectionStatus}</span>
        </div>
        <div className="device-ip">{deviceIp}</div>
      </div>
      
      <div className="status-row">
        <div className={`status-indicator ${wifiConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          <span className="status-label">
            WiFi: {wifiSsid}
            {wifiRssi && (
              <span className="signal-strength" title={`${wifiRssi} dBm`}>
                {' '}{getSignalStrength(wifiRssi)}
              </span>
            )}
          </span>
        </div>
        {wifiConnected && <div className="wifi-ip">{wifiIp}</div>}
      </div>
      
      {status?.uptime_ms && (
        <div className="uptime">
          Uptime: {Math.floor(status.uptime_ms / 1000)}s
        </div>
      )}
    </div>
  )
}
