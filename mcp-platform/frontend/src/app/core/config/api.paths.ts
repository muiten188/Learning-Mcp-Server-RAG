import { API_BASE_URL } from './api.config';

export const API_PATHS = {
  chat: `${API_BASE_URL}/chat`,
  conversations: `${API_BASE_URL}/conversations`,
  models: `${API_BASE_URL}/models`,
  servers: `${API_BASE_URL}/mcp-servers`,
  documents: `${API_BASE_URL}/documents`,
  embedPending: `${API_BASE_URL}/documents/embed-pending`,
} as const;
