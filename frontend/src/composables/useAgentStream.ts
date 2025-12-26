/**
 * useAgentStream Composable
 * 
 * Real-time WebSocket connection for agent events streaming.
 * Handles all agent lifecycle events: StepStart, ToolCall, Observation, Reflection, etc.
 * 
 * Inspired by OpenHands architecture but implemented with Vue 3 Composition API.
 * 
 * Author: Senior Full-Stack Engineer
 * Date: 2025-12-26
 */

import { ref, onUnmounted, reactive, computed } from 'vue'
import { io, Socket } from 'socket.io-client'

// Event types from backend
export enum AgentEventType {
  STEP_START = 'step_start',
  TOOL_CALL = 'tool_call',
  OBSERVATION = 'observation',
  REFLECTION = 'reflection',
  PLAN = 'plan',
  MESSAGE = 'message',
  ERROR = 'error',
  DONE = 'done',
  TITLE = 'title',
  STATUS = 'status'
}

// Tool types
export enum ToolType {
  SHELL = 'shell',
  BROWSER = 'browser',
  FILE = 'file',
  WEBDEV = 'webdev',
  MCP = 'mcp',
  MESSAGE = 'message'
}

// Agent state
export enum AgentState {
  IDLE = 'idle',
  PLANNING = 'planning',
  EXECUTING = 'executing',
  REFLECTING = 'reflecting',
  WAITING = 'waiting',
  COMPLETED = 'completed',
  ERROR = 'error'
}

// Event interfaces
export interface BaseAgentEvent {
  type: AgentEventType
  timestamp: string
  session_id?: string
}

export interface StepStartEvent extends BaseAgentEvent {
  type: AgentEventType.STEP_START
  step_id: string
  step_number: number
  description?: string
}

export interface ToolCallEvent extends BaseAgentEvent {
  type: AgentEventType.TOOL_CALL
  tool: ToolType
  function_name: string
  arguments: Record<string, any>
  tool_call_id?: string
}

export interface ObservationEvent extends BaseAgentEvent {
  type: AgentEventType.OBSERVATION
  content: string
  success: boolean
  metadata?: Record<string, any>
}

export interface ReflectionEvent extends BaseAgentEvent {
  type: AgentEventType.REFLECTION
  content: string
  analysis?: string
  decision?: string
}

export interface PlanEvent extends BaseAgentEvent {
  type: AgentEventType.PLAN
  plan: {
    goal: string
    steps: Array<{
      id: string
      description: string
      status: 'pending' | 'in_progress' | 'completed' | 'failed'
    }>
  }
}

export interface MessageEvent extends BaseAgentEvent {
  type: AgentEventType.MESSAGE
  content: string
  role: 'user' | 'assistant' | 'system'
}

export interface StatusEvent extends BaseAgentEvent {
  type: AgentEventType.STATUS
  state: AgentState
  message?: string
}

export type AgentEvent = 
  | StepStartEvent 
  | ToolCallEvent 
  | ObservationEvent 
  | ReflectionEvent 
  | PlanEvent 
  | MessageEvent 
  | StatusEvent
  | BaseAgentEvent

// Connection state
export interface ConnectionState {
  connected: boolean
  connecting: boolean
  error: string | null
  reconnectAttempts: number
}

// Agent stream state
export interface AgentStreamState {
  events: AgentEvent[]
  currentState: AgentState
  currentStep: string | null
  activeTool: ToolType | null
  latestReflection: string | null
  plan: PlanEvent['plan'] | null
}

/**
 * Main composable for agent streaming
 */
