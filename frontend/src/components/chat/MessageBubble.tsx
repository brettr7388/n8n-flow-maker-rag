'use client';

import { Message } from '@/types';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const formatTime = (timestamp: string) => {
    if (!isClient) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  return (
    <div
      className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 shadow-sm border-2 ${
          isUser
            ? 'bg-blue-100 text-black border-blue-600 rounded-br-md'
            : 'bg-white border border-gray-900 rounded-bl-md'
        }`}
      >
        <div className={`text-sm whitespace-pre-wrap break-words ${
          isUser ? "text-black font-semibold" : "text-black"
        }`}>
          {message.content}
        </div>
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-right text-gray-700' : 'text-left text-gray-500'
          }`}
        >
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}

