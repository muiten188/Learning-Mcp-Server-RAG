import { Routes } from '@angular/router';
export const chatRoutes: Routes = [
  { path: '', loadComponent: () => import('./pages/chat-page/chat-page').then((m) => m.ChatPage) },
];
