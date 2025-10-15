/**
 * Progress tracker component for conversation flow
 */

'use client';

import React from 'react';

interface ProgressTrackerProps {
  total: number;
  answered: number;
  complexity: number;
}

export function ProgressTracker({ total, answered, complexity }: ProgressTrackerProps) {
  const percentage = total > 0 ? (answered / total) * 100 : 0;

  const getComplexityLabel = (score: number) => {
    if (score < 4) return { label: 'Simple', color: 'text-green-600', bg: 'bg-green-100' };
    if (score < 7) return { label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { label: 'Complex', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const complexityInfo = getComplexityLabel(complexity);

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Progress</h3>
          <p className="text-xs text-gray-500">
            {answered} of {total} questions answered
          </p>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-xs font-semibold ${complexityInfo.bg} ${complexityInfo.color}`}
        >
          {complexityInfo.label} ({complexity}/10)
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-500">
          <span>0%</span>
          <span className="font-medium text-blue-600">{percentage.toFixed(0)}%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Expected Output */}
      <div className="pt-2 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Expected workflow size:</span>
          <span className="font-semibold text-gray-800">
            {complexity < 4 ? '3-5 nodes' : complexity < 7 ? '6-10 nodes' : '12-20+ nodes'}
          </span>
        </div>
      </div>
    </div>
  );
}

