import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideSend } from '@lucide/angular';
import { BrnButton } from '@spartan-ng/brain/button';
import { BrnInput } from '@spartan-ng/brain/input';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule, LucideSend, BrnButton, BrnInput],
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

  /**
   * Sends a non-empty draft on Enter while allowing Shift+Enter for a newline.
   * @param event The textarea keyboard event.
   * @returns Nothing.
   */
  onKeydown(event: KeyboardEvent): void {
    if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
    event.preventDefault();
    this.send();
  }
}
