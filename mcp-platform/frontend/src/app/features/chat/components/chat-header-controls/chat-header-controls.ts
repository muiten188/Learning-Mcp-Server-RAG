import { Component, OnInit, inject } from '@angular/core';
import { BrnButton } from '@spartan-ng/brain/button';
import { BrnPopover, BrnPopoverContent } from '@spartan-ng/brain/popover';
import { BrnSelect, BrnSelectContent, BrnSelectItem, BrnSelectList, BrnSelectTrigger } from '@spartan-ng/brain/select';
import { McpServersService } from '../../../../core/mcp/mcp-servers.service';
import { ChatStore } from '../../state/chat.store';

/** Displays chat model, MCP connection, and stream debug controls. */
@Component({
  selector: 'app-chat-header-controls',
  standalone: true,
  imports: [BrnButton, BrnPopover, BrnPopoverContent, BrnSelect, BrnSelectContent, BrnSelectItem, BrnSelectList, BrnSelectTrigger],
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
