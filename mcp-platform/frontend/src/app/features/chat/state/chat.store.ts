import { Injectable, computed, inject, signal } from '@angular/core';
import { injectChat } from '@tanstack/ai-angular';
import { stream, type UIMessage } from '@tanstack/ai-client';
import { EventType, type ModelMessage, type StreamChunk } from '@tanstack/ai/client';
import { Conversation } from '../models/conversation.model';
import { Message, ToolCall } from '../models/message.model';
import { ChatApiService } from '../services/chat-api.service';
import { ChatEvent, ChatStreamService } from '../services/chat-stream.service';

interface MessageAnnotations {
  documents?: string[];
  tool_calls: ToolCall[];
}

@Injectable({ providedIn: 'root' })
export class ChatStore {
  private readonly api = inject(ChatApiService);
  private readonly streamService = inject(ChatStreamService);
  private readonly annotations = signal<Record<string, MessageAnnotations>>({});

  readonly conversations = signal<Conversation[]>([]);
  readonly models = signal<string[]>([]);
  readonly activeId = signal<string | null>(null);
  readonly error = signal('');
  readonly debug = signal(false);
  readonly events = signal<string[]>([]);
  readonly model = signal('llama3.1');

  readonly chat = injectChat({
    connection: stream((messages, _data, abortSignal) => this.connect(messages, abortSignal)),
    onError: (error) => this.error.set(error.message),
  });
  readonly busy = this.chat.isLoading;
  readonly messages = computed<Message[]>(() => {
    const annotations = this.annotations();
    return this.chat
      .messages()
      .filter((item) => item.role === 'user' || item.role === 'assistant')
      .map((item) => ({
        id: item.id,
        role: item.role,
        content: item.parts
          .filter((part) => part.type === 'text')
          .map((part) => part.content)
          .join(''),
        tool_calls: annotations[item.id]?.tool_calls ?? [],
        documents: annotations[item.id]?.documents,
      }));
  });

  async initialize() {
    await Promise.all([this.refreshConversations(), this.refreshModels()]);
  }
  async refreshConversations() {
    try {
      this.conversations.set(await this.api.conversations());
    } catch (error) {
      this.error.set(String(error));
    }
  }
  async refreshModels() {
    try {
      const data = await this.api.models();
      this.models.set(data.models);
      this.model.set(data.default);
    } catch {
      this.models.set([this.model()]);
    }
  }
  newChat() {
    this.chat.stop();
    this.chat.clear();
    this.annotations.set({});
    this.activeId.set(null);
    this.events.set([]);
    this.error.set('');
  }
  async openChat(id: string) {
    try {
      const data = await this.api.conversation(id);
      this.chat.stop();
      this.activeId.set(id);
      this.model.set(data.model);
      this.events.set([]);
      this.annotations.set(
        Object.fromEntries(
          data.messages.map((message) => [
            message.id ?? '',
            {
              tool_calls: message.tool_calls,
              documents: message.documents,
            },
          ]),
        ),
      );
      this.chat.setMessages(
        data.messages.map((message) => ({
          id: message.id ?? crypto.randomUUID(),
          role: message.role as UIMessage['role'],
          parts: [{ type: 'text' as const, content: message.content }],
        })),
      );
    } catch (error) {
      this.error.set(String(error));
    }
  }
  async deleteChat(id: string) {
    try {
      await this.api.deleteConversation(id);
      if (this.activeId() === id) this.newChat();
      await this.refreshConversations();
    } catch (error) {
      this.error.set(String(error));
    }
  }
  async send(text: string) {
    if (!text.trim() || this.busy()) return;
    this.error.set('');
    try {
      await this.chat.sendMessage(text);
      await this.refreshConversations();
    } catch (error) {
      this.error.set(String(error));
    }
  }

  private async *connect(
    messages: UIMessage[] | ModelMessage[],
    abortSignal?: AbortSignal,
  ): AsyncGenerator<StreamChunk> {
    const latest = messages.at(-1);
    const text =
      latest && 'parts' in latest
        ? latest.parts
            .filter((part) => part.type === 'text')
            .map((part) => part.content)
            .join('')
        : latest && 'content' in latest && typeof latest.content === 'string'
          ? latest.content
          : '';
    const runId = crypto.randomUUID();
    const assistantId = crypto.randomUUID();
    const threadId = this.activeId() ?? crypto.randomUUID();
    yield { type: EventType.RUN_STARTED, threadId, runId };
    yield { type: EventType.TEXT_MESSAGE_START, messageId: assistantId, role: 'assistant' };

    let completed = false;
    for await (const event of this.streamService.events(
      text,
      this.activeId(),
      this.model(),
      abortSignal,
    )) {
      this.onBackendEvent(event, assistantId);
      if (event.type === 'token') {
        yield {
          type: EventType.TEXT_MESSAGE_CONTENT,
          messageId: assistantId,
          delta: event.data['text'],
        };
      } else if (event.type === 'error') {
        throw new Error(event.data['message']);
      } else if (event.type === 'done') {
        completed = true;
      }
    }
    if (!completed) throw new Error('Chat stream ended before completion');
    yield { type: EventType.TEXT_MESSAGE_END, messageId: assistantId };
    yield { type: EventType.RUN_FINISHED, threadId, runId };
  }

  private onBackendEvent({ type, data }: ChatEvent, assistantId: string) {
    this.events.update((items) => [...items, `${type}: ${JSON.stringify(data)}`]);
    if (type === 'done') this.activeId.set(data['conversation_id']);
    if (type !== 'rag' && type !== 'tool_call' && type !== 'tool_result') return;
    this.annotations.update((items) => {
      const current = items[assistantId] ?? { tool_calls: [] };
      const next: MessageAnnotations = { ...current, tool_calls: [...current.tool_calls] };
      if (type === 'rag') next.documents = data['documents'];
      if (type === 'tool_call') next.tool_calls.push(data as ToolCall);
      if (type === 'tool_result')
        next.tool_calls = next.tool_calls.map((call) =>
          call.id === data['id']
            ? { ...call, content: data['content'], is_error: data['is_error'] }
            : call,
        );
      return { ...items, [assistantId]: next };
    });
  }
}
