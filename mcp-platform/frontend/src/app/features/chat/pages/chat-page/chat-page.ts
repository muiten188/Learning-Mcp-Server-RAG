import { Component, inject } from '@angular/core';
import { ChatStore } from '../../state/chat.store';
import { ChatInput } from '../../components/chat-input/chat-input';
import { ChatMessageList } from '../../components/chat-message-list/chat-message-list';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [ChatInput, ChatMessageList],
  templateUrl: './chat-page.html',
  styleUrl: './chat-page.css',
})
export class ChatPage {
  readonly store = inject(ChatStore);
}
