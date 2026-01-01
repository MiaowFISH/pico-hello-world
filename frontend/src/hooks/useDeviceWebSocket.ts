/**
 * WebSocket connection hook with automatic reconnection
 * Manages WebSocket lifecycle and provides send/receive functions
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import useWebSocket, { ReadyState } from 'react-use-websocket'

export interface WebSocketMessage {
  status?: string
  action?: string
  error?: string
  message?: string
  timestamp?: number
}

interface UseDeviceWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (event: Event) => void
}

export const useDeviceWebSocket = (deviceIp: string, options: UseDeviceWebSocketOptions = {}) => {
  const wsUrl = `ws://${deviceIp}/ws`
  const [isManualClose, setIsManualClose] = useState(false)
  const heartbeatIntervalRef = useRef<number | null>(null)
  
  const {
    sendMessage,
    lastMessage,
    readyState,
    getWebSocket
  } = useWebSocket(
    wsUrl,
    {
      shouldReconnect: () => !isManualClose,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      onOpen: () => {
        console.log('WebSocket connected')
        options.onOpen?.()
        startHeartbeat()
      },
      onClose: () => {
        console.log('WebSocket disconnected')
        options.onClose?.()
        stopHeartbeat()
      },
      onError: (event) => {
        console.error('WebSocket error:', event)
        options.onError?.(event)
      }
    },
    !isManualClose // Only connect if not manually closed
  )
  
  // Start heartbeat ping every 25 seconds
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }
    
    heartbeatIntervalRef.current = window.setInterval(() => {
      if (readyState === ReadyState.OPEN) {
        sendMessage(JSON.stringify({ action: 'ping' }))
      }
    }, 25000)
  }, [readyState, sendMessage])
  
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])
  
  // Handle incoming messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data) as WebSocketMessage
        
        // Filter out pong responses from heartbeat
        if (data.status !== 'pong') {
          options.onMessage?.(data)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }, [lastMessage, options])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopHeartbeat()
    }
  }, [stopHeartbeat])
  
  // Send command helper
  const sendCommand = useCallback((command: object) => {
    if (readyState === ReadyState.OPEN) {
      sendMessage(JSON.stringify(command))
    } else {
      console.warn('WebSocket not connected, command not sent:', command)
    }
  }, [readyState, sendMessage])
  
  // Close connection
  const closeConnection = useCallback(() => {
    setIsManualClose(true)
    stopHeartbeat()
    const ws = getWebSocket()
    if (ws) {
      ws.close()
    }
  }, [getWebSocket, stopHeartbeat])
  
  // Reconnect
  const reconnect = useCallback(() => {
    setIsManualClose(false)
  }, [])
  
  return {
    sendCommand,
    readyState,
    isConnected: readyState === ReadyState.OPEN,
    isConnecting: readyState === ReadyState.CONNECTING,
    closeConnection,
    reconnect,
    connectionStatus: {
      [ReadyState.CONNECTING]: 'Connecting',
      [ReadyState.OPEN]: 'Connected',
      [ReadyState.CLOSING]: 'Closing',
      [ReadyState.CLOSED]: 'Disconnected',
      [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
    }[readyState]
  }
}
