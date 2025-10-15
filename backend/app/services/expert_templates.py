"""
Expert template management and integration.
Manages high-quality reference workflows for RAG retrieval.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class ExpertTemplateManager:
    """Manages expert workflow templates with high priority scoring."""
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            # Default to rag_system/expert_templates
            base_path = Path(__file__).parent.parent.parent / "rag_system" / "expert_templates"
            self.template_dir = base_path
        else:
            self.template_dir = Path(template_dir)
        
        self.templates: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Load templates if directory exists
        if self.template_dir.exists():
            self._load_all_templates()
            self._load_metadata()
    
    def _load_all_templates(self):
        """Load all expert workflow templates from disk."""
        self.templates = []
        
        for category_dir in ['social_media', 'ai_video_generation']:
            category_path = self.template_dir / category_dir
            
            if not category_path.exists():
                continue
            
            for file_path in category_path.glob('*.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    
                    self.templates.append({
                        'name': file_path.stem,
                        'category': category_dir,
                        'filepath': str(file_path),
                        'workflow': template,
                        'node_count': len(template.get('nodes', [])),
                        'complexity': self._calculate_complexity(template)
                    })
                except Exception as e:
                    print(f"Error loading template {file_path}: {e}")
    
    def _load_metadata(self):
        """Load workflow metadata tags."""
        metadata_file = self.template_dir / 'metadata' / 'workflow_tags.json'
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
    
    def _calculate_complexity(self, workflow: Dict[str, Any]) -> str:
        """Calculate workflow complexity level."""
        nodes = workflow.get('nodes', [])
        node_count = len(nodes)
        
        # Check for advanced features
        has_ai = any('ai' in n.get('type', '').lower() or 'langchain' in n.get('type', '').lower() 
                     for n in nodes)
        has_conditionals = any(n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch'] 
                               for n in nodes)
        has_merge = any(n.get('type') == 'n8n-nodes-base.merge' for n in nodes)
        has_error_handling = any('onError' in n or 'retryOnFail' in n for n in nodes)
        
        complexity_score = 0
        if node_count >= 30:
            complexity_score += 3
        elif node_count >= 20:
            complexity_score += 2
        elif node_count >= 15:
            complexity_score += 1
        
        if has_ai:
            complexity_score += 2
        if has_conditionals:
            complexity_score += 1
        if has_merge:
            complexity_score += 1
        if has_error_handling:
            complexity_score += 1
        
        if complexity_score >= 6:
            return 'very_high'
        elif complexity_score >= 4:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        else:
            return 'simple'
    
    def find_similar_templates(
        self, 
        use_case: str, 
        integrations: List[str], 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find most similar expert templates based on use case and integrations.
        
        Args:
            use_case: General use case (e.g., 'social_media', 'ai_video')
            integrations: List of required integrations
            top_k: Number of results to return
        
        Returns:
            List of matching templates with metadata
        """
        if not self.templates:
            return []
        
        scored_templates = []
        
        for template in self.templates:
            score = 0
            
            # Category match
            if use_case.lower() in template['category'].lower():
                score += 50
            
            # Node type matches
            workflow = template['workflow']
            node_types = {n.get('type', '') for n in workflow.get('nodes', [])}
            
            for integration in integrations:
                integration_lower = integration.lower()
                matching_nodes = [nt for nt in node_types if integration_lower in nt.lower()]
                if matching_nodes:
                    score += 20
            
            # Metadata matches
            template_name = template['name']
            if template_name in self.metadata:
                meta = self.metadata[template_name]
                tags = meta.get('tags', [])
                
                for integration in integrations:
                    if any(integration.lower() in tag.lower() for tag in tags):
                        score += 10
            
            scored_templates.append({
                **template,
                'relevance_score': score
            })
        
        # Sort by score and return top_k
        scored_templates.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_templates[:top_k]
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all loaded templates."""
        return self.templates
    
    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by name."""
        for template in self.templates:
            if template['name'] == name:
                return template
        return None
    
    def extract_patterns(self, template: Dict[str, Any]) -> List[str]:
        """Extract key workflow patterns from a template."""
        patterns = []
        workflow = template.get('workflow', {})
        nodes = workflow.get('nodes', [])
        
        # Identify multi-platform posting pattern
        posting_nodes = [n for n in nodes if 'post' in n.get('type', '').lower() 
                         or 'blotato' in n.get('type', '').lower()]
        if len(posting_nodes) >= 3:
            platforms = [n.get('name', 'platform') for n in posting_nodes[:5]]
            patterns.append(f"Multi-platform distribution: {', '.join(platforms)}")
        
        # Identify AI generation pattern
        ai_nodes = [n for n in nodes if 'ai' in n.get('type', '').lower() 
                    or 'openai' in n.get('type', '').lower()
                    or 'langchain' in n.get('type', '').lower()]
        if len(ai_nodes) >= 2:
            patterns.append(f"AI-driven content generation with {len(ai_nodes)} AI nodes")
        
        # Identify conditional branching
        if_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.if']
        switch_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.switch']
        if if_nodes or switch_nodes:
            patterns.append(f"Conditional branching with {len(if_nodes + switch_nodes)} decision points")
        
        # Identify merge pattern
        merge_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.merge']
        if merge_nodes:
            patterns.append(f"Parallel execution with {len(merge_nodes)} merge points")
        
        # Identify error handling
        error_nodes = [n for n in nodes if 'onError' in n or 'retryOnFail' in n]
        if error_nodes:
            percentage = (len(error_nodes) / len(nodes)) * 100
            patterns.append(f"Error handling on {percentage:.0f}% of nodes")
        
        # Identify data transformation
        set_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.set']
        code_nodes = [n for n in nodes if n.get('type') in ['n8n-nodes-base.code', 'n8n-nodes-base.function']]
        if set_nodes or code_nodes:
            patterns.append(f"Data transformation with {len(set_nodes + code_nodes)} processing nodes")
        
        return patterns
    
    def extract_node_configs(
        self, 
        template: Dict[str, Any], 
        node_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract node configuration examples from a template."""
        workflow = template.get('workflow', {})
        nodes = workflow.get('nodes', [])
        
        configs = []
        for node in nodes:
            node_type = node.get('type', '')
            
            # Filter by type if specified
            if node_type_filter and node_type_filter.lower() not in node_type.lower():
                continue
            
            # Extract key configuration
            config = {
                'type': node_type,
                'name': node.get('name'),
                'parameters': node.get('parameters', {}),
                'has_credentials': 'credentials' in node,
                'has_error_handling': 'onError' in node or 'retryOnFail' in node
            }
            
            if 'credentials' in node:
                config['credentials'] = node['credentials']
            
            if 'onError' in node:
                config['onError'] = node['onError']
            
            if 'retryOnFail' in node:
                config['retryOnFail'] = node['retryOnFail']
                config['maxTries'] = node.get('maxTries', 3)
            
            configs.append(config)
        
        return configs
    
    def create_metadata_file(self, workflows: Dict[str, Dict[str, Any]]):
        """Create workflow metadata tags file."""
        metadata_dir = self.template_dir / 'metadata'
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / 'workflow_tags.json'
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(workflows, f, indent=2)
        
        print(f"Created metadata file: {metadata_file}")


# Global instance
_expert_template_manager = None


def get_expert_template_manager() -> ExpertTemplateManager:
    """Get singleton instance of expert template manager."""
    global _expert_template_manager
    if _expert_template_manager is None:
        _expert_template_manager = ExpertTemplateManager()
    return _expert_template_manager


