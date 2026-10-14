import { Component, OnInit, inject } from '@angular/core';
import { McpServersService } from '../../../../core/mcp/mcp-servers.service';

/** Displays MCP server connection and tool status. */
@Component({
  selector: 'app-settings-page',
  standalone: true,
  templateUrl: './settings-page.html',
  styleUrl: './settings-page.css',
})
export class SettingsPage implements OnInit {
  readonly store = inject(McpServersService);

  /**
   * Refreshes server status when the page opens.
   * @returns Nothing.
   */
  ngOnInit(): void {
    void this.store.refresh();
  }
}
