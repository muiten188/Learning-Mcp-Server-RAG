import { Component, Input, ViewEncapsulation } from '@angular/core';
import { MarkdownComponent } from 'ngx-markdown';

@Component({
  selector: 'app-chat-markdown',
  standalone: true,
  imports: [MarkdownComponent],
  templateUrl: './chat-markdown.html',
  styleUrl: './chat-markdown.css',
  encapsulation: ViewEncapsulation.None,
})
export class ChatMarkdown {
  @Input() content = '';
}
