import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { McpServersService } from '../../../../core/mcp/mcp-servers.service';
import { ChatStore } from '../../state/chat.store';

/** Displays chat model, MCP connection, and stream debug controls. */
@Component({
  selector: 'app-chat-header-controls',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './chat-header-controls.html',
  styleUrl: './chat-header-controls.css',
})
export class ChatHeaderControls implements OnInit {
  readonly store = inject(ChatStore);
  readonly mcp = inject(McpServersService);

  /**
   * Refreshes the MCP connection shown in the header.
   * @returns Nothing.
   */
  ngOnInit(): void {
    void this.mcp.refresh();
  }
}
