export enum AgentState {
  IDLE = 'idle',
  LISTENING = 'listening',
  PROCESSING = 'processing',
  THINKING = 'thinking',
  EXECUTING = 'executing',
  SPEAKING = 'speaking',
  ERROR = 'error'
}

export type ToolStatus = 'pending' | 'running' | 'success' | 'failed';

export interface TimelineEvent {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp?: number;
  details?: any;
}

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  timeline?: any[];
  tools_used?: string[];
}

export interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  network: { sent: number; received: number };
  battery?: number;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  timestamp?: number;
  read?: boolean;
}

export interface WorkflowNode {
  id: string;
  type: string;
  data: { label: string; [key: string]: any };
  position: { x: number; y: number };
}
