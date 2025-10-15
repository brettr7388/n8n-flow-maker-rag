'use client';

import { useConversationStore } from '@/store/conversationStore';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';

export function ConversationSidebar() {
  const {
    conversations,
    currentConversationId,
    createConversation,
    setCurrentConversation,
    deleteConversation,
  } = useConversationStore();

  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleNewConversation = () => {
    const id = createConversation();
    setCurrentConversation(id);
  };

  const formatTime = (timestamp: string) => {
    if (!isClient) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  return (
    <div className={cn(
      "border-r border-gray-200 flex flex-col h-full bg-white transition-all duration-300",
      isCollapsed ? "w-12" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        {!isCollapsed && (
          <div className="flex items-center gap-2 mb-3">
            <Button 
              onClick={handleNewConversation} 
              className="flex-1 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm" 
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Conversation
            </Button>
          </div>
        )}
        
        {/* Collapse/Expand Button */}
        <div className="flex justify-center">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={cn(
              "w-8 h-8 rounded-lg transition-all duration-200",
              isCollapsed 
                ? "bg-blue-100 text-blue-600 hover:bg-blue-200 border border-blue-200" 
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            )}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
        
        {isCollapsed && (
          <div className="mt-3 flex justify-center">
            <Button 
              onClick={handleNewConversation} 
              className="w-8 h-8 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm rounded-lg" 
              size="icon"
              title="New conversation"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={cn(
                'group flex items-center gap-2 p-3 mb-1 rounded-lg cursor-pointer transition-all duration-150',
                'hover:bg-gray-50',
                currentConversationId === conv.id && 'bg-blue-50 border-l-4 border-blue-500 shadow-sm'
              )}
              onClick={() => setCurrentConversation(conv.id)}
              title={isCollapsed ? conv.title : undefined}
            >
              {isCollapsed ? (
                <div className="flex justify-center w-full">
                  <MessageSquare className={cn(
                    "h-4 w-4",
                    currentConversationId === conv.id ? "text-blue-600" : "text-gray-500"
                  )} />
                </div>
              ) : (
                <>
                  <MessageSquare className={cn(
                    "h-4 w-4 flex-shrink-0",
                    currentConversationId === conv.id ? "text-blue-600" : "text-gray-500"
                  )} />
                  <div className="flex-1 min-w-0">
                    <div className={cn(
                      "text-sm font-medium truncate",
                      currentConversationId === conv.id ? "text-blue-800" : "text-gray-700"
                    )}>{conv.title}</div>
                    <div className="text-xs text-gray-400">
                      {formatTime(conv.updatedAt)}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 hover:bg-red-50"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversation(conv.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Footer with user avatar */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className={cn(
          "flex items-center gap-3",
          isCollapsed && "justify-center"
        )}>
          <div className="w-8 h-8 bg-blue-900 rounded-full flex items-center justify-center text-white font-semibold text-sm">
            N
          </div>
          {!isCollapsed && (
            <div className="text-sm">
              <div className="font-semibold text-gray-900">n8n User</div>
              <div className="text-xs text-gray-500">Flow Generator</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

