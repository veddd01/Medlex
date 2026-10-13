export interface Source {
  page: number;
  source: string;
  score: number;
  excerpt: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  grounded: boolean;
  emergency: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  emergency?: boolean;
  timestamp: number;
}

export interface FeedbackPayload {
  question: string;
  answer: string;
  rating: 'up' | 'down';
  session_id: string;
}

export interface StreamEvent {
  token?: string;
  done?: boolean;
  sources?: Source[];
  emergency?: boolean;
}
