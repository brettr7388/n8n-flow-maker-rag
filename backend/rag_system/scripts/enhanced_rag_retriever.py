#!/usr/bin/env python3
"""
Enhanced RAG retrieval system for n8n workflows.
Implements multi-stage retrieval with priority weighting based on flowfix.txt requirements.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings


class EnhancedRAGRetriever:
    """
    Enhanced RAG retriever with multi-stage approach and priority weighting.
    Prioritizes expert templates and complex workflows for production-ready outputs.
    """
    
    def __init__(self, embeddings_dir="../embeddings"):
        self.embeddings_dir = Path(__file__).parent.parent / embeddings_dir.lstrip('../')
        
        # Connect to ChromaDB
        chroma_path = self.embeddings_dir / "chroma_db"
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Priority weights for different workflow types
        self.priority_weights = {
            'expert_template': 2.0,      # HIGHEST - Sabrina Romanov workflows
            'complex_workflow': 1.5,     # HIGH - 20+ node workflows
            'standard_workflow': 1.0     # STANDARD - other workflows
        }
        
        try:
            self.collection = self.client.get_collection(name="n8n_workflows")
            print(f"✓ Connected to vector database")
            print(f"✓ {self.collection.count()} workflows indexed")
        except Exception as e:
            print(f"Error connecting to vector database: {e}")
            print("Please run create_embeddings.py first")
            self.collection = None
    
    def retrieve_context(
        self,
        query: str,
        use_case: Optional[str] = None,
        integrations: Optional[List[str]] = None,
        complexity: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Enhanced retrieval with multi-stage approach and priority weighting.
        
        Args:
            query: User's workflow request
            use_case: General use case category
            integrations: Required integrations
            complexity: 'simple', 'standard', or 'complex'
        
        Returns:
            Structured context with expert examples, patterns, and node configs
        """
        if not self.collection:
            return self._empty_context()
        
        integrations = integrations or []
        
        # Stage 1: Retrieve expert templates (HIGHEST PRIORITY)
        expert_templates = self._retrieve_expert_templates(
            use_case=use_case or query,
            integrations=integrations,
            top_k=3
        )
        
        # Stage 2: Retrieve complex community workflows
        complex_workflows = self._retrieve_complex_workflows(
            query=query,
            min_node_count=20,
            top_k=2
        )
        
        # Stage 3: Retrieve workflow patterns
        patterns = self._retrieve_patterns(
            use_case=use_case or query,
            integrations=integrations,
            top_k=5
        )
        
        # Stage 4: Retrieve node configurations
        node_configs = self._retrieve_node_configs(
            integrations=integrations,
            top_k=10
        )
        
        # Combine and format context
        context = self._format_context(
            expert_templates=expert_templates,
            complex_workflows=complex_workflows,
            patterns=patterns,
            node_configs=node_configs,
            complexity=complexity
        )
        
        return context
    
    def _retrieve_expert_templates(
        self,
        use_case: str,
        integrations: List[str],
        top_k: int = 3
    ) -> List[Dict]:
        """Retrieve from expert template collection with highest priority."""
        try:
            # Query for expert templates (tagged with priority=10)
            results = self.collection.query(
                query_texts=[f"{use_case} {' '.join(integrations)}"],
                n_results=min(top_k * 3, self.collection.count()),
                where={"priority": {"$gte": 9}} if self._has_priority_field() else None
            )
            
            workflows = self._load_workflows_from_results(results)
            
            # Boost relevance scores for expert templates
            for wf in workflows:
                wf['_rag_metadata']['boosted_score'] = wf['_rag_metadata']['similarity_score'] * self.priority_weights['expert_template']
            
            # Sort by boosted score and return top_k
            workflows.sort(key=lambda x: x['_rag_metadata']['boosted_score'], reverse=True)
            return workflows[:top_k]
            
        except Exception as e:
            print(f"Error retrieving expert templates: {e}")
            return []
    
    def _retrieve_complex_workflows(
        self,
        query: str,
        min_node_count: int = 20,
        top_k: int = 2
    ) -> List[Dict]:
        """Retrieve complex community workflows (20+ nodes)."""
        try:
            # Query for complex workflows
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k * 5, self.collection.count())
            )
            
            workflows = []
            for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                node_count = metadata.get('node_count', 0)
                has_error = metadata.get('has_error_handling', 'false') == 'true'
                has_creds = metadata.get('has_credentials', 'false') == 'true'
                
                # Filter for complex, quality workflows
                if node_count >= min_node_count and has_error and has_creds:
                    filepath = metadata.get('filepath')
                    if filepath and Path(filepath).exists():
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                workflow = json.load(f)
                            
                            workflow['_rag_metadata'] = {
                                'similarity_score': 1 - distance,
                                'boosted_score': (1 - distance) * self.priority_weights['complex_workflow'],
                                'node_count': node_count,
                                'query': query
                            }
                            workflows.append(workflow)
                            
                            if len(workflows) >= top_k:
                                break
                        except Exception as e:
                            print(f"Error loading workflow: {e}")
            
            return workflows
            
        except Exception as e:
            print(f"Error retrieving complex workflows: {e}")
            return []
    
    def _retrieve_patterns(
        self,
        use_case: str,
        integrations: List[str],
        top_k: int = 5
    ) -> List[str]:
        """Retrieve workflow patterns for the use case."""
        patterns = []
        
        # Get workflows that match the use case
        try:
            results = self.collection.query(
                query_texts=[f"workflow pattern for {use_case} using {' '.join(integrations)}"],
                n_results=min(top_k, self.collection.count())
            )
            
            # Extract patterns from workflows
            for metadata in results['metadatas'][0]:
                filepath = metadata.get('filepath')
                if filepath and Path(filepath).exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            workflow = json.load(f)
                        
                        # Extract pattern description
                        pattern = self._extract_workflow_pattern(workflow)
                        if pattern:
                            patterns.append(pattern)
                    except Exception as e:
                        pass
        
        except Exception as e:
            print(f"Error retrieving patterns: {e}")
        
        return patterns[:top_k]
    
    def _retrieve_node_configs(
        self,
        integrations: List[str],
        top_k: int = 10
    ) -> List[Dict]:
        """Retrieve node configuration examples for specified integrations."""
        configs = []
        
        for integration in integrations:
            try:
                results = self.collection.query(
                    query_texts=[f"node configuration for {integration}"],
                    n_results=min(top_k // max(len(integrations), 1), self.collection.count())
                )
                
                for metadata in results['metadatas'][0]:
                    filepath = metadata.get('filepath')
                    if filepath and Path(filepath).exists():
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                workflow = json.load(f)
                            
                            # Extract relevant node configs
                            for node in workflow.get('nodes', []):
                                if integration.lower() in node.get('type', '').lower():
                                    config = {
                                        'type': node.get('type'),
                                        'parameters': node.get('parameters', {}),
                                        'has_credentials': 'credentials' in node,
                                        'has_error_handling': 'onError' in node or 'retryOnFail' in node
                                    }
                                    configs.append(config)
                                    
                                    if len(configs) >= top_k:
                                        break
                        except Exception as e:
                            pass
                        
                        if len(configs) >= top_k:
                            break
            except Exception as e:
                print(f"Error retrieving node configs for {integration}: {e}")
        
        return configs[:top_k]
    
    def _load_workflows_from_results(self, results: Dict) -> List[Dict]:
        """Load full workflow JSONs from query results."""
        workflows = []
        
        if not results.get('metadatas') or not results['metadatas'][0]:
            return workflows
        
        for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
            filepath = metadata.get('filepath')
            if filepath and Path(filepath).exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    workflow['_rag_metadata'] = {
                        'similarity_score': 1 - distance,
                        'distance': distance,
                        'metadata': metadata
                    }
                    
                    workflows.append(workflow)
                except Exception as e:
                    print(f"Error loading workflow {filepath}: {e}")
        
        return workflows
    
    def _extract_workflow_pattern(self, workflow: Dict) -> Optional[str]:
        """Extract a workflow pattern description."""
        nodes = workflow.get('nodes', [])
        node_types = [n.get('type', '') for n in nodes]
        
        # Identify pattern types
        has_webhook = any('webhook' in t.lower() for t in node_types)
        has_schedule = any('schedule' in t.lower() or 'cron' in t.lower() for t in node_types)
        has_if = any('if' in t.lower() for t in node_types)
        has_merge = any('merge' in t.lower() for t in node_types)
        has_ai = any('ai' in t.lower() or 'openai' in t.lower() or 'langchain' in t.lower() for t in node_types)
        
        pattern_parts = []
        
        if has_schedule:
            pattern_parts.append("Schedule trigger")
        elif has_webhook:
            pattern_parts.append("Webhook trigger")
        
        if has_ai:
            pattern_parts.append("AI processing")
        
        if has_if:
            pattern_parts.append("conditional branching")
        
        if has_merge:
            pattern_parts.append("parallel execution with merge")
        
        if pattern_parts:
            return " → ".join(pattern_parts) + f" ({len(nodes)} nodes)"
        
        return None
    
    def _format_context(
        self,
        expert_templates: List[Dict],
        complex_workflows: List[Dict],
        patterns: List[str],
        node_configs: List[Dict],
        complexity: str
    ) -> Dict[str, Any]:
        """Format retrieved context for LLM prompt."""
        return {
            "expert_examples": self._format_workflows(expert_templates),
            "additional_examples": self._format_workflows(complex_workflows),
            "patterns": patterns,
            "node_configurations": node_configs,
            "quality_requirements": self._get_quality_requirements(complexity)
        }
    
    def _format_workflows(self, workflows: List[Dict]) -> List[Dict[str, Any]]:
        """Format workflow examples for prompt."""
        formatted = []
        
        for wf in workflows:
            nodes = wf.get('nodes', [])
            
            # Extract key structural info
            structure = {
                'total_nodes': len(nodes),
                'has_conditionals': any(n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch'] for n in nodes),
                'has_merge': any(n.get('type') == 'n8n-nodes-base.merge' for n in nodes),
                'has_error_handling': any('onError' in n or 'retryOnFail' in n for n in nodes),
                'has_ai': any('ai' in n.get('type', '').lower() or 'openai' in n.get('type', '').lower() for n in nodes)
            }
            
            # Extract node types
            node_types = list(set([n.get('type', '').replace('n8n-nodes-base.', '').replace('@n8n/n8n-nodes-langchain.', '') 
                                  for n in nodes]))[:10]
            
            formatted.append({
                "name": wf.get('name', 'Untitled Workflow'),
                "description": f"Workflow with {len(nodes)} nodes",
                "node_count": len(nodes),
                "structure": structure,
                "node_types": node_types,
                "key_patterns": self._extract_key_patterns(wf)
            })
        
        return formatted
    
    def _extract_key_patterns(self, workflow: Dict) -> List[str]:
        """Extract key patterns from a workflow."""
        patterns = []
        nodes = workflow.get('nodes', [])
        
        # Error handling pattern
        error_nodes = [n for n in nodes if 'onError' in n or 'retryOnFail' in n]
        if error_nodes:
            percentage = (len(error_nodes) / len(nodes)) * 100
            patterns.append(f"Error handling on {percentage:.0f}% of nodes")
        
        # Credential pattern
        cred_nodes = [n for n in nodes if 'credentials' in n]
        if cred_nodes:
            patterns.append(f"Credentials configured on {len(cred_nodes)} service nodes")
        
        # Flow control pattern
        if any(n.get('type') == 'n8n-nodes-base.merge' for n in nodes):
            patterns.append("Parallel branches with merge node")
        
        if any(n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch'] for n in nodes):
            patterns.append("Conditional branching logic")
        
        # Data transformation
        set_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.set']
        if set_nodes:
            patterns.append(f"Data transformation with {len(set_nodes)} Set nodes")
        
        return patterns
    
    def _get_quality_requirements(self, complexity: str) -> Dict[str, Any]:
        """Get quality requirements based on complexity level."""
        requirements = {
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
        }
        return requirements.get(complexity, requirements['standard'])
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context when RAG is unavailable."""
        return {
            "expert_examples": [],
            "additional_examples": [],
            "patterns": [],
            "node_configurations": [],
            "quality_requirements": self._get_quality_requirements('standard')
        }
    
    def _has_priority_field(self) -> bool:
        """Check if collection has priority field in metadata."""
        try:
            # Try a test query to see if priority field exists
            results = self.collection.query(
                query_texts=["test"],
                n_results=1
            )
            if results['metadatas'] and results['metadatas'][0]:
                return 'priority' in results['metadatas'][0][0]
        except:
            pass
        return False


# Backward compatibility - keep old class name
class N8NWorkflowRAG(EnhancedRAGRetriever):
    """Alias for backward compatibility."""
    pass


def main():
    """Test the enhanced RAG retrieval system"""
    rag = EnhancedRAGRetriever()
    
    if not rag.collection:
        print("Cannot run tests without embeddings database")
        return
    
    print("\n" + "=" * 70)
    print("TESTING ENHANCED RAG RETRIEVAL")
    print("=" * 70)
    
    # Test query
    query = "Create a workflow that posts content to multiple social media platforms"
    use_case = "social_media"
    integrations = ["instagram", "tiktok", "twitter"]
    
    print(f"\nQuery: {query}")
    print(f"Use case: {use_case}")
    print(f"Integrations: {integrations}")
    
    # Retrieve context
    context = rag.retrieve_context(
        query=query,
        use_case=use_case,
        integrations=integrations,
        complexity='standard'
    )
    
    print(f"\n{'='*70}")
    print("RETRIEVED CONTEXT")
    print('='*70)
    
    print(f"\nExpert examples: {len(context['expert_examples'])}")
    for ex in context['expert_examples']:
        print(f"  - {ex['name']} ({ex['node_count']} nodes)")
    
    print(f"\nAdditional examples: {len(context['additional_examples'])}")
    for ex in context['additional_examples']:
        print(f"  - {ex['name']} ({ex['node_count']} nodes)")
    
    print(f"\nPatterns: {len(context['patterns'])}")
    for pattern in context['patterns']:
        print(f"  - {pattern}")
    
    print(f"\nNode configurations: {len(context['node_configurations'])}")
    
    print(f"\nQuality requirements:")
    for key, value in context['quality_requirements'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()


