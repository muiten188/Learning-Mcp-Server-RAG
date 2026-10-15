import { JsonPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { BrnButton } from '@spartan-ng/brain/button';
import { BrnCollapsible, BrnCollapsibleContent, BrnCollapsibleTrigger } from '@spartan-ng/brain/collapsible';
import { Message } from '../../models/message.model';
import { ChatMarkdown } from '../chat-markdown/chat-markdown';

@Component({
  selector: 'app-chat-message',
  standalone: true,
  imports: [JsonPipe, ChatMarkdown, BrnButton, BrnCollapsible, BrnCollapsibleContent, BrnCollapsibleTrigger],
  templateUrl: './chat-message.html',
  styleUrl: './chat-message.css',
})
export class ChatMessage {
  @Input({ required: true }) message!: Message;
  @Input() busy = false;
}
