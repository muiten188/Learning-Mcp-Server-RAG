import { Component, output } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import {
  LucideBookOpen,
  LucideFiles,
  LucideMessageCircle,
  LucideServer,
  LucideX,
} from '@lucide/angular';
import { BrnButton } from '@spartan-ng/brain/button';
import { ChatSidebarPanel } from '../../../features/chat/components/chat-sidebar-panel/chat-sidebar-panel';

/** Displays application navigation and conversation shortcuts. */
@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    BrnButton,
    ChatSidebarPanel,
    LucideFiles,
    LucideBookOpen,
    LucideMessageCircle,
    LucideServer,
    LucideX,
  ],
  templateUrl: './app-sidebar.html',
  styleUrl: './app-sidebar.css',
})
export class AppSidebar {
  readonly navigation = output<void>();
}
