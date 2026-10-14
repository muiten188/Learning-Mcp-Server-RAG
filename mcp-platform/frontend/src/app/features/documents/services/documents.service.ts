import { Injectable, signal } from '@angular/core';
import { API_PATHS } from '../../../core/config/api.paths';
import { Document } from '../models/document.model';

/** Loads and uploads documents for the knowledge base. */
@Injectable({ providedIn: 'root' })
export class DocumentsService {
  readonly documents = signal<Document[]>([]);
  readonly error = signal('');

  /**
   * Loads the current document status list.
   * @returns A promise that resolves after the request completes.
   */
  async refresh(): Promise<void> {
    try {
      const response = await fetch(API_PATHS.documents);
      if (!response.ok) throw new Error(`Documents: ${response.status}`);
      this.documents.set(await response.json());
    } catch (error) {
      this.error.set(String(error));
    }
  }

  /**
   * Uploads a document and reloads its status.
   * @param file The text or Markdown file to upload.
   * @returns A promise that resolves after the upload and refresh complete.
   */
  async upload(file: File): Promise<void> {
    try {
      const body = new FormData();
      body.append('file', file);
      const response = await fetch(API_PATHS.documents, { method: 'POST', body });
      if (!response.ok) throw new Error(await response.text());
      await this.refresh();
    } catch (error) {
      this.error.set(String(error));
    }
  }
}
