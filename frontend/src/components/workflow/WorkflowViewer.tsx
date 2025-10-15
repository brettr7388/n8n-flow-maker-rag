'use client';

import { useState } from 'react';
import { WorkflowJSON } from '@/types';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, Copy, Check } from 'lucide-react';
import { WorkflowVisualizer } from './WorkflowVisualizer';
import { WorkflowCodeView } from './WorkflowCodeView';

interface WorkflowViewerProps {
  workflow: WorkflowJSON;
}

export function WorkflowViewer({ workflow }: WorkflowViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(workflow, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(workflow, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflow.name.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold text-gray-900">{workflow.name}</h2>
        <div className="flex gap-2">
          <Button 
            onClick={handleCopy} 
            size="sm"
            className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm"
          >
            {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
            {copied ? 'Copied!' : 'Copy JSON'}
          </Button>
          <Button 
            onClick={handleDownload} 
            size="sm"
            className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </div>

      <Tabs defaultValue="visual" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-4 bg-gray-100">
          <TabsTrigger 
            value="visual"
            className="text-gray-600 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600 data-[state=inactive]:bg-transparent"
          >
            Visual
          </TabsTrigger>
          <TabsTrigger 
            value="code"
            className="text-gray-600 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm data-[state=inactive]:text-gray-600 data-[state=inactive]:bg-transparent"
          >
            JSON
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="visual" className="flex-1 mt-0 p-4 bg-gray-100">
          <WorkflowVisualizer workflow={workflow} />
        </TabsContent>
        
        <TabsContent value="code" className="flex-1 mt-0 p-4 bg-white">
          <WorkflowCodeView workflow={workflow} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

