import { Routes } from '@angular/router';
import { AppLayout } from './core/layout/app-layout/app-layout';

export const appRoutes: Routes = [
  {
    path: '',
    component: AppLayout,
    children: [
      {
        path: '',
        loadChildren: () => import('./features/chat/chat.routes').then((m) => m.chatRoutes),
      },
      {
        path: 'documents',
        loadComponent: () =>
          import('./features/documents/pages/documents-page/documents-page').then(
            (m) => m.DocumentsPage,
          ),
      },
      { path: 'knowledge-base', redirectTo: 'documents', pathMatch: 'full' },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/pages/settings-page/settings-page').then(
            (m) => m.SettingsPage,
          ),
      },
      {
        path: 'jobs',
        loadComponent: () =>
          import('./features/jobs/pages/jobs-page/jobs-page').then((m) => m.JobsPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
