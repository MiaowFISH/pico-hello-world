/**
 * Zustand state store for device status and control state
 * Centralized state management for the application
 */

import { create } from 'zustand'

export interface ServoState {
  channel: number
  name: string
  current_angle: number
  min_angle: number
  max_angle: number
}

export interface TrackState {
  left_speed: number
  right_speed: number
  enabled: boolean
}

export interface BaseRotationState {
  direction: 'cw' | 'ccw' | 'stop'
  speed: number
  sleeping: boolean
}

export interface WiFiStatus {
  connected: boolean
  ssid: string
  ip_address: string | null
  rssi: number | null
}

export interface DeviceConfig {
  servos: Array<{
    channel: number
    name: string
    min_angle: number
    max_angle: number
    initial_angle: number
  }>
  speed_presets: {
    slow: number
    medium: number
    fast: number
  }
  safety: {
    command_timeout_ms: number
  }
}

export interface DeviceStatus {
  wifi: WiFiStatus
  servos: ServoState[]
  tracks: TrackState
  base_rotation: BaseRotationState
  last_command_ms: number
  uptime_ms: number
  errors: string[]
}

interface DeviceStore {
  // Device connection
  deviceIp: string
  setDeviceIp: (ip: string) => void
  
  // Device configuration
  config: DeviceConfig | null
  setConfig: (config: DeviceConfig) => void
  
  // Device status
  status: DeviceStatus | null
  setStatus: (status: DeviceStatus) => void
  
  // Selected speed preset
  selectedSpeed: 'slow' | 'medium' | 'fast'
  setSelectedSpeed: (speed: 'slow' | 'medium' | 'fast') => void
  
  // Error messages
  errorMessage: string | null
  setErrorMessage: (message: string | null) => void
  
  // WebSocket connection state
  wsConnected: boolean
  setWsConnected: (connected: boolean) => void
}

export const useDeviceStore = create<DeviceStore>((set) => ({
  // Device connection
  deviceIp: window.location.hostname || '192.168.1.200',
  setDeviceIp: (ip) => set({ deviceIp: ip }),
  
  // Device configuration
  config: null,
  setConfig: (config) => set({ config }),
  
  // Device status
  status: null,
  setStatus: (status) => set({ status }),
  
  // Selected speed preset
  selectedSpeed: 'medium',
  setSelectedSpeed: (speed) => set({ selectedSpeed: speed }),
  
  // Error messages
  errorMessage: null,
  setErrorMessage: (message) => set({ errorMessage: message }),
  
  // WebSocket connection state
  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),
}))
