import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Conversation, Message, WorkflowJSON } from '@/types';

interface ConversationState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isGenerating: boolean;
  
  // Actions
  createConversation: (title?: string) => string;
  addMessage: (conversationId: string, message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateCurrentWorkflow: (conversationId: string, workflow: WorkflowJSON) => void;
  setCurrentConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  setIsGenerating: (isGenerating: boolean) => void;
  getCurrentConversation: () => Conversation | null;
}

export const useConversationStore = create<ConversationState>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      isGenerating: false,

      createConversation: (title = 'New Conversation') => {
        const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const newConversation: Conversation = {
          id,
          title,
          createdAt: new Date(),
          updatedAt: new Date(),
          messages: [],
          currentWorkflow: null,
        };

        set((state) => ({
          conversations: [newConversation, ...state.conversations],
          currentConversationId: id,
        }));

        return id;
      },

      addMessage: (conversationId, message) => {
        const newMessage: Message = {
          ...message,
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
        };

        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, newMessage],
                  updatedAt: new Date(),
                  title: conv.messages.length === 0 
                    ? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
                    : conv.title,
                }
              : conv
          ),
        }));
      },

      updateCurrentWorkflow: (conversationId, workflow) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? { ...conv, currentWorkflow: workflow, updatedAt: new Date() }
              : conv
          ),
        }));
      },

      setCurrentConversation: (id) => {
        set({ currentConversationId: id });
      },

      deleteConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.filter((conv) => conv.id !== id),
          currentConversationId:
            state.currentConversationId === id ? null : state.currentConversationId,
        }));
      },

      setIsGenerating: (isGenerating) => {
        set({ isGenerating });
      },

      getCurrentConversation: () => {
        const state = get();
        return (
          state.conversations.find((conv) => conv.id === state.currentConversationId) || null
        );
      },
    }),
    {
      name: 'conversation-storage',
    }
  )
);

