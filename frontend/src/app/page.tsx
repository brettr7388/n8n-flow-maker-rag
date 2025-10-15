'use client';

import { useEffect, useRef, useState } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { ConversationSidebar } from '@/components/conversation/ConversationSidebar';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { WorkflowViewer } from '@/components/workflow/WorkflowViewer';
import { ConversationFlow } from '@/components/conversation/ConversationFlow';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Loader2 } from 'lucide-react';
import { GenerateResponse } from '@/types';
import { editWorkflow } from '@/lib/conversationApi';

export default function Home() {
  const {
    currentConversationId,
    createConversation,
    addMessage,
    updateCurrentWorkflow,
    getCurrentConversation,
    isGenerating,
  } = useConversationStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentConversation = getCurrentConversation();
  
  // State for conversation flow
  const [showConversationFlow, setShowConversationFlow] = useState(false);
  const [initialMessage, setInitialMessage] = useState('');
  const [isMounted, setIsMounted] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [backendConversationId, setBackendConversationId] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!currentConversationId) {
      createConversation();
    }
  }, [currentConversationId, createConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentConversation?.messages]);

  const handleSendMessage = async (message: string) => {
    if (!currentConversationId) return;

    // Add user message
    addMessage(currentConversationId, {
      role: 'user',
      content: message,
    });

    // Check if we have an existing workflow - if so, treat this as an edit
    if (currentConversation?.currentWorkflow && backendConversationId) {
      setIsEditing(true);
      try {
        const response = await editWorkflow(backendConversationId, message);
        
        // Add assistant message with edited workflow
        addMessage(currentConversationId, {
          role: 'assistant',
          content: response.explanation,
          workflowSnapshot: response.workflowJSON,
        });

        // Update current workflow
        updateCurrentWorkflow(currentConversationId, response.workflowJSON);
      } catch (error) {
        // Check if it's a conversation not found error
        if (error instanceof Error && error.message.includes('not found')) {
          // Conversation was lost (server restart), start fresh with chat-based flow
          addMessage(currentConversationId, {
            role: 'assistant',
            content: 'It looks like the previous conversation was lost (server restart). Let me start fresh with your request.',
          });
          // Don't show the conversation flow - just handle it in chat
          handleChatBasedGeneration(message);
        } else {
          // Other error
          addMessage(currentConversationId, {
            role: 'assistant',
            content: `Sorry, I couldn't edit the workflow: ${error instanceof Error ? error.message : 'Unknown error'}`,
          });
        }
      } finally {
        setIsEditing(false);
      }
    } else {
      // No existing workflow - first time, show question cards
      setInitialMessage(message);
      setShowConversationFlow(true);
    }
  };

  const handleChatBasedGeneration = async (message: string) => {
    // For subsequent generations after the first workflow, use chat-based interaction
    // This would integrate with the conversation API but keep it in the chat interface
    // For now, fall back to showing the conversation flow
    setInitialMessage(message);
    setShowConversationFlow(true);
  };

  const handleWorkflowGenerated = (response: GenerateResponse, conversationId: string) => {
    if (!currentConversationId) return;

    // Store the backend conversation ID for future edits
    setBackendConversationId(conversationId);

    // Add assistant message with generated workflow
    addMessage(currentConversationId, {
      role: 'assistant',
      content: response.explanation,
      workflowSnapshot: response.workflowJSON,
    });

    // Update current workflow
    updateCurrentWorkflow(currentConversationId, response.workflowJSON);

    // Hide conversation flow
    setShowConversationFlow(false);
    setInitialMessage('');
  };

  const handleCancelConversation = () => {
    setShowConversationFlow(false);
    setInitialMessage('');
    
    if (currentConversationId) {
      addMessage(currentConversationId, {
        role: 'assistant',
        content: 'Workflow generation cancelled. Feel free to start again with a new request!',
      });
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <ConversationSidebar />
      
      <div className="flex-1 flex">
        {/* Chat Section */}
        <div className="flex-1 flex flex-col bg-white">
          <div className="border-b border-gray-200 p-4 bg-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">n8n Flow Generator</h1>
                <p className="text-sm text-gray-600">
                  {showConversationFlow 
                    ? 'Answer questions to customize your workflow' 
                    : currentConversation?.currentWorkflow
                    ? 'Describe changes you want to make to your workflow'
                    : 'Describe your workflow in natural language'
                  }
                </p>
              </div>
              <ThemeToggle />
            </div>
          </div>

          <ScrollArea className="flex-1 p-4 bg-white">
            {!showConversationFlow && (
              <>
                {isMounted && currentConversation?.messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center px-4">
                    <div className="max-w-2xl">
                      <h2 className="text-3xl font-bold text-gray-900 mb-4">
                        {currentConversation?.currentWorkflow 
                          ? "Edit Your Workflow ✏️" 
                          : "Welcome to n8n Flow Generator! 🚀"
                        }
                      </h2>
                      <p className="text-lg text-gray-600 mb-6">
                        {currentConversation?.currentWorkflow
                          ? "You can make changes to your workflow by describing what you want to modify. I'll update the workflow while keeping your original requirements."
                          : "Describe your workflow in plain English, and I'll ask you a few questions to create the perfect n8n workflow tailored to your needs."
                        }
                      </p>
                      {!currentConversation?.currentWorkflow && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left">
                          <h3 className="font-semibold text-blue-900 mb-3">Example requests:</h3>
                          <ul className="space-y-2 text-blue-800">
                            <li>• "Send daily emails to customers from my database"</li>
                            <li>• "Process new leads from webhook and add to CRM"</li>
                            <li>• "Sync data between Stripe and PostgreSQL every hour"</li>
                            <li>• "Monitor API and alert me on Slack if it goes down"</li>
                          </ul>
                        </div>
                      )}
                      {currentConversation?.currentWorkflow && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-left">
                          <h3 className="font-semibold text-green-900 mb-3">Example edit requests:</h3>
                          <ul className="space-y-2 text-green-800">
                            <li>• "Change the schedule to run every 2 hours instead"</li>
                            <li>• "Add error handling and retry logic"</li>
                            <li>• "Send notifications to Slack when the workflow completes"</li>
                            <li>• "Filter the data to only process active records"</li>
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {isMounted && currentConversation?.messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                {isMounted && (isGenerating || isEditing) && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{isEditing ? 'Editing your workflow...' : 'Analyzing your request...'}</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}

            {showConversationFlow && initialMessage && (
              <div className="max-w-3xl mx-auto py-6">
                <ConversationFlow
                  initialMessage={initialMessage}
                  onWorkflowGenerated={handleWorkflowGenerated}
                  onCancel={handleCancelConversation}
                />
              </div>
            )}
          </ScrollArea>

          {!showConversationFlow && (
            <ChatInput
              onSend={handleSendMessage}
              disabled={isGenerating || isEditing}
              placeholder={
                currentConversation?.currentWorkflow
                  ? "Describe changes you want to make to your workflow..."
                  : "Describe the workflow you want to create..."
              }
            />
          )}
        </div>

        {/* Workflow Viewer */}
        {isMounted && currentConversation?.currentWorkflow && !showConversationFlow && (
          <div className="w-1/2 border-l border-gray-200 bg-gray-100">
            <WorkflowViewer workflow={currentConversation.currentWorkflow} />
          </div>
        )}
      </div>
    </div>
  );
}
