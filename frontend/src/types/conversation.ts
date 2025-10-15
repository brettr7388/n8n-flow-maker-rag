/**
 * Type definitions for conversation-based workflow generation
 */

export interface Question {
  id: string;
  type: string;
  question: string;
  options: string[];
  required: boolean;
  answered: boolean;
  answer?: string;
  answered_at?: string;
}

export interface ConversationAnalysis {
  complexity: number;
  has_trigger: boolean;
  has_data_source: boolean;
  has_action: boolean;
  mentions_database: boolean;
  mentions_email: boolean;
  mentions_webhook: boolean;
  mentions_schedule: boolean;
  mentions_validation: boolean;
  mentions_error_handling: boolean;
  question_categories: string[];
}

export interface StartConversationRequest {
  message: string;
  user_id?: string;
}

export interface StartConversationResponse {
  conversation_id: string;
  analysis: ConversationAnalysis;
  questions: Question[];
  message: string;
}

export interface AnswerQuestionRequest {
  conversation_id: string;
  question_id: string;
  answer: string;
}

export interface AnswerQuestionResponse {
  status: 'more_questions' | 'continue' | 'ready_to_generate';
  next_questions?: Question[];
  unanswered_questions?: Question[];
  requirements?: Record<string, any>;
  message: string;
}

export interface GenerateFromConversationRequest {
  conversation_id: string;
}

export interface ConversationProgress {
  total_questions: number;
  answered_questions: number;
  required_questions: number;
  answered_required: number;
  percentage: number;
}

export interface ConversationStatus {
  conversation_id: string;
  phase: 'initial' | 'analyzing' | 'questioning' | 'generating' | 'complete';
  initial_request: string;
  complexity_score: number;
  progress: ConversationProgress;
  requirements: Record<string, any>;
  ready_to_generate: boolean;
}

