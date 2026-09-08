export enum AgentState {
  IDLE = 'idle',
  LISTENING = 'listening',
  PROCESSING = 'processing',
  THINKING = 'thinking',
  EXECUTING = 'executing',
  SPEAKING = 'speaking',
  ERROR = 'error',
  WAITING_CONFIRMATION = 'waiting_confirmation'
}

export enum PermissionLevel {
  SAFE = 'safe',
  SENSITIVE = 'sensitive',
  DESTRUCTIVE = 'destructive'
}

export enum ToolStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  language?: 'en' | 'hi' | 'hinglish';
}

export interface ToolCall {
  id: string;
  tool: string;
  input: any;
  status: ToolStatus;
  result?: any;
  error?: string;
  startTime: number;
  endTime?: number;
}

export interface Task {
  id: string;
  command: string;
  intent: string;
  plan: TaskStep[];
  status: ToolStatus;
  timeline: TimelineEvent[];
  result?: any;
  error?: string;
}

export interface TaskStep {
  id: string;
  description: string;
  tool: string;
  input: any;
  status: ToolStatus;
  result?: any;
}

export interface TimelineEvent {
  id: string;
  timestamp: number;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  details?: any;
}

export interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    sent: number;
    received: number;
  };
  battery?: number;
  temperature?: number;
}

export interface Tool {
  name: string;
  description: string;
  category: string;
  permission: PermissionLevel;
  schema: any;
  enabled: boolean;
}

export interface Integration {
  id: string;
  name: string;
  enabled: boolean;
  configured: boolean;
  config?: any;
}

export interface Automation {
  id: string;
  name: string;
  trigger: string;
  action: string;
  enabled: boolean;
  lastRun?: number;
  nextRun?: number;
}

export interface VoiceConfig {
  sttProvider: string;
  ttsProvider: string;
  voice: string;
  speed: number;
  volume: number;
  language: string;
  wakeWord: string;
  wakeWordEnabled: boolean;
}

export interface AIConfig {
  provider: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}
