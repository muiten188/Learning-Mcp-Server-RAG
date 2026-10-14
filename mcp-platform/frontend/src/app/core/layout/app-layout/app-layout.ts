import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppHeader } from '../app-header/app-header';
import { AppSidebar } from '../app-sidebar/app-sidebar';

/** Hosts the shared header, sidebar, and routed page content. */
@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, AppSidebar, AppHeader],
  templateUrl: './app-layout.html',
  styleUrl: './app-layout.css',
})
export class AppLayout {}
