import type { FileInfo } from '../api/file';

export type MessageType = "user" | "assistant" | "tool" | "step" | "attachments";

export interface Message {
  type: MessageType;
  content: BaseContent;
}

export interface BaseContent {
  timestamp: number;
}

export interface MessageContent extends BaseContent {
  content: string;
  reflection?: string; // Reflexion/self-reflection content
  thinking?: string;   // Agent thinking process
  state?: 'IDLE' | 'PLANNING' | 'EXECUTING' | 'REFLECTING' | 'WAITING' | 'COMPLETED' | 'ERROR';
}

export interface ToolContent extends BaseContent {
  tool_call_id: string;
  name: string;
  function: string;
  args: any;
  content?: any;
  status: "calling" | "called";
}

export interface StepContent extends BaseContent {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  tools: ToolContent[];
}

export interface AttachmentsContent extends BaseContent {
  role: "user" | "assistant";
  attachments: FileInfo[];
}