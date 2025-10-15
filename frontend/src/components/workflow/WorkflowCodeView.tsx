'use client';

import { WorkflowJSON } from '@/types';
import Editor from '@monaco-editor/react';

interface WorkflowCodeViewProps {
  workflow: WorkflowJSON;
}

export function WorkflowCodeView({ workflow }: WorkflowCodeViewProps) {
  return (
    <div className="h-full border border-gray-300 rounded-lg overflow-hidden bg-white">
      <Editor
        height="100%"
        defaultLanguage="json"
        value={JSON.stringify(workflow, null, 2)}
        theme="vs"
        options={{
          readOnly: true,
          minimap: { enabled: true },
          fontSize: 14,
          wordWrap: 'on',
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 16, bottom: 16 },
        }}
      />
    </div>
  );
}

