'use client';

import { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { WorkflowJSON } from '@/types';

interface WorkflowVisualizerProps {
  workflow: WorkflowJSON;
}

export function WorkflowVisualizer({ workflow }: WorkflowVisualizerProps) {
  // Convert n8n workflow to ReactFlow format
  const convertToReactFlow = useCallback(() => {
    const nodes: Node[] = workflow.nodes.map((node) => ({
      id: node.id,
      type: 'default',
      position: { x: node.position[0], y: node.position[1] },
        data: {
          label: (
            <div className="text-xs text-black">
              <div className="font-semibold text-gray-900">{node.name}</div>
              <div className="text-gray-600">{node.type.split('.')[1]}</div>
            </div>
          ),
        },
    }));

    const edges: Edge[] = [];
    Object.entries(workflow.connections).forEach(([sourceName, outputs]) => {
      const sourceNode = workflow.nodes.find((n) => n.name === sourceName);
      if (!sourceNode) return;

      outputs.main?.forEach((outputGroup, outputIndex) => {
        outputGroup.forEach((connection) => {
          const targetNode = workflow.nodes.find((n) => n.name === connection.node);
          if (!targetNode) return;

          edges.push({
            id: `${sourceNode.id}-${targetNode.id}-${outputIndex}`,
            source: sourceNode.id,
            target: targetNode.id,
            sourceHandle: outputIndex.toString(),
            type: 'smoothstep',
          });
        });
      });
    });

    return { nodes, edges };
  }, [workflow]);

  const { nodes, edges } = convertToReactFlow();
  const [reactFlowNodes, , onNodesChange] = useNodesState(nodes);
  const [reactFlowEdges, , onEdgesChange] = useEdgesState(edges);

  return (
    <div className="w-full h-full border border-gray-300 rounded-lg bg-gray-100 shadow-sm">
      <ReactFlow
        nodes={reactFlowNodes}
        edges={reactFlowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        className="bg-gray-100"
      >
        <Background 
          color="#D1D5DB" 
          gap={20}
          size={1}
        />
        <Controls 
          className="bg-white border border-gray-300 shadow-sm"
        />
        <MiniMap 
          className="bg-white border border-gray-300 shadow-sm"
          nodeColor="#3B82F6"
        />
      </ReactFlow>
    </div>
  );
}

