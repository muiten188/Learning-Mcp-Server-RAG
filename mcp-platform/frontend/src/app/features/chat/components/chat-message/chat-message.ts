import { JsonPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Message } from '../../models/message.model';
import { ChatMarkdown } from '../chat-markdown/chat-markdown';

@Component({
  selector: 'app-chat-message',
  standalone: true,
  imports: [JsonPipe, ChatMarkdown],
  templateUrl: './chat-message.html',
  styleUrl: './chat-message.css',
})
export class ChatMessage {
  @Input({ required: true }) message!: Message;
  @Input() busy = false;
}
