import { Component, OnInit, inject } from '@angular/core';
import { DocumentsService } from '../../services/documents.service';

/** Displays uploaded documents and their ingestion status. */
@Component({
  selector: 'app-documents-page',
  standalone: true,
  templateUrl: './documents-page.html',
  styleUrl: './documents-page.css',
})
export class DocumentsPage implements OnInit {
  readonly store = inject(DocumentsService);

  /**
   * Loads document status when the page opens.
   * @returns Nothing.
   */
  ngOnInit(): void {
    void this.store.refresh();
  }

  /**
   * Uploads the file selected by the user.
   * @param event The file input change event.
   * @returns Nothing.
   */
  upload(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) void this.store.upload(file);
    input.value = '';
  }
}
