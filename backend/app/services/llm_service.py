"""
LLM service for generating n8n workflows using GPT-4.
Enhanced with RAG, node catalog, and pattern library.
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from openai import OpenAI
from ..config import get_settings
from ..models.workflow import WorkflowJSON
from .rag_service import RAGService
from .node_catalog import get_node_catalog
from .pattern_library import get_pattern_library
from .workflow_generator import get_workflow_generator
from .conversation_manager import ConversationState

# Try to import enhanced RAG workflow generator
try:
    from .rag_workflow_generator import get_rag_workflow_generator
    ENHANCED_GENERATOR_AVAILABLE = True
except ImportError:
    ENHANCED_GENERATOR_AVAILABLE = False
    print("Warning: Enhanced RAG generator not available")

class LLMService:
    """Handles LLM interaction for workflow generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.rag_service = RAGService()
        self.node_catalog = get_node_catalog()
        self.pattern_library = get_pattern_library()
        self.workflow_generator = get_workflow_generator()
        
        # Initialize enhanced RAG generator if available
        self.enhanced_generator = None
        if ENHANCED_GENERATOR_AVAILABLE:
            try:
                self.enhanced_generator = get_rag_workflow_generator()
                print("✓ Enhanced RAG workflow generator initialized")
            except Exception as e:
                print(f"Warning: Could not initialize enhanced generator: {e}")
        
        self.system_prompt = """You are an expert n8n workflow architect. Your task is to generate production-ready, complex n8n workflows based on user requests.

CRITICAL RULES:
1. ALWAYS return a valid JSON object with exactly two keys: "workflowJSON" and "explanation"
2. The "workflowJSON" key must contain a complete, valid n8n workflow
3. The "explanation" key must contain a clear description of what the workflow does
4. Generate realistic UUIDs for all node IDs
5. Position nodes logically (left to right, 220px horizontal spacing)
6. Use proper node types (n8n-nodes-base.{nodeType})
7. Ensure all connections reference valid node names
8. Include proper typeVersion for each node (usually 1 or latest)
9. EVERY NODE MUST HAVE A "parameters" FIELD: Even if empty, include "parameters": {}
10. CREDENTIALS MUST BE OBJECTS: When a node requires credentials, use this format:
   "credentials": {
     "credentialType": {
       "id": "placeholder_credential_id",
       "name": "Credential Name (to be configured)"
     }
   }
   NEVER use a string for credentials!

WORKFLOW COMPLEXITY REQUIREMENTS:
- Simple requests (e.g., "send email daily"): 3-5 nodes
- Medium complexity (e.g., "process leads and send to CRM"): 6-10 nodes
- Complex requests (e.g., "lead management system"): 10-20+ nodes
- ALWAYS include error handling for production workflows (complexity > 5)
- ALWAYS include data validation for external inputs
- Use conditional logic (IF, Switch) when appropriate
- Add logging nodes for audit trails on complex workflows

PRODUCTION WORKFLOW COMPONENTS:
1. Trigger: Choose appropriate trigger (webhook, schedule, email, etc.)
2. Authentication: Add API key validation for webhooks
3. Validation: Validate incoming data format and required fields
4. Duplicate Check: Check if record already exists (when relevant)
5. Data Processing: Transform, enrich, score data as needed
6. Conditional Logic: Route based on conditions (priority, type, etc.)
7. Main Actions: Execute primary workflow actions
8. Error Handling: Add Error Trigger workflow for failures
9. Logging: Log important events to database
10. Notifications: Send success/failure notifications

RESPONSE FORMAT:
{
  "workflowJSON": {
    "name": "Workflow Name",
    "nodes": [
      {
        "id": "uuid-here",
        "name": "Node Name",
        "type": "n8n-nodes-base.nodeType",
        "typeVersion": 1,
        "position": [240, 300],
        "parameters": {},
        "credentials": {
          "gmail": {
            "id": "1",
            "name": "Gmail account"
          }
        }
      }
    ],
    "connections": {},
    "active": false,
    "settings": {},
    "meta": {
      "generatedBy": "n8n-flow-generator",
      "version": "1.0"
    }
  },
  "explanation": "This workflow does X, Y, and Z. It starts with... and then..."
}

CREDENTIAL EXAMPLES:
- Gmail: {"gmail": {"id": "1", "name": "Gmail account"}}
- Slack: {"slackApi": {"id": "2", "name": "Slack API"}}
- HTTP: {"httpBasicAuth": {"id": "3", "name": "HTTP Basic Auth"}}
- Google Sheets: {"googleSheetsOAuth2Api": {"id": "4", "name": "Google Sheets"}}

Use the provided documentation to ensure accuracy and follow n8n best practices."""
    
    def generate_workflow(
        self,
        user_request: str,
        previous_workflow: Optional[WorkflowJSON] = None,
        conversation_context: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
        use_enhanced_generation: bool = True,
        existing_workflow: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate n8n workflow from user request.
        
        Args:
            user_request: User's description of desired workflow
            previous_workflow: Optional previous workflow for modifications
            conversation_context: Optional conversation history
            requirements: Optional requirements from conversation
            use_enhanced_generation: Use enhanced workflow generator if True
        
        Returns:
            Dict with workflowJSON and explanation
        """
        # Try enhanced RAG generator first if available
        if use_enhanced_generation and self.enhanced_generator:
            try:
                print("Using Enhanced RAG Workflow Generator...")
                
                # Build requirements from user request if not provided
                if not requirements:
                    requirements = self._parse_requirements_from_request(user_request)
                
                # Generate with enhanced generator
                result = self.enhanced_generator.generate(requirements)
                
                # Format result
                if isinstance(result, dict) and 'nodes' in result:
                    # Direct workflow JSON
                    return {
                        "workflowJSON": result,
                        "explanation": self._create_workflow_explanation(result, requirements, user_request)
                    }
                else:
                    # Already formatted result
                    return result
                    
            except Exception as e:
                print(f"Enhanced generator failed: {e}")
                print("Falling back to LLM-based generation...")
        
        # If we have requirements and enhanced generation is enabled, use the new generator
        if use_enhanced_generation and requirements and requirements.get("trigger"):
            return self._generate_with_requirements(user_request, requirements)
        
        # Otherwise, use LLM-based generation with enhanced context
        # Use existing_workflow if provided, otherwise use previous_workflow
        workflow_to_use = existing_workflow or (previous_workflow.model_dump() if previous_workflow else None)
        return self._generate_with_llm(
            user_request,
            workflow_to_use,
            conversation_context
        )
    
    def _generate_with_requirements(
        self,
        user_request: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate workflow using the enhanced workflow generator.
        
        Args:
            user_request: User's request
            requirements: Gathered requirements
            
        Returns:
            Dict with workflowJSON and explanation
        """
        # Generate workflow using the programmatic generator
        workflow_json = self.workflow_generator.generate(requirements)
        
        # Create explanation
        explanation = self._create_workflow_explanation(workflow_json, requirements, user_request)
        
        return {
            "workflowJSON": workflow_json,
            "explanation": explanation
        }
    
    def _generate_with_llm(
        self,
        user_request: str,
        previous_workflow: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate workflow using LLM with enhanced context.
        
        Args:
            user_request: User's request
            previous_workflow: Optional previous workflow
            conversation_context: Optional conversation history
            
        Returns:
            Dict with workflowJSON and explanation
        """
        # Get relevant context from RAG
        rag_context = self.rag_service.get_context_for_generation(user_request)
        
        # Find relevant nodes
        relevant_nodes = self.node_catalog.find_best_nodes_for_request(user_request)
        node_context = self._format_node_recommendations(relevant_nodes[:5])
        
        # Find relevant patterns
        relevant_patterns = self.pattern_library.find_patterns_for_request(user_request)
        pattern_context = self._format_pattern_recommendations(relevant_patterns[:3])
        
        # Build enhanced user prompt
        user_prompt = self._build_enhanced_prompt(
            user_request,
            rag_context,
            node_context,
            pattern_context,
            previous_workflow,
            conversation_context
        )
        
        # Call OpenAI
        response = self.openai_client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        # Ensure UUIDs are generated and parameters exist
        if 'workflowJSON' in result:
            result['workflowJSON'] = self._ensure_uuids(result['workflowJSON'])
            result['workflowJSON'] = self._ensure_parameters(result['workflowJSON'])
        
        return result
    
    def _create_workflow_explanation(
        self,
        workflow: Dict[str, Any],
        requirements: Dict[str, Any],
        user_request: str
    ) -> str:
        """Create a detailed explanation of the generated workflow."""
        node_count = len(workflow.get("nodes", []))
        complexity = workflow.get("meta", {}).get("complexity", 0)
        
        explanation = f"""# {workflow.get('name', 'Generated Workflow')}

This workflow was generated based on your request: "{user_request}"

## Workflow Overview
- **Total Nodes**: {node_count}
- **Complexity Score**: {complexity}/10
- **Trigger Type**: {requirements.get('trigger', 'Not specified').title()}

## Key Features"""
        
        if requirements.get("needs_validation"):
            explanation += "\n- ✅ **Data Validation**: Validates incoming data and rejects invalid entries"
        
        if requirements.get("needs_duplicate_check"):
            explanation += "\n- ✅ **Duplicate Prevention**: Checks database to avoid duplicate records"
        
        if requirements.get("needs_error_handling"):
            explanation += "\n- ✅ **Error Handling**: Comprehensive error workflow with retry logic"
        
        if requirements.get("has_branching"):
            explanation += "\n- ✅ **Conditional Routing**: Routes data based on priority/conditions"
        
        if requirements.get("needs_logging"):
            explanation += "\n- ✅ **Audit Logging**: Logs all operations to database"
        
        outputs = requirements.get("outputs", [])
        if outputs:
            output_str = ", ".join(outputs)
            explanation += f"\n- ✅ **Output Channels**: {output_str.title()}"
        
        explanation += "\n\n## Next Steps\n"
        explanation += "1. Import this workflow into your n8n instance\n"
        explanation += "2. Configure credentials for nodes that require them\n"
        explanation += "3. Update placeholder values (API keys, database names, etc.)\n"
        explanation += "4. Test the workflow with sample data\n"
        explanation += "5. Activate the workflow when ready"
        
        return explanation
    
    def _format_node_recommendations(self, nodes: List[Any]) -> str:
        """Format node recommendations for prompt."""
        if not nodes:
            return ""
        
        formatted = "\n# Recommended Nodes for this Workflow\n\n"
        for node in nodes:
            formatted += f"## {node.node_type}\n"
            formatted += f"- **Purpose**: {node.purpose}\n"
            formatted += f"- **Use Cases**: {', '.join(node.use_cases[:2])}\n"
            if node.requires_credentials:
                formatted += f"- **Requires Credentials**: {', '.join(node.credential_types)}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_pattern_recommendations(self, patterns: List[Any]) -> str:
        """Format pattern recommendations for prompt."""
        if not patterns:
            return ""
        
        formatted = "\n# Recommended Patterns for this Workflow\n\n"
        for pattern in patterns:
            formatted += f"## {pattern.name}\n"
            formatted += f"- **Description**: {pattern.description}\n"
            formatted += f"- **Complexity**: {pattern.complexity_score}/10\n"
            formatted += f"- **When to Use**: {', '.join(pattern.when_to_use[:2])}\n"
            formatted += "\n"
        
        return formatted
    
    def _build_enhanced_prompt(
        self,
        user_request: str,
        rag_context: str,
        node_context: str,
        pattern_context: str,
        previous_workflow: Optional[Dict[str, Any]],
        conversation_context: Optional[str]
    ) -> str:
        """Build enhanced user prompt with all context."""
        prompt_parts = []
        
        # Add RAG context
        prompt_parts.append(rag_context)
        
        # Add node recommendations
        if node_context:
            prompt_parts.append(node_context)
        
        # Add pattern recommendations
        if pattern_context:
            prompt_parts.append(pattern_context)
        
        # Add conversation context if exists (with higher priority)
        if conversation_context:
            prompt_parts.insert(0, f"\n# DETAILED WORKFLOW SPECIFICATIONS (HIGHEST PRIORITY)\n{conversation_context}\n\nYou MUST follow these specifications exactly. They were gathered through a detailed conversation with the user and represent their precise requirements.\n")
        
        # Add previous workflow if exists
        if previous_workflow:
            prompt_parts.append(f"\n# Current Workflow (to be modified)\n```json\n{json.dumps(previous_workflow, indent=2)}\n```\n")
        
        # Add user request
        prompt_parts.append(f"\n# User Request\n{user_request}\n")
        
        # Add enhanced instructions
        prompt_parts.append("""
# Instructions
Based on the above documentation, recommended nodes, patterns, and request, generate a complete production-ready n8n workflow.

Requirements:
- Start with an appropriate trigger node
- Include ALL necessary nodes for a production system (minimum 5 nodes for non-trivial requests)
- Add data validation if workflow receives external input
- Include error handling for complex workflows (Error Trigger workflow)
- Add conditional logic where appropriate (IF, Switch nodes)
- Include logging for audit trails
- Position nodes logically (start at x=240, increment by 220)
- Generate unique UUIDs for all node IDs
- Create proper connections between nodes
- Use descriptive node names
- Follow n8n best practices

CRITICAL VALIDATION REQUIREMENTS:
1. Every node MUST include a "parameters" field: "parameters": {}
2. If parameters is missing or null, it will cause validation errors
3. Even nodes that don't need parameters must have: "parameters": {}
4. Example node structure:
   {
     "id": "uuid-here",
     "name": "Node Name", 
     "type": "n8n-nodes-base.nodeType",
     "typeVersion": 1,
     "position": [240, 300],
     "parameters": {},
     "credentials": {}
   }

IMPORTANT: Analyze the complexity of the request:
- Simple (e.g., "send daily email"): 3-5 nodes
- Medium (e.g., "process leads"): 6-10 nodes  
- Complex (e.g., "lead management system"): 12-20+ nodes

For complex requests, include:
1. Trigger with authentication
2. Data validation flow
3. Duplicate checking (if relevant)
4. Data processing/transformation
5. Conditional routing
6. Main actions
7. Error handling workflow
8. Logging
9. Notifications

Remember: Return ONLY valid JSON with "workflowJSON" and "explanation" keys.""")
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(
        self,
        user_request: str,
        rag_context: str,
        previous_workflow: Optional[Dict[str, Any]],
        conversation_context: Optional[str]
    ) -> str:
        """Build the complete user prompt (legacy method)."""
        # Use enhanced prompt building
        return self._build_enhanced_prompt(
            user_request,
            rag_context,
            "",
            "",
            previous_workflow,
            conversation_context
        )
    
    def _ensure_uuids(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all nodes have valid UUIDs."""
        if 'nodes' in workflow:
            for node in workflow['nodes']:
                if 'id' not in node or not node['id'] or node['id'].startswith('uuid'):
                    node['id'] = str(uuid.uuid4())
        return workflow
    
    def _ensure_parameters(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all nodes have a parameters field."""
        if 'nodes' in workflow:
            for node in workflow['nodes']:
                # Ensure parameters field exists
                if 'parameters' not in node:
                    node['parameters'] = {}
                # Ensure parameters is a dict, not None
                elif node['parameters'] is None:
                    node['parameters'] = {}
        return workflow
    
    def _parse_requirements_from_request(self, user_request: str) -> Dict[str, Any]:
        """Parse requirements from user request."""
        request_lower = user_request.lower()
        
        requirements = {
            'trigger': 'webhook',
            'needs_validation': False,
            'needs_duplicate_check': False,
            'needs_error_handling': True,  # Always enable for quality
            'needs_scoring': False,
            'has_branching': False,
            'needs_logging': False,
            'needs_notification': False,
            'outputs': [],
            'integrations': [],
            'use_case': None
        }
        
        # Detect trigger type
        if 'schedule' in request_lower or 'daily' in request_lower or 'cron' in request_lower:
            requirements['trigger'] = 'schedule'
        elif 'email' in request_lower and 'receive' in request_lower:
            requirements['trigger'] = 'email'
        
        # Detect needs
        if 'validat' in request_lower:
            requirements['needs_validation'] = True
        if 'duplicate' in request_lower or 'check if exists' in request_lower:
            requirements['needs_duplicate_check'] = True
        if 'error' in request_lower or 'retry' in request_lower:
            requirements['needs_error_handling'] = True
        if 'score' in request_lower or 'priorit' in request_lower or 'rank' in request_lower:
            requirements['needs_scoring'] = True
            requirements['has_branching'] = True
        if 'log' in request_lower or 'audit' in request_lower:
            requirements['needs_logging'] = True
        if 'notif' in request_lower or 'alert' in request_lower or 'slack' in request_lower:
            requirements['needs_notification'] = True
        if 'branch' in request_lower or 'condition' in request_lower or 'if' in request_lower:
            requirements['has_branching'] = True
        
        # Detect outputs/integrations
        integrations = []
        if 'email' in request_lower or 'gmail' in request_lower:
            requirements['outputs'].append('email')
            integrations.append('email')
        if 'slack' in request_lower:
            requirements['outputs'].append('slack')
            integrations.append('slack')
        if 'database' in request_lower or 'postgres' in request_lower or 'mysql' in request_lower:
            requirements['outputs'].append('database')
            integrations.append('database')
        if 'google sheets' in request_lower or 'spreadsheet' in request_lower:
            integrations.append('google_sheets')
        if 'openai' in request_lower or 'ai' in request_lower or 'gpt' in request_lower:
            integrations.append('openai')
        if 'instagram' in request_lower:
            integrations.append('instagram')
        if 'tiktok' in request_lower or 'tik tok' in request_lower:
            integrations.append('tiktok')
        if 'twitter' in request_lower or 'x.com' in request_lower:
            integrations.append('twitter')
        if 'facebook' in request_lower:
            integrations.append('facebook')
        
        requirements['integrations'] = integrations
        
        # Detect use case
        if 'social media' in request_lower or 'post' in request_lower:
            requirements['use_case'] = 'social_media'
        elif 'video' in request_lower or 'ai avatar' in request_lower:
            requirements['use_case'] = 'ai_video'
        elif 'lead' in request_lower or 'crm' in request_lower:
            requirements['use_case'] = 'crm'
        elif 'email' in request_lower:
            requirements['use_case'] = 'email_automation'
        
        return requirements

