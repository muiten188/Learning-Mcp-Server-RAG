import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { LucidePlus } from '@lucide/angular';
import { ChatStore } from '../../state/chat.store';
import { ChatSidebar } from '../chat-sidebar/chat-sidebar';

/** Hosts new-chat and conversation controls in the app sidebar. */
@Component({
  selector: 'app-chat-sidebar-panel',
  standalone: true,
  imports: [LucidePlus, ChatSidebar],
  templateUrl: './chat-sidebar-panel.html',
  styleUrl: './chat-sidebar-panel.css',
})
export class ChatSidebarPanel implements OnInit {
  private readonly store = inject(ChatStore);
  private readonly router = inject(Router);

  /**
   * Loads conversation history and available models.
   * @returns Nothing.
   */
  ngOnInit(): void {
    void this.store.initialize();
  }

  /**
   * Opens a blank conversation on the chat page.
   * @returns Nothing.
   */
  newChat(): void {
    this.store.newChat();
    void this.router.navigateByUrl('/');
  }
}
