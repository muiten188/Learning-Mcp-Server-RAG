import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ChatStore } from '../../state/chat.store';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  templateUrl: './chat-sidebar.html',
  styleUrl: './chat-sidebar.css',
})
export class ChatSidebar {
  readonly store = inject(ChatStore);
  private readonly router = inject(Router);
  openChat(id: string) {
    void this.store.openChat(id).then(() => this.router.navigateByUrl('/'));
  }
  deleteChat(id: string, event: Event) {
    event.stopPropagation();
    void this.store.deleteChat(id);
  }
}
