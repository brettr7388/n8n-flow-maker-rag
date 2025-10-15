"""
RAG-Enhanced Workflow Generator Service.
Integrates the RAG system with the enhanced workflow generator.
Now uses multi-stage pipeline for production-ready workflows.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add rag_system scripts to path
rag_scripts_path = Path(__file__).parent.parent.parent / "rag_system" / "scripts"
sys.path.insert(0, str(rag_scripts_path))

# Try to import enhanced RAG retriever
try:
    from enhanced_rag_retriever import EnhancedRAGRetriever
    RAG_AVAILABLE = True
    print("✓ Enhanced RAG retriever available")
except ImportError:
    try:
        from rag_retriever import N8NWorkflowRAG as EnhancedRAGRetriever
        RAG_AVAILABLE = True
        print("⚠ Using basic RAG retriever")
    except ImportError:
        RAG_AVAILABLE = False
        print("Warning: RAG system not available. Using fallback generator.")

from .workflow_generator import WorkflowGenerator
from .conversation_manager import ConversationState

# Import enhanced generator if available
try:
    from .enhanced_workflow_generator import get_enhanced_workflow_generator
    ENHANCED_GENERATOR_AVAILABLE = True
    print("✓ Enhanced workflow generator available")
except ImportError:
    ENHANCED_GENERATOR_AVAILABLE = False
    print("⚠ Enhanced generator not available, using basic version")


class RAGEnhancedWorkflowGenerator:
    """
    Enhanced workflow generator that uses RAG to retrieve real n8n workflow 
    templates and generate more sophisticated, production-ready workflows.
    """
    
    def __init__(self):
        self.fallback_generator = WorkflowGenerator()
        self.rag = None
        self.enhanced_generator = None
        
        # Initialize enhanced generator if available
        if ENHANCED_GENERATOR_AVAILABLE:
            try:
                self.enhanced_generator = get_enhanced_workflow_generator()
                print("✓ Enhanced workflow generator initialized")
            except Exception as e:
                print(f"Warning: Could not initialize enhanced generator: {e}")
        
        # Initialize RAG system
        if RAG_AVAILABLE:
            try:
                self.rag = EnhancedRAGRetriever()
                print("✓ RAG system initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize RAG system: {e}")
                print("Using fallback generator.")
    
    def generate(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState] = None
    ) -> Dict[str, Any]:
        """
        Generate a workflow using enhanced multi-stage approach when available,
        otherwise fall back to RAG template-based or basic generator.
        
        Args:
            requirements: Dictionary of workflow requirements
            conversation: Optional conversation state for context
            
        Returns:
            Complete n8n workflow JSON
        """
        # Try enhanced generator with RAG context first
        if self.enhanced_generator and self.rag and self._check_rag_ready():
            print("\n" + "="*70)
            print("USING ENHANCED GENERATOR WITH RAG CONTEXT")
            print("="*70)
            
            try:
                return self._generate_with_enhanced(requirements, conversation)
            except Exception as e:
                print(f"Error in enhanced generation: {e}")
                print("Falling back to template-based approach...")
        
        # Fall back to RAG template-based approach
        if self.rag and self._check_rag_ready():
            print("Using RAG template-based generator...")
            try:
                return self._generate_with_rag(requirements, conversation)
            except Exception as e:
                print(f"Error in RAG generation: {e}")
                print("Falling back to standard generator...")
        
        # Final fallback to basic generator
        print("Using fallback workflow generator...")
        return self.fallback_generator.generate(requirements, conversation)
    
    def _generate_with_enhanced(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState] = None
    ) -> Dict[str, Any]:
        """Generate workflow using enhanced multi-stage pipeline with RAG context."""
        
        # Build query from requirements and conversation
        query = self._build_query(requirements, conversation)
        use_case = requirements.get('use_case')
        integrations = requirements.get('integrations', [])
        
        # Determine complexity
        complexity_map = {
            1: 'simple',
            2: 'simple',
            3: 'simple',
            4: 'simple',
            5: 'standard',
            6: 'standard',
            7: 'standard',
            8: 'complex',
            9: 'complex',
            10: 'complex'
        }
        complexity_score = self.fallback_generator.calculate_complexity(requirements)
        complexity = complexity_map.get(complexity_score, 'standard')
        
        print(f"\nQuery: {query}")
        print(f"Complexity: {complexity} (score: {complexity_score})")
        print(f"Integrations: {integrations}")
        
        # Retrieve RAG context
        if hasattr(self.rag, 'retrieve_context'):
            context = self.rag.retrieve_context(
                query=query,
                use_case=use_case,
                integrations=integrations,
                complexity=complexity
            )
        else:
            # Fallback for basic RAG
            context = None
        
        # Generate with enhanced pipeline
        result = self.enhanced_generator.generate(
            user_request=query,
            use_case=use_case,
            integrations=integrations,
            complexity=complexity,
            context=context
        )
        
        # Extract workflow from result
        if isinstance(result, dict) and 'workflow' in result:
            workflow = result['workflow']
            
            # Add metadata
            if 'meta' not in workflow:
                workflow['meta'] = {}
            
            workflow['meta'].update({
                'generatedBy': 'enhanced-rag-n8n-generator',
                'version': '3.0',
                'quality_score': result.get('quality_score'),
                'complexity': complexity
            })
            
            return workflow
        
        return result
    
    def _check_rag_ready(self) -> bool:
        """Check if RAG system is ready with embeddings."""
        if not self.rag or not self.rag.collection:
            return False
        
        try:
            count = self.rag.collection.count()
            return count > 0
        except:
            return False
    
    def _generate_with_rag(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState] = None
    ) -> Dict[str, Any]:
        """Generate workflow using RAG-enhanced approach."""
        
        # Build query from requirements and conversation
        query = self._build_query(requirements, conversation)
        
        # Analyze query to determine complexity and features
        analysis = self.rag.analyze_query(query)
        complexity = analysis.get('inferred_complexity', 'medium')
        
        print(f"RAG Query: {query}")
        print(f"Inferred complexity: {complexity}")
        print(f"Required features: {analysis.get('required_features', [])}")
        
        # Retrieve similar workflows
        if analysis['required_features']:
            similar_workflows = self.rag.retrieve_by_features(
                query,
                required_features=analysis['required_features'],
                n_results=3
            )
        else:
            similar_workflows = self.rag.retrieve_by_complexity(
                query,
                complexity=complexity,
                n_results=3
            )
        
        print(f"Retrieved {len(similar_workflows)} similar workflows")
        
        if not similar_workflows:
            # No similar workflows found, use fallback
            print("No similar workflows found, using fallback generator")
            return self.fallback_generator.generate(requirements, conversation)
        
        # Use the best matching workflow as a base template
        base_workflow = similar_workflows[0]
        
        # Enhance the base workflow with user requirements
        enhanced_workflow = self._enhance_template(
            base_workflow,
            requirements,
            conversation,
            query
        )
        
        return enhanced_workflow
    
    def _build_query(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState] = None
    ) -> str:
        """Build a natural language query from requirements."""
        parts = []
        
        # Use conversation initial request if available
        if conversation and conversation.initial_request:
            return conversation.initial_request
        
        # Build from requirements
        trigger = requirements.get("trigger", "workflow")
        parts.append(f"Create a {trigger} workflow that")
        
        # Add validation requirements
        if requirements.get("needs_validation"):
            parts.append("validates incoming data,")
        
        # Add duplicate checking
        if requirements.get("needs_duplicate_check"):
            parts.append("checks for duplicates,")
        
        # Add scoring
        if requirements.get("needs_scoring"):
            parts.append("scores or prioritizes items,")
        
        # Add branching
        if requirements.get("has_branching"):
            parts.append("routes data based on conditions,")
        
        # Add outputs
        outputs = requirements.get("outputs", [])
        if outputs:
            output_str = ", ".join(outputs)
            parts.append(f"and sends to {output_str}")
        
        # Add error handling
        if requirements.get("needs_error_handling"):
            parts.append("with error handling")
        
        query = " ".join(parts)
        return query
    
    def _enhance_template(
        self,
        template: Dict[str, Any],
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState],
        query: str
    ) -> Dict[str, Any]:
        """
        Enhance a template workflow with user-specific requirements.
        
        This preserves the structure and complexity of the template while
        adapting it to the user's specific needs.
        """
        import uuid
        from datetime import datetime
        
        # Create a deep copy of the template
        import json
        enhanced = json.loads(json.dumps(template))
        
        # Update workflow name
        if conversation and conversation.initial_request:
            name_parts = conversation.initial_request.split()[:6]
            enhanced['name'] = " ".join(name_parts).title() + " Workflow"
        else:
            trigger = requirements.get("trigger", "Workflow")
            action = requirements.get("outputs", ["Processing"])[0]
            enhanced['name'] = f"{trigger.title()} to {action.title()} - Enhanced"
        
        # Regenerate node IDs and webhookIds to make them unique
        node_id_map = {}
        for node in enhanced.get('nodes', []):
            old_id = node.get('id')
            new_id = str(uuid.uuid4())
            node['id'] = new_id
            
            if old_id:
                node_id_map[old_id] = new_id
            
            # Regenerate webhook IDs
            if node.get('type') == 'n8n-nodes-base.webhook':
                node['webhookId'] = str(uuid.uuid4())
                
                # Update webhook path with user requirements
                if requirements.get("webhook_path"):
                    node.setdefault('parameters', {})['path'] = requirements['webhook_path']
        
        # Update trigger node parameters if needed
        trigger_type = requirements.get("trigger")
        if trigger_type:
            for node in enhanced.get('nodes', []):
                node_type = node.get('type', '')
                
                # If user wants webhook but template has different trigger, note it
                if trigger_type == "webhook" and "webhook" not in node_type.lower():
                    if "trigger" in node_type.lower():
                        # Add note about trigger difference
                        node['notes'] = f"Original template used {node_type}. Consider changing to webhook trigger."
        
        # Update database configurations if specified
        if requirements.get("database"):
            db_type = requirements['database']
            for node in enhanced.get('nodes', []):
                if 'postgres' in node.get('type', '').lower() or 'mysql' in node.get('type', '').lower():
                    # Update to user's preferred database
                    if db_type != "postgres" and db_type != "mysql":
                        node['notes'] = f"Consider changing to {db_type} if needed"
        
        # Update output nodes based on requirements
        outputs = requirements.get("outputs", [])
        if outputs:
            for node in enhanced.get('nodes', []):
                node_type = node.get('type', '').lower()
                
                # Update email nodes
                if 'gmail' in node_type or 'email' in node_type:
                    if "email" in outputs and 'parameters' in node:
                        # Keep the structure but mark for configuration
                        node['notes'] = "Email output - configure credentials and recipient"
                
                # Update Slack nodes
                if 'slack' in node_type:
                    if "slack" in outputs:
                        node['notes'] = "Slack output - configure credentials and channel"
                
                # Update database nodes
                if any(db in node_type for db in ['postgres', 'mysql', 'mongodb']):
                    if "database" in outputs:
                        node['notes'] = "Database output - configure credentials and table"
        
        # Add metadata
        enhanced['meta'] = {
            'generatedBy': 'rag-enhanced-n8n-generator',
            'version': '2.0',
            'userQuery': query,
            'generatedAt': datetime.utcnow().isoformat() + 'Z',
            'basedOnTemplate': template.get('name', 'Unknown'),
            'templateSimilarity': template.get('_rag_metadata', {}).get('similarity_score', 0),
            'enhancementNotes': 'Workflow based on real n8n template and adapted to your requirements'
        }
        
        # Remove RAG metadata if present
        if '_rag_metadata' in enhanced:
            del enhanced['_rag_metadata']
        
        # Ensure settings exist
        if 'settings' not in enhanced:
            enhanced['settings'] = {}
        
        enhanced['settings']['executionOrder'] = 'v1'
        
        # Mark as inactive by default (user must activate after configuration)
        enhanced['active'] = False
        
        return enhanced


# Global instance
_rag_generator_instance = None


def get_rag_workflow_generator() -> RAGEnhancedWorkflowGenerator:
    """Get singleton instance of RAG-enhanced workflow generator."""
    global _rag_generator_instance
    if _rag_generator_instance is None:
        _rag_generator_instance = RAGEnhancedWorkflowGenerator()
    return _rag_generator_instance

