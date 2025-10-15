// Core Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workflowSnapshot?: WorkflowJSON;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
  currentWorkflow: WorkflowJSON | null;
}

// n8n Workflow Types
export interface WorkflowJSON {
  name: string;
  nodes: WorkflowNode[];
  connections: WorkflowConnections;
  active?: boolean;
  settings?: Record<string, any>;
  meta?: {
    generatedBy?: string;
    version?: string;
    createdAt?: string;
  };
}

export interface WorkflowNode {
  id: string;
  name: string;
  type: string;
  typeVersion: number;
  position: [number, number];
  parameters: Record<string, any>;
  credentials?: Record<string, CredentialReference>;
}

export interface CredentialReference {
  id: string;
  name: string;
}

export interface WorkflowConnections {
  [nodeName: string]: {
    main?: Connection[][];
  };
}

export interface Connection {
  node: string;
  type: string;
  index: number;
}

// API Types
export interface GenerateRequest {
  message: string;
  conversationId?: string;
  previousWorkflow?: WorkflowJSON;
}

export interface GenerateResponse {
  workflowJSON: WorkflowJSON;
  explanation: string;
  validation: ValidationResult;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: string[];
}

export interface ValidationError {
  type: string;
  message: string;
  nodeId?: string;
}

// Example Types
export interface ExampleWorkflow {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: 'simple' | 'moderate' | 'advanced';
  prompt: string;
}

