import { Component, inject, output } from '@angular/core';
import { Router } from '@angular/router';
import { BrnButton } from '@spartan-ng/brain/button';
import { ChatStore } from '../../state/chat.store';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  imports: [BrnButton],
  templateUrl: './chat-sidebar.html',
  styleUrl: './chat-sidebar.css',
})
export class ChatSidebar {
  readonly conversationOpened = output<void>();
  readonly store = inject(ChatStore);
  private readonly router = inject(Router);
  openChat(id: string) {
    void this.store.openChat(id).then(() => this.router.navigateByUrl('/'));
    this.conversationOpened.emit();
  }
  deleteChat(id: string, event: Event) {
    event.stopPropagation();
    void this.store.deleteChat(id);
  }
}
