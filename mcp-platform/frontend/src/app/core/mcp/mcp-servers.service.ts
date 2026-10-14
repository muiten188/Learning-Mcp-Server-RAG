import { Injectable, signal } from '@angular/core';
import { API_PATHS } from '../config/api.paths';
import { Server } from './server.model';

/** Shares MCP server status between the settings page and app header. */
@Injectable({ providedIn: 'root' })
export class McpServersService {
  readonly servers = signal<Server[]>([]);
  readonly error = signal('');

  /**
   * Reloads server connection status and tool names.
   * @returns A promise that resolves after the request completes.
   */
  async refresh(): Promise<void> {
    try {
      const response = await fetch(API_PATHS.servers);
      if (!response.ok) throw new Error(`MCP servers: ${response.status}`);
      this.servers.set(await response.json());
    } catch (error) {
      this.error.set(String(error));
    }
  }
}
