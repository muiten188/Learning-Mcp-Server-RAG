import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideFiles, LucideMessageCircle, LucideServer } from '@lucide/angular';
import { ChatSidebarPanel } from '../../../features/chat/components/chat-sidebar-panel/chat-sidebar-panel';

/** Displays application navigation and conversation shortcuts. */
@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    ChatSidebarPanel,
    LucideFiles,
    LucideMessageCircle,
    LucideServer,
  ],
  templateUrl: './app-sidebar.html',
  styleUrl: './app-sidebar.css',
})
export class AppSidebar {}
