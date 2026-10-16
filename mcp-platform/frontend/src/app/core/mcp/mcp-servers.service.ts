import { computed, Injectable, signal } from '@angular/core';
import { API_PATHS } from '../config/api.paths';
import { Server } from './server.model';

/** Shares MCP server status between the settings page and app header. */
@Injectable({ providedIn: 'root' })
export class McpServersService {
  readonly servers = signal<Server[]>([]);
  readonly error = signal('');
  readonly connectedCount = computed(
    () => this.servers().filter((server) => server.status === 'connected').length,
  );
  readonly totalCount = computed(
    () => this.servers().filter((server) => server.status !== 'disabled').length,
  );

  /**
   * Reloads server connection status and tool names.
   * @returns A promise that resolves after the request completes.
   */
  async refresh(): Promise<void> {
    try {
      const response = await fetch(API_PATHS.servers);
      if (!response.ok) throw new Error(`MCP servers: ${response.status}`);
      this.servers.set(await response.json());
      this.error.set('');
    } catch (error) {
      this.error.set(String(error));
    }
  }
}
