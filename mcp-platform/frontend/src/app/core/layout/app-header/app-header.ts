import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ChatHeaderControls } from '../../../features/chat/components/chat-header-controls/chat-header-controls';

/** Displays the current page title and chat controls. */
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [ChatHeaderControls],
  templateUrl: './app-header.html',
  styleUrl: './app-header.css',
})
export class AppHeader {
  readonly router = inject(Router);
}