export function useAgentStream() {
  // WebSocket connection
  let socket: Socket | null = null
  
  // Connection state
  const connection = reactive<ConnectionState>({
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0
  })
  
  // Agent state
  const state = reactive<AgentStreamState>({
    events: [],
    currentState: AgentState.IDLE,
    currentStep: null,
    activeTool: null,
    latestReflection: null,
    plan: null
  })
  
  // Event callbacks
  const eventCallbacks = new Map<AgentEventType, Set<(event: AgentEvent) => void>>()
  
  /**
   * Connect to WebSocket server
   */
  const connect = (sessionId: string, baseUrl?: string) => {
    if (socket?.connected) {
      console.warn('Already connected to agent stream')
      return
    }
    
    connection.connecting = true
    connection.error = null
    
    const url = baseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    
    socket = io(url, {
      path: '/ws/socket.io',
      query: { session_id: sessionId },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10
    })
    
    // Connection events
    socket.on('connect', () => {
      console.log('🟢 Agent stream connected')
      connection.connected = true
      connection.connecting = false
      connection.reconnectAttempts = 0
      connection.error = null
    })
    
    socket.on('disconnect', (reason) => {
      console.log('🔴 Agent stream disconnected:', reason)
      connection.connected = false
      connection.connecting = false
      
      if (reason === 'io server disconnect') {
        // Server disconnected, need to reconnect manually
        setTimeout(() => connect(sessionId, baseUrl), 1000)
      }
    })
    
    socket.on('connect_error', (error) => {
      console.error('❌ Agent stream connection error:', error)
      connection.connecting = false
      connection.error = error.message
      connection.reconnectAttempts++
    })
    
    socket.on('reconnect_attempt', (attempt) => {
      console.log(`🔄 Reconnecting... attempt ${attempt}`)
      connection.reconnectAttempts = attempt
    })
    
    // Agent events
    socket.on('agent_event', (event: AgentEvent) => {
      handleAgentEvent(event)
    })
    
    // Specific event handlers
    socket.on('step_start', (event: StepStartEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('tool_call', (event: ToolCallEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('observation', (event: ObservationEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('reflection', (event: ReflectionEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('plan', (event: PlanEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('status', (event: StatusEvent) => {
      handleAgentEvent(event)
    })
    
    socket.on('message', (event: MessageEvent) => {
      handleAgentEvent(event)
    })
  }
  
  /**
   * Handle incoming agent event
   */
  const handleAgentEvent = (event: AgentEvent) => {
    // Add to events array
    state.events.push(event)
    
    // Update state based on event type
    switch (event.type) {
      case AgentEventType.STEP_START:
        state.currentStep = (event as StepStartEvent).step_id
        state.currentState = AgentState.EXECUTING
        break
        
      case AgentEventType.TOOL_CALL:
        state.activeTool = (event as ToolCallEvent).tool
        break
        
      case AgentEventType.REFLECTION:
        state.latestReflection = (event as ReflectionEvent).content
        state.currentState = AgentState.REFLECTING
        break
        
      case AgentEventType.PLAN:
        state.plan = (event as PlanEvent).plan
        state.currentState = AgentState.PLANNING
        break
        
      case AgentEventType.STATUS:
        state.currentState = (event as StatusEvent).state
        break
        
      case AgentEventType.DONE:
        state.currentState = AgentState.COMPLETED
        state.currentStep = null
        state.activeTool = null
        break
        
      case AgentEventType.ERROR:
        state.currentState = AgentState.ERROR
        break
    }
    
    // Trigger callbacks
    const callbacks = eventCallbacks.get(event.type)
    if (callbacks) {
      callbacks.forEach(callback => callback(event))
    }
    
    // Trigger generic callbacks
    const genericCallbacks = eventCallbacks.get('*' as AgentEventType)
    if (genericCallbacks) {
      genericCallbacks.forEach(callback => callback(event))
    }
  }
  
  /**
   * Subscribe to specific event type
   */
  const on = (eventType: AgentEventType | '*', callback: (event: AgentEvent) => void) => {
    const type = eventType as AgentEventType
    if (!eventCallbacks.has(type)) {
      eventCallbacks.set(type, new Set())
    }
    eventCallbacks.get(type)!.add(callback)
    
    // Return unsubscribe function
    return () => {
      eventCallbacks.get(type)?.delete(callback)
    }
  }
  
  /**
   * Send message to agent
   */
  const sendMessage = (message: string, attachments?: any[]) => {
    if (!socket?.connected) {
      console.error('Cannot send message: not connected')
      return
    }
    
    socket.emit('user_message', {
      content: message,
      attachments: attachments || []
    })
  }
  
  /**
   * Intervene with shell command (for terminal intervention)
   */
  const sendShellCommand = (command: string) => {
    if (!socket?.connected) {
      console.error('Cannot send command: not connected')
      return
    }
    
    socket.emit('shell_input', { command })
  }
  
  /**
   * Request current status
   */
  const requestStatus = () => {
    if (!socket?.connected) {
      console.error('Cannot request status: not connected')
      return
    }
    
    socket.emit('request_status')
  }
  
  /**
   * Pause agent execution
   */
  const pause = () => {
    if (!socket?.connected) return
    socket.emit('pause')
  }
  
  /**
   * Resume agent execution
   */
  const resume = () => {
    if (!socket?.connected) return
    socket.emit('resume')
  }
  
  /**
   * Stop agent execution
   */
  const stop = () => {
    if (!socket?.connected) return
    socket.emit('stop')
  }
  
  /**
   * Disconnect from server
   */
  const disconnect = () => {
    if (socket) {
      socket.disconnect()
      socket = null
      connection.connected = false
      connection.connecting = false
    }
  }
  
  /**
   * Clear events
   */
  const clearEvents = () => {
    state.events = []
  }
  
  /**
   * Computed properties
   */
  const isConnected = computed(() => connection.connected)
  const isConnecting = computed(() => connection.connecting)
  const hasError = computed(() => connection.error !== null)
  const isActive = computed(() => 
    state.currentState !== AgentState.IDLE && 
    state.currentState !== AgentState.COMPLETED
  )
  
  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    // State
    connection,
    state,
    
    // Computed
    isConnected,
    isConnecting,
    hasError,
    isActive,
    
    // Methods
    connect,
    disconnect,
    on,
    sendMessage,
    sendShellCommand,
    requestStatus,
    pause,
    resume,
    stop,
    clearEvents
  }
}

// Export singleton instance for global usage if needed
let globalAgentStream: ReturnType<typeof useAgentStream> | null = null

export function useGlobalAgentStream() {
  if (!globalAgentStream) {
    globalAgentStream = useAgentStream()
  }
  return globalAgentStream
}
