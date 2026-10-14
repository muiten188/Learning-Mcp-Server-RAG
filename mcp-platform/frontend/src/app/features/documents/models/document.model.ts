/** A document uploaded for knowledge-base retrieval. */
export interface Document {
  id: string;
  filename: string;
  status: string;
  error?: string;
}
