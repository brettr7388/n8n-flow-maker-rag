/**
 * Main conversation flow component for interactive workflow generation
 */

'use client';

import React, { useState } from 'react';
import { Question, ConversationStatus } from '@/types/conversation';
import {
  startConversation,
  answerQuestion,
  generateFromConversation,
} from '@/lib/conversationApi';
import { Button } from '@/components/ui/button';
import { QuestionCard } from './QuestionCard';
import { ProgressTracker } from './ProgressTracker';
import { GenerateResponse } from '@/types';

interface ConversationFlowProps {
  initialMessage: string;
  onWorkflowGenerated: (response: GenerateResponse, conversationId: string) => void;
  onCancel: () => void;
}

export function ConversationFlow({
  initialMessage,
  onWorkflowGenerated,
  onCancel,
}: ConversationFlowProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [systemMessage, setSystemMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readyToGenerate, setReadyToGenerate] = useState(false);
  const [complexity, setComplexity] = useState(0);
  const [showAllQuestions, setShowAllQuestions] = useState(false);

  // Start conversation
  React.useEffect(() => {
    const initConversation = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await startConversation({
          message: initialMessage,
        });

        setConversationId(response.conversation_id);
        setQuestions(response.questions);
        setSystemMessage(response.message);
        setComplexity(response.analysis.complexity);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start conversation');
      } finally {
        setIsLoading(false);
      }
    };

    initConversation();
  }, [initialMessage]);

  // Handle answer submission
  const handleAnswerSubmit = async (questionId: string, answer: string) => {
    if (!conversationId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await answerQuestion({
        conversation_id: conversationId,
        question_id: questionId,
        answer: answer,
      });

      setSystemMessage(response.message);

      // Update the current question as answered in local state
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === questionId ? { ...q, answered: true, answer: answer } : q
        )
      );

      if (response.status === 'more_questions' && response.next_questions) {
        // Add follow-up questions
        setQuestions((prev) => [...prev, ...response.next_questions!]);
        setCurrentQuestionIndex((prev) => prev + 1);
      } else if (response.status === 'continue') {
        // Move to next question
        setCurrentQuestionIndex((prev) => prev + 1);
      } else if (response.status === 'ready_to_generate') {
        // All questions answered
        setReadyToGenerate(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to answer question');
    } finally {
      setIsLoading(false);
    }
  };

  // Generate workflow
  const handleGenerate = async () => {
    if (!conversationId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await generateFromConversation({
        conversation_id: conversationId,
      });

      onWorkflowGenerated(response, conversationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate workflow');
    } finally {
      setIsLoading(false);
    }
  };

  // Skip to generation (for simple workflows)
  const handleSkip = () => {
    setReadyToGenerate(true);
  };

  // Modify answers - go back to question flow
  const handleModifyAnswers = () => {
    setReadyToGenerate(false);
    setShowAllQuestions(true);
  };

  // Re-answer a specific question
  const handleReAnswerQuestion = async (questionId: string, newAnswer: string) => {
    if (!conversationId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await answerQuestion({
        conversation_id: conversationId,
        question_id: questionId,
        answer: newAnswer,
      });

      // Update local questions state
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === questionId ? { ...q, answer: newAnswer, answered: true } : q
        )
      );

      setSystemMessage('Answer updated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update answer');
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={onCancel} 
            variant="outline" 
            className="text-black border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 font-semibold bg-white"
          >
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  // Show loading screen during workflow generation
  if (isLoading && readyToGenerate) {
    return (
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
          <h3 className="text-blue-800 font-semibold text-lg mb-2">
            🚀 Generating Your Workflow...
          </h3>
          <p className="text-blue-700 mb-4">
            Creating a production-ready workflow based on your requirements.
          </p>
          <div className="space-y-2 text-sm text-blue-600">
            <p>✓ Analyzing your requirements</p>
            <p>✓ Selecting optimal nodes</p>
            <p>✓ Building workflow connections</p>
            <p>✓ Adding error handling</p>
            <p>⏳ Generating final workflow...</p>
          </div>
        </div>
      </div>
    );
  }

  if (readyToGenerate) {
    // Get summary of answered questions
    const answeredQuestions = questions.filter(q => q.answered);
    
    return (
      <div className="space-y-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-green-800 font-semibold text-lg mb-2">
            ✨ Ready to Generate Your Workflow!
          </h3>
          <p className="text-green-700 mb-4">
            I have all the information I need to create your production-ready workflow.
          </p>
          <div className="space-y-2 text-sm text-green-700">
            <p><strong>Complexity Score:</strong> {complexity}/10</p>
            <p><strong>Questions Answered:</strong> {answeredQuestions.length} / {questions.length}</p>
            <p><strong>Expected Nodes:</strong> {complexity < 4 ? '3-5' : complexity < 7 ? '6-10' : '12-20+'}</p>
          </div>
        </div>

        {/* Requirements Summary */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            📋 Workflow Specifications
          </h3>
          <div className="space-y-3">
            {answeredQuestions.map((q) => (
              <div key={q.id} className="border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                <p className="text-sm font-medium text-gray-700 mb-1">{q.question}</p>
                <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                  {q.answer}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> After generation, you'll need to configure credentials for any nodes 
            that require authentication (e.g., email services, databases, APIs).
          </p>
        </div>

        <div className="flex gap-3">
          <Button
            onClick={handleGenerate}
            disabled={isLoading}
            className="flex-1 bg-green-500 text-black hover:bg-green-600 font-bold border-2 border-black disabled:opacity-50 disabled:cursor-not-allowed"
            size="lg"
          >
            {isLoading ? '⏳ Generating...' : '🚀 Generate Workflow'}
          </Button>
          <Button
            onClick={handleModifyAnswers}
            variant="outline"
            disabled={isLoading}
            className="text-black border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 font-semibold bg-white"
          >
            Modify Answers
          </Button>
          <Button
            onClick={onCancel}
            variant="outline"
            disabled={isLoading}
            className="text-black border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 font-semibold bg-white"
          >
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  if (isLoading && !conversationId) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing your request...</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const answeredCount = questions.filter((q) => q.answered).length;

  return (
    <div className="space-y-6">
      {/* Progress Tracker */}
      <ProgressTracker
        total={questions.length}
        answered={answeredCount}
        complexity={complexity}
      />

      {/* System Message */}
      {systemMessage && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">{systemMessage}</p>
        </div>
      )}

      {/* Current Question or All Questions (for modification) */}
      {showAllQuestions ? (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800">
              Review and modify your answers below. Click "Done" when finished.
            </p>
          </div>
          {questions.filter(q => q.answered).map((question) => (
            <div key={question.id} className="bg-white border border-gray-200 rounded-lg p-4">
              <p className="font-medium text-gray-900 mb-2">{question.question}</p>
              <p className="text-sm text-gray-700 mb-3 bg-gray-50 px-3 py-2 rounded">
                Current answer: {question.answer}
              </p>
              <QuestionCard
                question={{ ...question, answered: false }}
                onAnswer={(id, answer) => handleReAnswerQuestion(id, answer)}
                isLoading={isLoading}
              />
            </div>
          ))}
          <div className="flex gap-3">
            <Button
              onClick={() => {
                setShowAllQuestions(false);
                setReadyToGenerate(true);
              }}
              className="flex-1 bg-blue-500 text-black hover:bg-blue-600 font-bold border-2 border-black"
            >
              Done - Back to Summary
            </Button>
            <Button
              onClick={onCancel}
              variant="outline"
              className="text-black border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 font-semibold bg-white"
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : currentQuestion && !currentQuestion.answered ? (
        <>
          <QuestionCard
            question={currentQuestion}
            onAnswer={handleAnswerSubmit}
            isLoading={isLoading}
          />

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={onCancel}
              variant="outline"
              disabled={isLoading}
              className="text-black border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 font-semibold bg-white"
            >
              Cancel
            </Button>

            {!currentQuestion?.required && answeredCount > 0 && (
              <Button
                onClick={handleSkip}
                variant="secondary"
                disabled={isLoading}
                className="ml-auto bg-yellow-400 text-black hover:bg-yellow-500 font-semibold border-2 border-black"
              >
                Skip & Generate
              </Button>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}

