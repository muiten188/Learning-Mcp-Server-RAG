import { Injectable } from '@angular/core';
import { API_PATHS } from '../../../core/config/api.paths';
import { Conversation } from '../models/conversation.model';
import { Message } from '../models/message.model';

@Injectable({ providedIn: 'root' })
export class ChatApiService {
  private async getJson<T>(path: string): Promise<T> {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }
  conversations() {
    return this.getJson<Conversation[]>(API_PATHS.conversations);
  }
  conversation(id: string) {
    return this.getJson<{ messages: Message[]; model: string }>(
      `${API_PATHS.conversations}/${encodeURIComponent(id)}`,
    );
  }
  models() {
    return this.getJson<{ models: string[]; default: string }>(API_PATHS.models);
  }
  async deleteConversation(id: string) {
    const response = await fetch(`${API_PATHS.conversations}/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error(`Delete failed: ${response.status}`);
  }
}
