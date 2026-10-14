import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideSend } from '@lucide/angular';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule, LucideSend],
  templateUrl: './chat-input.html',
  styleUrl: './chat-input.css',
})
export class ChatInput {
  @Input() busy = false;
  @Output() sendMessage = new EventEmitter<string>();
  draft = '';
  send() {
    const text = this.draft.trim();
    if (text && !this.busy) {
      this.draft = '';
      this.sendMessage.emit(text);
    }
  }
}
