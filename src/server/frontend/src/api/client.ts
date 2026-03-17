/**
 * API Client for PStock Server
 *
 * Provides HTTP and SSE (Server-Sent Events) functionality
 * for communicating with the PStock backend.
 */

import axios from 'axios';

// Types
export interface ToolInfo {
  name: string;
  description: string;
  display_name?: string;
  parameters?: Record<string, unknown>;
}

export interface SkillInfo {
  name: string;
  description: string;
  path?: string;
}

export interface SubagentInfo {
  name: string;
  description: string;
}

export interface AgentConfig {
  max_steps: number;
  workspace_root?: string;
  instructions?: string;
  mcp_servers: Record<string, unknown>[];
  experience_enabled: boolean;
  knowledge_base?: Record<string, unknown> | null;
}

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  tools: ToolInfo[];
  skills: SkillInfo[];
  subagents: SubagentInfo[];
  config: AgentConfig;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  stream?: boolean;
}

export interface StepData {
  type: string;
  content: string;
  display_name?: string;
  raw?: string;
  data: Record<string, unknown>;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  steps: StepData[];
}

export interface ChatStreamEvent {
  type: 'step' | 'final' | 'error';
  content: string;
  step?: StepData;
  session_id?: string;
}

// API Client
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Agent API
export const agentsApi = {
  list: async (): Promise<AgentInfo[]> => {
    const response = await api.get<AgentInfo[]>('/agents');
    return response.data;
  },

  get: async (agentId: string): Promise<AgentInfo> => {
    const response = await api.get<AgentInfo>(`/agents/${agentId}`);
    return response.data;
  },

  getConfig: async (agentId: string): Promise<{
    name: string;
    description: string;
    config: AgentConfig;
    tools: ToolInfo[];
    skills: SkillInfo[];
    subagents: SubagentInfo[];
  }> => {
    const response = await api.get(`/agents/${agentId}/config`);
    return response.data;
  },
};

// Chat API
export const chatApi = {
  chat: async (agentId: string, request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>(`/agents/${agentId}/chat`, request);
    return response.data;
  },

  streamChat: (
    agentId: string,
    request: ChatRequest,
    onEvent: (event: ChatStreamEvent) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void,
  ): (() => void) => {
    const url = `${api.defaults.baseURL}/agents/${agentId}/chat/stream`;
    const eventSource = new EventSource(
      `${url}?message=${encodeURIComponent(request.message)}${request.session_id ? `&session_id=${request.session_id}` : ''}`,
    );

    eventSource.addEventListener('step', (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
      } catch (err) {
        console.error('Failed to parse step event:', err);
      }
    });

    eventSource.addEventListener('final', (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
        onComplete?.();
        eventSource.close();
      } catch (err) {
        console.error('Failed to parse final event:', err);
      }
    });

    eventSource.addEventListener('error', () => {
      onError?.(new Error('Stream error'));
      eventSource.close();
    });

    eventSource.onerror = () => {
      onError?.(new Error('Connection lost'));
      eventSource.close();
    };

    return () => eventSource.close();
  },

  listSessions: async (agentId: string): Promise<
    Array<{
      session_id: string;
      created_at: string;
      message_count: number;
    }>
  > => {
    const response = await api.get(`/agents/${agentId}/sessions`);
    return response.data;
  },

  getSession: async (agentId: string, sessionId: string): Promise<{
    session_id: string;
    created_at: string;
    messages: Array<{
      role: string;
      content: string;
      steps?: StepData[];
      timestamp: string;
    }>;
  }> => {
    const response = await api.get(`/agents/${agentId}/sessions/${sessionId}`);
    return response.data;
  },
};

export default api;
