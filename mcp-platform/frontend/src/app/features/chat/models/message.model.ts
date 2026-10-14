export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  content?: string;
  is_error?: boolean;
}
export interface Message {
  id?: string;
  role: string;
  content: string;
  tool_calls: ToolCall[];
  documents?: string[];
}
