/**
 * API client for conversation-based workflow generation
 */

import {
  StartConversationRequest,
  StartConversationResponse,
  AnswerQuestionRequest,
  AnswerQuestionResponse,
  GenerateFromConversationRequest,
  ConversationStatus
} from '@/types/conversation';
import { GenerateResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Start a new conversation for workflow generation
 */
export async function startConversation(
  request: StartConversationRequest
): Promise<StartConversationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start conversation');
  }

  return response.json();
}

/**
 * Answer a question in the conversation
 */
export async function answerQuestion(
  request: AnswerQuestionRequest
): Promise<AnswerQuestionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to answer question');
  }

  return response.json();
}

/**
 * Generate workflow from conversation
 */
export async function generateFromConversation(
  request: GenerateFromConversationRequest
): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate workflow');
  }

  return response.json();
}

/**
 * Get conversation status
 */
export async function getConversationStatus(
  conversationId: string
): Promise<ConversationStatus> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversation/status/${conversationId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get conversation status');
  }

  return response.json();
}

/**
 * Edit an existing workflow
 */
export async function editWorkflow(
  conversationId: string,
  editMessage: string
): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/edit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      edit_message: editMessage,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to edit workflow');
  }

  return response.json();
}

/**
 * Get conversation summary
 */
export async function getConversationSummary(
  conversationId: string
): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/api/conversation/summary/${conversationId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get conversation summary');
  }

  return response.json();
}

