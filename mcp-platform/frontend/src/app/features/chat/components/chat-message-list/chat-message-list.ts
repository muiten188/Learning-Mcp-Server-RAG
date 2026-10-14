import { Component, Input } from '@angular/core';
import { Message } from '../../models/message.model';
import { ChatMessage } from '../chat-message/chat-message';
import { AutoScrollDirective } from '../../directives/auto-scroll.directive';

@Component({
  selector: 'app-chat-message-list',
  standalone: true,
  imports: [ChatMessage, AutoScrollDirective],
  templateUrl: './chat-message-list.html',
  styleUrl: './chat-message-list.css',
})
export class ChatMessageList {
  @Input() messages: Message[] = [];
  @Input() busy = false;
}
