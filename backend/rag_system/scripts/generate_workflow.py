#!/usr/bin/env python3
"""
Generate n8n workflows using RAG-enhanced templates
"""
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path to import rag_retriever
sys.path.insert(0, os.path.dirname(__file__))

from rag_retriever import N8NWorkflowRAG

try:
    import openai
except ImportError:
    openai = None
    print("Warning: OpenAI not installed. Install with: pip install openai")

class RAGWorkflowGenerator:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.rag = N8NWorkflowRAG()
        
        # Initialize OpenAI if available
        if openai and openai_api_key:
            openai.api_key = openai_api_key
        elif openai and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            print("Warning: No OpenAI API key provided. Will use template-based generation only.")
            self.use_openai = False
            return
        
        self.use_openai = True
    
    def generate_workflow(self, 
                         user_query: str,
                         complexity: str = "auto") -> Dict:
        """
        Generate a workflow based on user query using RAG
        
        Args:
            user_query: Natural language description of workflow
            complexity: "simple", "medium", "complex", or "auto"
        
        Returns:
            Complete n8n workflow JSON
        """
        print(f"\n{'='*70}")
        print(f"Generating workflow for: {user_query}")
        print('='*70)
        
        # Analyze query
        analysis = self.rag.analyze_query(user_query)
        
        if complexity == "auto":
            complexity = analysis['inferred_complexity']
        
        print(f"\nQuery Analysis:")
        print(f"  Complexity: {complexity}")
        print(f"  Required features: {analysis['required_features']}")
        
        # Retrieve relevant workflows
        print(f"\nRetrieving similar workflows...")
        
        if analysis['required_features']:
            similar_workflows = self.rag.retrieve_by_features(
                user_query,
                required_features=analysis['required_features'],
                n_results=3
            )
        else:
            similar_workflows = self.rag.retrieve_by_complexity(
                user_query,
                complexity=complexity,
                n_results=3
            )
        
        print(f"Found {len(similar_workflows)} similar workflows")
        
        # Build context for LLM
        context = self._build_context(similar_workflows, user_query, analysis)
        
        # Generate workflow using LLM with RAG context or template-based
        if self.use_openai and openai:
            workflow = self._generate_with_llm(context, user_query, complexity)
        else:
            workflow = self._generate_from_template(similar_workflows, user_query, complexity)
        
        return workflow
    
    def _build_context(self, 
                      workflows: List[Dict],
                      user_query: str,
                      analysis: Dict) -> str:
        """Build context for LLM from retrieved workflows"""
        context_parts = []
        
        context_parts.append("# Real n8n Workflow Examples")
        context_parts.append(f"\nUser Request: {user_query}")
        context_parts.append(f"Target Complexity: {analysis['inferred_complexity']}")
        context_parts.append(f"Required Features: {', '.join(analysis['required_features']) or 'None specified'}")
        
        context_parts.append("\n## Similar Real Workflows:\n")
        
        for idx, workflow in enumerate(workflows, 1):
            context_parts.append(f"\n### Example {idx}: {workflow.get('name', 'Untitled')}")
            context_parts.append(f"Nodes: {len(workflow.get('nodes', []))}")
            if '_rag_metadata' in workflow:
                score = workflow.get('_rag_metadata', {}).get('similarity_score', 0)
                context_parts.append(f"Similarity: {score:.2%}")
            
            # Include node types and structure
            nodes = workflow.get('nodes', [])
            node_types = [n.get('type', '') for n in nodes]
            context_parts.append(f"Node types used: {', '.join(set(node_types))}")
            
            # Include JSON structure (simplified)
            simplified = {
                "name": workflow.get('name'),
                "nodes": [
                    {
                        "name": n.get('name'),
                        "type": n.get('type'),
                        "parameters": n.get('parameters')
                    }
                    for n in nodes[:10]  # First 10 nodes only
                ],
                "connections": workflow.get('connections', {})
            }
            
            context_parts.append(f"\n```json\n{json.dumps(simplified, indent=2)}\n```\n")
        
        return "\n".join(context_parts)
    
    def _generate_with_llm(self,
                          context: str,
                          user_query: str,
                          complexity: str) -> Dict:
        """Generate workflow using LLM with RAG context"""
        
        system_prompt = """You are an expert n8n workflow generator. Generate complete, 
production-ready n8n workflows based on the user's request and the provided real workflow examples.

CRITICAL RULES:
1. Use the structure and patterns from the real workflow examples
2. Include proper error handling (Error Trigger nodes)
3. Add data validation nodes
4. Use realistic node configurations
5. Include proper connections between all nodes
6. Generate unique UUIDs for node IDs
7. Set realistic positions for visual layout
8. Include all required parameters for each node type
9. Add proper credential placeholders
10. Follow n8n best practices

Return ONLY valid JSON in n8n workflow format. No explanations."""
        
        user_prompt = f"""{context}

Based on the real workflow examples above, generate a new n8n workflow that:
1. Fulfills this request: {user_query}
2. Matches the {complexity} complexity level
3. Uses similar patterns and structures from the examples
4. Is production-ready with proper error handling

Generate the complete workflow JSON:"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            workflow_json = response.choices[0].message.content
            workflow = json.loads(workflow_json)
            
            # Validate and enhance
            workflow = self._validate_and_enhance(workflow, user_query)
            
            return workflow
            
        except Exception as e:
            print(f"Error generating with LLM: {e}")
            # Fallback to template-based generation
            return self._generate_from_template([], user_query, complexity)
    
    def _validate_and_enhance(self, workflow: Dict, user_query: str) -> Dict:
        """Validate and enhance generated workflow"""
        # Ensure all required fields
        if 'name' not in workflow:
            workflow['name'] = "Generated Workflow"
        
        if 'nodes' not in workflow:
            workflow['nodes'] = []
        
        if 'connections' not in workflow:
            workflow['connections'] = {}
        
        # Ensure all nodes have IDs
        for node in workflow['nodes']:
            if 'id' not in node:
                node['id'] = str(uuid.uuid4())
            
            if 'position' not in node:
                node['position'] = [240, 300]
        
        # Add metadata
        workflow['meta'] = {
            'generatedBy': 'rag-enhanced-n8n-generator',
            'version': '2.0',
            'userQuery': user_query,
            'generatedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        return workflow
    
    def _generate_from_template(self,
                               similar_workflows: List[Dict],
                               user_query: str,
                               complexity: str) -> Dict:
        """Fallback: Generate from template if LLM fails or unavailable"""
        print("Using template-based generation...")
        
        if similar_workflows:
            # Use the best matching workflow as a base template
            base_workflow = similar_workflows[0]
            
            # Create a new workflow based on the template
            workflow = {
                "name": f"Generated: {user_query[:50]}",
                "nodes": [],
                "connections": {}
            }
            
            # Copy nodes from template
            for node in base_workflow.get('nodes', []):
                new_node = {
                    "id": str(uuid.uuid4()),
                    "name": node.get('name'),
                    "type": node.get('type'),
                    "typeVersion": node.get('typeVersion', 1),
                    "position": node.get('position', [240, 300]),
                    "parameters": node.get('parameters', {})
                }
                workflow['nodes'].append(new_node)
            
            # Copy connections
            workflow['connections'] = base_workflow.get('connections', {})
            
            return self._validate_and_enhance(workflow, user_query)
        else:
            # Create a minimal workflow
            return {
                "name": "Generated Workflow (Minimal)",
                "nodes": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Start",
                        "type": "n8n-nodes-base.manualTrigger",
                        "typeVersion": 1,
                        "position": [240, 300],
                        "parameters": {}
                    }
                ],
                "connections": {},
                "meta": {
                    "note": "Minimal workflow - please customize",
                    "userQuery": user_query
                }
            }

def main():
    """Test workflow generation"""
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not set. Using template-based generation only.")
    
    generator = RAGWorkflowGenerator(openai_api_key=api_key)
    
    test_queries = [
        "Create a workflow that receives leads via webhook, scores them, and distributes to sales reps via email",
        "Build a simple API polling workflow that checks for new data every hour and saves to database",
        "Advanced workflow for processing customer support tickets with AI categorization and routing"
    ]
    
    output_dir = Path(__file__).parent.parent / "generated_workflows"
    output_dir.mkdir(exist_ok=True)
    
    for query in test_queries:
        workflow = generator.generate_workflow(query, complexity="auto")
        
        # Save generated workflow
        safe_name = query[:50].replace(' ', '_').replace('/', '_')
        filename = output_dir / f"generated_{safe_name}.json"
        with open(filename, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        print(f"\n✓ Generated workflow saved to: {filename}")
        print(f"  Nodes: {len(workflow.get('nodes', []))}")
        print(f"  Connections: {len(workflow.get('connections', {}))}")

if __name__ == "__main__":
    main()


