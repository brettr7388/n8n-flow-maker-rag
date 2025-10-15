/**
 * Question card component for displaying and answering questions
 */

'use client';

import React, { useState } from 'react';
import { Question } from '@/types/conversation';
import { Button } from '@/components/ui/button';

interface QuestionCardProps {
  question: Question;
  onAnswer: (questionId: string, answer: string) => void;
  isLoading: boolean;
}

export function QuestionCard({ question, onAnswer, isLoading }: QuestionCardProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<string[]>([]);
  const [customAnswer, setCustomAnswer] = useState<string>('');

  const handleSubmit = () => {
    const answer = selectedAnswers.length > 0 
      ? (selectedAnswers.length === 1 ? selectedAnswers[0] : selectedAnswers.join(', '))
      : customAnswer;
    if (answer.trim()) {
      onAnswer(question.id, answer);
      setSelectedAnswers([]);
      setCustomAnswer('');
    }
  };

  const handleOptionClick = (option: string) => {
    setSelectedAnswers(prev => {
      if (prev.includes(option)) {
        // Remove if already selected
        return prev.filter(item => item !== option);
      } else {
        // Add to selection
        return [...prev, option];
      }
    });
  };

  const hasOptions = question.options && question.options.length > 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-4">
      {/* Question */}
      <div>
        <div className="flex items-start gap-2 mb-3">
          <span className="text-2xl">💬</span>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {question.question}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              {question.required && (
                <span className="text-xs text-red-600 font-medium">* Required</span>
              )}
              {hasOptions && (
                <span className="text-xs text-blue-600 font-medium">• You can select multiple options</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Options */}
      {hasOptions && (
        <div className="space-y-2">
          {question.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleOptionClick(option)}
              disabled={isLoading}
              className={`
                w-full text-left p-4 rounded-lg border-2 transition-all
                ${
                  selectedAnswers.includes(option)
                    ? 'border-blue-600 bg-blue-50 shadow-md'
                    : 'border-black hover:border-blue-400 hover:bg-gray-50'
                }
                ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`
                  w-5 h-5 rounded-full border-2 flex items-center justify-center
                  ${
                    selectedAnswers.includes(option)
                      ? 'border-blue-600 bg-blue-600'
                      : 'border-black'
                  }
                `}
                >
                  {selectedAnswers.includes(option) && (
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  )}
                </div>
                <span className="text-black font-medium">{option}</span>
                {selectedAnswers.includes(option) && (
                  <span className="ml-auto text-blue-600 font-semibold text-sm">
                    ✓ Selected
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Custom Answer Input */}
      {!hasOptions && (
        <div>
          <textarea
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Type your answer here..."
            disabled={isLoading}
            rows={3}
            className="w-full px-4 py-3 border-2 border-black rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-black bg-white"
          />
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end pt-2">
        <Button
          onClick={handleSubmit}
          disabled={isLoading || (selectedAnswers.length === 0 && !customAnswer.trim())}
          size="lg"
          className="bg-blue-500 text-black hover:bg-blue-600 disabled:bg-gray-300 disabled:text-gray-500 px-6 py-3 font-bold border-2 border-black"
        >
          {isLoading 
            ? 'Submitting...' 
            : selectedAnswers.length > 1 
              ? `Submit ${selectedAnswers.length} Answers →`
              : 'Submit Answer →'
          }
        </Button>
      </div>
    </div>
  );
}

