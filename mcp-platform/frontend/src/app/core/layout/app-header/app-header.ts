import { Component, inject, input, output } from '@angular/core';
import { Router } from '@angular/router';
import { LucideMenu, LucideX } from '@lucide/angular';
import { ChatHeaderControls } from '../../../features/chat/components/chat-header-controls/chat-header-controls';

/** Displays the current page title and chat controls. */
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [ChatHeaderControls, LucideMenu, LucideX],
  templateUrl: './app-header.html',
  styleUrl: './app-header.css',
})
export class AppHeader {
  readonly router = inject(Router);
  readonly menuOpen = input(false);
  readonly menuToggle = output<void>();
}
