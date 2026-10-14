import { Injectable } from '@angular/core';
import { API_PATHS } from '../../../core/config/api.paths';

export interface ChatEvent {
  type: string;
  data: Record<string, any>;
}

@Injectable({ providedIn: 'root' })
export class ChatStreamService {
  async *events(
    message: string,
    conversationId: string | null,
    model: string,
    signal?: AbortSignal,
  ): AsyncGenerator<ChatEvent> {
    const response = await fetch(API_PATHS.chat, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId, model }),
      signal,
    });
    if (!response.ok || !response.body) throw new Error(`Chat failed: ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    try {
      for (;;) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        let boundary: number;
        while ((boundary = buffer.indexOf('\n\n')) >= 0) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          const type = block.match(/^event: (.+)$/m)?.[1];
          const data = block.match(/^data: (.+)$/m)?.[1];
          if (type && data) yield { type, data: JSON.parse(data) };
        }
        if (done) break;
      }
    } finally {
      reader.releaseLock();
    }
  }
}
