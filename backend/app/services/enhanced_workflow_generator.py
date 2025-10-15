"""
Enhanced Workflow Generator with Multi-Stage Pipeline.
Implements comprehensive validation, refinement, and quality assurance.
Based on flowfix.txt requirements for production-ready workflows.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI

from .node_schemas import get_node_schema_validator
from .quality_validator import get_quality_validator
from .expert_templates import get_expert_template_manager
from ..config import get_settings, QUALITY_CONFIG


class EnhancedWorkflowGenerator:
    """
    Multi-stage workflow generator that produces production-ready n8n workflows.
    
    Pipeline:
    1. Initial Generation (LLM with enhanced prompt)
    2. Structure Validation
    3. Parameter Validation
    4. Credential Injection
    5. Error Handling Addition
    6. Documentation Addition
    7. Connection Validation
    8. Final Quality Check
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_client = OpenAI(api_key=self.settings.openai_api_key)
        self.node_validator = get_node_schema_validator()
        self.quality_validator = get_quality_validator()
        self.expert_manager = get_expert_template_manager()
    
    def generate(
        self,
        user_request: str,
        use_case: Optional[str] = None,
        integrations: Optional[List[str]] = None,
        complexity: str = 'standard',
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a production-ready workflow using multi-stage pipeline.
        
        Args:
            user_request: User's natural language request
            use_case: General use case category
            integrations: Required integrations
            complexity: 'simple', 'standard', or 'complex'
            context: Optional RAG context (if not provided, will use expert templates)
        
        Returns:
            Complete n8n workflow JSON with metadata
        """
        integrations = integrations or []
        
        # Determine required node count
        required_node_count = self._get_required_node_count(complexity)
        
        # Use context if provided, otherwise use expert templates
        if not context:
            context = self._build_context_from_experts(use_case, integrations, complexity)
        
        # Build comprehensive generation prompt
        prompt = self._build_generation_prompt(
            user_request=user_request,
            context=context,
            required_node_count=required_node_count,
            complexity=complexity,
            integrations=integrations
        )
        
        # Generate workflow with retries
        max_attempts = QUALITY_CONFIG.get('max_generation_attempts', 3)
        best_workflow = None
        best_score = 0
        
        for attempt in range(max_attempts):
            print(f"\n{'='*70}")
            print(f"Generation Attempt {attempt + 1}/{max_attempts}")
            print('='*70)
            
            # Stage 1: Initial generation
            raw_workflow = self._generate_workflow(prompt)
            
            if not raw_workflow:
                continue
            
            # Stage 2-7: Validate and refine
            refined_workflow = self._validate_and_refine(raw_workflow, context, complexity)
            
            # Stage 8: Quality check
            quality_result = self.quality_validator.validate(refined_workflow, complexity)
            
            print(f"\nQuality Score: {quality_result['score']}/100 ({quality_result['grade']})")
            
            # Track best workflow
            if quality_result['score'] > best_score:
                best_score = quality_result['score']
                best_workflow = refined_workflow
            
            # If quality is good enough, return
            if quality_result['valid'] and quality_result['score'] >= QUALITY_CONFIG['min_quality_score']:
                print(f"✓ Quality threshold met!")
                return {
                    'workflow': refined_workflow,
                    'quality_score': quality_result['score'],
                    'quality_details': quality_result,
                    'attempt': attempt + 1
                }
            
            # Generate feedback for next attempt
            if attempt < max_attempts - 1:
                feedback = self.quality_validator.generate_feedback(quality_result)
                print(f"\nFeedback for next attempt:")
                for fb in feedback:
                    print(f"  - {fb}")
                prompt = self._update_prompt_with_feedback(prompt, feedback)
        
        # Return best attempt even if not perfect
        print(f"\n⚠ Returning best workflow (score: {best_score}/100)")
        return {
            'workflow': best_workflow,
            'quality_score': best_score,
            'warning': 'Workflow may not meet all quality standards',
            'attempts': max_attempts
        }
    
    def _get_required_node_count(self, complexity: str) -> int:
        """Determine required node count based on complexity."""
        return QUALITY_CONFIG['min_node_count'].get(complexity, 25)
    
    def _build_context_from_experts(
        self,
        use_case: Optional[str],
        integrations: List[str],
        complexity: str
    ) -> Dict[str, Any]:
        """Build context from expert templates when RAG is not available."""
        templates = self.expert_manager.find_similar_templates(
            use_case=use_case or "workflow",
            integrations=integrations,
            top_k=3
        )
        
        expert_examples = []
        for template in templates:
            workflow = template.get('workflow', {})
            expert_examples.append({
                'name': template['name'],
                'node_count': template['node_count'],
                'complexity': template['complexity'],
                'patterns': self.expert_manager.extract_patterns(template),
                'structure': self._analyze_structure(workflow)
            })
        
        return {
            'expert_examples': expert_examples,
            'patterns': [p for t in templates for p in self.expert_manager.extract_patterns(t)],
            'node_configurations': [],
            'quality_requirements': self._get_quality_requirements(complexity)
        }
    
    def _analyze_structure(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow structure."""
        nodes = workflow.get('nodes', [])
        return {
            'total_nodes': len(nodes),
            'has_conditionals': any(n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch'] for n in nodes),
            'has_merge': any(n.get('type') == 'n8n-nodes-base.merge' for n in nodes),
            'has_error_handling': any('onError' in n or 'retryOnFail' in n for n in nodes),
            'has_ai': any('ai' in n.get('type', '').lower() or 'openai' in n.get('type', '').lower() for n in nodes)
        }
    
    def _build_generation_prompt(
        self,
        user_request: str,
        context: Dict[str, Any],
        required_node_count: int,
        complexity: str,
        integrations: List[str]
    ) -> str:
        """Build comprehensive generation prompt with all requirements."""
        
        integrations_str = ", ".join(integrations) if integrations else "appropriate services"
        
        prompt = f"""ROLE: You are an expert n8n workflow architect with 5+ years of experience building production-ready automation workflows.

CONTEXT: You are generating a workflow for n8n.io that MUST be production-ready. Users should be able to import it and use it immediately after adding their credentials.

TASK: Generate a complete n8n workflow for: {user_request}

COMPLEXITY LEVEL: {complexity}
REQUIRED NODE COUNT: {required_node_count}
REQUIRED INTEGRATIONS: {integrations_str}

CRITICAL REQUIREMENTS:

1. NODE COUNT:
   ✓ Generate EXACTLY {required_node_count} or more nodes
   ✓ Current requirement: MINIMUM {required_node_count} nodes
   
2. EVERY NODE MUST HAVE:
   ✓ Unique "id" field (UUID format)
   ✓ Descriptive "name" field
   ✓ Correct "type" field (valid n8n node type)
   ✓ "typeVersion" field (typically 1)
   ✓ "position" field with [x, y] coordinates
   ✓ "parameters" object (NEVER empty {{}})
   ✓ "credentials" object (if service node requires auth)

3. ERROR HANDLING (CRITICAL):
   ✓ Add error handling to 50%+ of nodes
   ✓ ALL API/posting/service nodes MUST have:
     - "onError": "continueRegularOutput"
     - "retryOnFail": true
     - "maxTries": 3
   ✓ This prevents cascade failures

4. CREDENTIALS CONFIGURATION:
   ✓ Every service node needs credentials:
   {{
     "credentials": {{
       "serviceTypeApi": {{
         "id": "{{{{CREDENTIAL_ID}}}}",
         "name": "Service Name account"
       }}
     }}
   }}
   
5. FLOW ORCHESTRATION:
   ✓ Include IF or Switch nodes for conditional logic
   ✓ Include Merge nodes for parallel branches
   ✓ Include Set nodes for data transformation
   ✓ Include Wait nodes for async operations (if needed)

6. DOCUMENTATION:
   ✓ Add 8-12 sticky notes (type: "n8n-nodes-base.stickyNote")
   ✓ Position sticky notes near relevant node groups
   ✓ Include clear descriptions of workflow sections

7. CONNECTIONS:
   ✓ All nodes properly connected via "connections" object
   ✓ Use format: {{"NodeName": {{"main": [[{{"node": "NextNode", "type": "main", "index": 0}}]]}}}}
   ✓ Ensure no orphaned nodes

8. PARAMETERS:
   ✓ Use n8n expression syntax: ={{{{$json.field}}}}
   ✓ No placeholder values like "YOUR_VALUE_HERE"
   ✓ Realistic default values
   ✓ Complex expressions when needed

"""
        
        # Add expert examples
        if context.get('expert_examples'):
            prompt += "\n\nEXPERT WORKFLOW EXAMPLES TO FOLLOW:\n\n"
            for i, example in enumerate(context['expert_examples'][:3], 1):
                prompt += f"{i}. {example['name']}\n"
                prompt += f"   Node Count: {example['node_count']}\n"
                if 'patterns' in example:
                    prompt += f"   Key Patterns:\n"
                    for pattern in example.get('patterns', [])[:3]:
                        prompt += f"     - {pattern}\n"
                prompt += "\n"
        
        # Add patterns
        if context.get('patterns'):
            prompt += "\nWORKFLOW PATTERNS TO USE:\n\n"
            for pattern in context['patterns'][:5]:
                prompt += f"  - {pattern}\n"
        
        # Add quality requirements
        prompt += f"\n\nQUALITY REQUIREMENTS FOR {complexity.upper()}:\n\n"
        requirements = context.get('quality_requirements', {})
        for key, value in requirements.items():
            prompt += f"  {key}: {value}\n"
        
        prompt += """

OUTPUT FORMAT:
Return ONLY valid JSON matching the n8n workflow schema.
No explanations, no markdown code blocks, just the raw JSON.

WORKFLOW JSON STRUCTURE:
{
  "name": "Descriptive Workflow Name",
  "nodes": [
    {
      "id": "uuid-here",
      "name": "Node Name",
      "type": "n8n-nodes-base.nodeType",
      "typeVersion": 1,
      "position": [x, y],
      "parameters": { ... },
      "credentials": { ... }  // if needed
    }
  ],
  "connections": { ... },
  "active": false,
  "settings": {
    "executionOrder": "v1"
  }
}

VALIDATION CHECKLIST (must pass before output):
✓ Node count >= """ + str(required_node_count) + """
✓ No empty parameters objects
✓ Credentials present on service nodes
✓ Error handling on >= 50% of nodes
✓ Sticky notes present (8-12)
✓ All nodes connected properly
✓ Valid JSON syntax

START GENERATION NOW:
"""
        
        return prompt
    
    def _generate_workflow(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call LLM to generate workflow."""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert n8n workflow architect. Generate production-ready workflows with complete configurations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            workflow_json = self._extract_json(content)
            
            return workflow_json
            
        except Exception as e:
            print(f"Error generating workflow: {e}")
            return None
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        # Try to parse directly
        try:
            return json.loads(content)
        except:
            pass
        
        # Try to extract from markdown code block
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            if end != -1:
                try:
                    return json.loads(content[start:end])
                except:
                    pass
        
        # Try to find JSON object
        if '{' in content and '}' in content:
            start = content.find('{')
            end = content.rfind('}') + 1
            try:
                return json.loads(content[start:end])
            except:
                pass
        
        print("Failed to extract JSON from response")
        return None
    
    def _validate_and_refine(
        self,
        workflow: Dict[str, Any],
        context: Dict[str, Any],
        complexity: str
    ) -> Dict[str, Any]:
        """Multi-stage validation and refinement."""
        
        # Stage 2: Structure validation
        print("  Stage 2: Validating structure...")
        workflow = self._fix_structure(workflow)
        
        # Stage 3: Parameter validation
        print("  Stage 3: Validating parameters...")
        workflow = self._fix_parameters(workflow)
        
        # Stage 4: Credential injection
        print("  Stage 4: Injecting credentials...")
        workflow = self._inject_credentials(workflow)
        
        # Stage 5: Error handling addition
        print("  Stage 5: Adding error handling...")
        workflow = self._add_error_handling(workflow)
        
        # Stage 6: Documentation addition
        print("  Stage 6: Adding documentation...")
        workflow = self._add_documentation(workflow, complexity)
        
        # Stage 7: Connection validation
        print("  Stage 7: Validating connections...")
        workflow = self._validate_connections(workflow)
        
        return workflow
    
    def _fix_structure(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure workflow has proper structure."""
        # Ensure top-level fields
        if 'name' not in workflow:
            workflow['name'] = "Generated Workflow"
        
        if 'nodes' not in workflow:
            workflow['nodes'] = []
        
        if 'connections' not in workflow:
            workflow['connections'] = {}
        
        if 'active' not in workflow:
            workflow['active'] = False
        
        if 'settings' not in workflow:
            workflow['settings'] = {"executionOrder": "v1"}
        
        # Fix each node
        for node in workflow.get('nodes', []):
            if 'id' not in node:
                node['id'] = str(uuid.uuid4())
            
            if 'position' not in node:
                node['position'] = [0, 0]
            
            if 'parameters' not in node:
                node['parameters'] = {}
            
            if 'typeVersion' not in node:
                node['typeVersion'] = 1
        
        return workflow
    
    def _fix_parameters(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix node parameters."""
        for node in workflow.get('nodes', []):
            validation = self.node_validator.validate_node(node)
            
            # Log issues
            if not validation['valid']:
                print(f"    Warning: {node.get('name', 'Unknown')} has issues:")
                for error in validation['errors']:
                    print(f"      - {error}")
        
        return workflow
    
    def _inject_credentials(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Add credential configuration to service nodes."""
        for node in workflow.get('nodes', []):
            node_type = node.get('type', '')
            
            if self.node_validator.requires_credentials(node_type):
                if 'credentials' not in node:
                    cred_type = self.node_validator.get_credential_type(node_type)
                    if cred_type:
                        service_name = self._get_service_name(node_type)
                        node['credentials'] = {
                            cred_type: {
                                "id": "{{CREDENTIAL_ID}}",
                                "name": f"{service_name} account"
                            }
                        }
        
        return workflow
    
    def _get_service_name(self, node_type: str) -> str:
        """Extract service name from node type."""
        # Remove common prefixes
        name = node_type.replace('n8n-nodes-base.', '')
        name = name.replace('@n8n/n8n-nodes-langchain.', '')
        name = name.replace('@blotato/n8n-nodes-blotato.', '')
        
        # Capitalize
        return name.replace('_', ' ').replace('-', ' ').title()
    
    def _add_error_handling(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Add error handling to critical nodes."""
        for node in workflow.get('nodes', []):
            node_type = node.get('type', '')
            
            # Skip triggers and sticky notes
            if node_type.endswith('Trigger') or node_type == 'n8n-nodes-base.stickyNote':
                continue
            
            # Add error handling to nodes that need it
            if self.node_validator.needs_error_handling(node_type):
                if 'onError' not in node:
                    node['onError'] = 'continueRegularOutput'
                if 'retryOnFail' not in node:
                    node['retryOnFail'] = True
                if 'maxTries' not in node:
                    node['maxTries'] = 3
        
        return workflow
    
    def _add_documentation(self, workflow: Dict[str, Any], complexity: str) -> Dict[str, Any]:
        """Add sticky notes for workflow documentation."""
        nodes = workflow.get('nodes', [])
        
        # Count existing sticky notes
        existing_notes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.stickyNote']
        
        # Determine how many more we need
        target_notes = QUALITY_CONFIG.get('min_sticky_notes', 5)
        if complexity == 'complex':
            target_notes = 8
        
        notes_needed = max(0, target_notes - len(existing_notes))
        
        if notes_needed > 0:
            # Identify sections to document
            sections = self._identify_workflow_sections(workflow)
            
            for i, section in enumerate(sections[:notes_needed]):
                sticky = self._create_sticky_note(section, i)
                nodes.append(sticky)
        
        return workflow
    
    def _identify_workflow_sections(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify logical sections in the workflow."""
        nodes = workflow.get('nodes', [])
        sections = []
        
        # Find trigger
        triggers = [n for n in nodes if n.get('type', '').endswith('Trigger')]
        if triggers:
            sections.append({
                'title': 'Workflow Trigger',
                'description': 'Initiates the workflow execution',
                'position': triggers[0].get('position', [0, 0])
            })
        
        # Find conditional nodes
        conditionals = [n for n in nodes if n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch']]
        if conditionals:
            sections.append({
                'title': 'Conditional Logic',
                'description': 'Routes data based on conditions',
                'position': conditionals[0].get('position', [220, 0])
            })
        
        # Find AI nodes
        ai_nodes = [n for n in nodes if 'ai' in n.get('type', '').lower() or 'openai' in n.get('type', '').lower()]
        if ai_nodes:
            sections.append({
                'title': 'AI Processing',
                'description': 'AI-powered content generation',
                'position': ai_nodes[0].get('position', [440, 0])
            })
        
        # Find merge nodes
        merges = [n for n in nodes if n.get('type') == 'n8n-nodes-base.merge']
        if merges:
            sections.append({
                'title': 'Merge Results',
                'description': 'Combines parallel execution paths',
                'position': merges[0].get('position', [660, 0])
            })
        
        # Find posting/output nodes
        output_nodes = [n for n in nodes if any(word in n.get('name', '').lower() for word in ['post', 'send', 'save', 'create'])]
        if output_nodes:
            sections.append({
                'title': 'Output Actions',
                'description': 'Final workflow outputs',
                'position': output_nodes[0].get('position', [880, 0])
            })
        
        # General sections if not enough specific ones
        if len(sections) < 3:
            sections.append({
                'title': 'Data Processing',
                'description': 'Transform and prepare data',
                'position': [440, 300]
            })
        
        return sections
    
    def _create_sticky_note(self, section: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a sticky note node."""
        position = section.get('position', [0, 200])
        # Position sticky notes slightly above and to the left of their section
        position = [position[0] - 200, position[1] - 150]
        
        return {
            "id": str(uuid.uuid4()),
            "name": f"Note {index + 1}",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": position,
            "parameters": {
                "content": f"## {section['title']}\n\n{section['description']}",
                "height": 160,
                "width": 240
            }
        }
    
    def _validate_connections(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all nodes are properly connected."""
        # This is a complex operation that would require analyzing the workflow graph
        # For now, we just ensure the connections object exists
        if 'connections' not in workflow:
            workflow['connections'] = {}
        
        return workflow
    
    def _get_quality_requirements(self, complexity: str) -> Dict[str, Any]:
        """Get quality requirements for complexity level."""
        return {
            "simple": {
                "min_nodes": 15,
                "error_handling_percentage": 0.3,
                "requires_branching": False,
                "requires_documentation": True
            },
            "standard": {
                "min_nodes": 25,
                "error_handling_percentage": 0.4,
                "requires_branching": True,
                "requires_documentation": True
            },
            "complex": {
                "min_nodes": 35,
                "error_handling_percentage": 0.5,
                "requires_branching": True,
                "requires_ai_agent": True,
                "requires_documentation": True
            }
        }.get(complexity, {})
    
    def _update_prompt_with_feedback(self, prompt: str, feedback: List[str]) -> str:
        """Add feedback to prompt for retry."""
        feedback_str = "\n".join(f"  - {fb}" for fb in feedback)
        
        updated_prompt = f"""{prompt}

PREVIOUS ATTEMPT FEEDBACK (MUST FIX):
{feedback_str}

CRITICAL: Address ALL feedback points above in this generation.
"""
        
        return updated_prompt


# Global instance
_enhanced_generator = None


def get_enhanced_workflow_generator() -> EnhancedWorkflowGenerator:
    """Get singleton instance of enhanced workflow generator."""
    global _enhanced_generator
    if _enhanced_generator is None:
        _enhanced_generator = EnhancedWorkflowGenerator()
    return _enhanced_generator


