/**
 * useContinuousCommand hook
 * Sends commands continuously while button is pressed (press-and-hold pattern)
 */

import { useRef, useCallback } from 'react'

export const useContinuousCommand = (
  sendCommand: (command: object) => void,
  intervalMs: number = 100
) => {
  const intervalRef = useRef<number | null>(null)
  const isActiveRef = useRef(false)
  
  const start = useCallback((command: object) => {
    // Prevent multiple intervals
    if (isActiveRef.current) {
      return
    }
    
    isActiveRef.current = true
    
    // Send first command immediately
    sendCommand(command)
    
    // Set up interval for continuous commands
    intervalRef.current = window.setInterval(() => {
      sendCommand(command)
    }, intervalMs)
  }, [sendCommand, intervalMs])
  
  const stop = useCallback(() => {
    isActiveRef.current = false
    
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])
  
  // Cleanup on unmount
  useCallback(() => {
    return () => {
      stop()
    }
  }, [stop])
  
  return { start, stop }
}
