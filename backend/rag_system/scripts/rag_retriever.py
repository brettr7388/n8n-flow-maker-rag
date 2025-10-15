#!/usr/bin/env python3
"""
RAG retrieval system for n8n workflows.
Imports enhanced retriever for better quality.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

# Import enhanced retriever
try:
    from enhanced_rag_retriever import EnhancedRAGRetriever
    USE_ENHANCED = True
except ImportError:
    USE_ENHANCED = False
    print("Warning: Enhanced RAG retriever not available, using basic version")

class N8NWorkflowRAG:
    def __init__(self, embeddings_dir="../embeddings"):
        self.embeddings_dir = Path(__file__).parent.parent / embeddings_dir.lstrip('../')
        
        # Connect to ChromaDB
        chroma_path = self.embeddings_dir / "chroma_db"
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(name="n8n_workflows")
            print(f"✓ Connected to vector database")
            print(f"✓ {self.collection.count()} workflows indexed")
        except Exception as e:
            print(f"Error connecting to vector database: {e}")
            print("Please run create_embeddings.py first")
            self.collection = None
    
    def retrieve_workflows(self, 
                          query: str,
                          n_results: int = 5,
                          filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve relevant workflows for a given query
        
        Args:
            query: Natural language description of desired workflow
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"has_webhook": "true"})
        
        Returns:
            List of workflow dictionaries with metadata
        """
        if not self.collection:
            return []
        
        # Build where clause for filtering
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                # ChromaDB stores booleans as strings
                if isinstance(value, bool):
                    where[key] = str(value)
                else:
                    where[key] = value
        
        # Query the collection
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count()),
                where=where
            )
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
        
        # Load full workflow JSONs
        workflows = []
        for metadata, distance in zip(
            results['metadatas'][0],
            results['distances'][0]
        ):
            filepath = metadata.get('filepath')
            if filepath and Path(filepath).exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    workflow['_rag_metadata'] = {
                        'similarity_score': 1 - distance,
                        'distance': distance,
                        'query': query
                    }
                    
                    workflows.append(workflow)
                except Exception as e:
                    print(f"Error loading workflow {filepath}: {e}")
        
        return workflows
    
    def retrieve_by_complexity(self, 
                               query: str,
                               complexity: str = "medium",
                               n_results: int = 3) -> List[Dict]:
        """Retrieve workflows matching a complexity level"""
        # Map complexity to node count ranges
        node_ranges = {
            "simple": (2, 5),
            "medium": (6, 15),
            "complex": (16, 100)
        }
        
        min_nodes, max_nodes = node_ranges.get(complexity, (6, 15))
        
        if not self.collection:
            return []
        
        # Query with complexity filter
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, self.collection.count())  # Get more and filter
            )
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
        
        # Filter by node count
        workflows = []
        for metadata, distance in zip(
            results['metadatas'][0],
            results['distances'][0]
        ):
            node_count = metadata.get('node_count', 0)
            if min_nodes <= node_count <= max_nodes:
                filepath = metadata.get('filepath')
                if filepath and Path(filepath).exists():
                    try:
                        with open(filepath, 'r') as f:
                            workflow = json.load(f)
                        workflow['_rag_metadata'] = {
                            'similarity_score': 1 - distance,
                            'complexity': complexity
                        }
                        workflows.append(workflow)
                        
                        if len(workflows) >= n_results:
                            break
                    except Exception as e:
                        print(f"Error loading workflow: {e}")
        
        return workflows
    
    def retrieve_by_features(self,
                            query: str,
                            required_features: List[str],
                            n_results: int = 5) -> List[Dict]:
        """Retrieve workflows with specific features"""
        feature_map = {
            "webhook": "has_webhook",
            "error_handling": "has_error_handling",
            "database": "has_database",
            "ai": "has_ai"
        }
        
        where = {}
        for feature in required_features:
            if feature in feature_map:
                where[feature_map[feature]] = "true"
        
        return self.retrieve_workflows(query, n_results, filters=where)
    
    def get_workflow_template(self, workflow_name: str) -> Optional[Dict]:
        """Retrieve a specific workflow by name"""
        if not self.collection:
            return None
        
        try:
            results = self.collection.query(
                query_texts=[workflow_name],
                n_results=1
            )
            
            if results['metadatas']:
                filepath = results['metadatas'][0][0].get('filepath')
                if filepath and Path(filepath).exists():
                    with open(filepath, 'r') as f:
                        return json.load(f)
        except Exception as e:
            print(f"Error retrieving workflow: {e}")
        
        return None
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze a user query to determine best retrieval strategy"""
        query_lower = query.lower()
        
        analysis = {
            "query": query,
            "inferred_complexity": "medium",
            "required_features": [],
            "suggested_node_types": []
        }
        
        # Complexity inference
        if any(word in query_lower for word in ["simple", "basic", "quick"]):
            analysis["inferred_complexity"] = "simple"
        elif any(word in query_lower for word in ["complex", "advanced", "sophisticated"]):
            analysis["inferred_complexity"] = "complex"
        
        # Feature detection
        if any(word in query_lower for word in ["webhook", "api", "endpoint"]):
            analysis["required_features"].append("webhook")
        
        if any(word in query_lower for word in ["error", "failure", "retry"]):
            analysis["required_features"].append("error_handling")
        
        if any(word in query_lower for word in ["database", "postgres", "mysql", "store"]):
            analysis["required_features"].append("database")
        
        if any(word in query_lower for word in ["ai", "openai", "gpt", "generate"]):
            analysis["required_features"].append("ai")
        
        # Node type suggestions
        if "email" in query_lower:
            analysis["suggested_node_types"].append("n8n-nodes-base.gmail")
        if "slack" in query_lower:
            analysis["suggested_node_types"].append("n8n-nodes-base.slack")
        if "schedule" in query_lower or "cron" in query_lower:
            analysis["suggested_node_types"].append("n8n-nodes-base.cron")
        
        return analysis

def main():
    """Test the RAG retrieval system"""
    rag = N8NWorkflowRAG()
    
    if not rag.collection:
        print("Cannot run tests without embeddings database")
        return
    
    print("\n" + "=" * 70)
    print("TESTING RAG RETRIEVAL")
    print("=" * 70)
    
    # Test queries
    test_queries = [
        "Create a workflow that sends emails when a webhook receives data",
        "Build an advanced lead distribution system with scoring",
        "Simple workflow to fetch API data and save to database"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print('='*70)
        
        # Analyze query
        analysis = rag.analyze_query(query)
        print(f"\nQuery Analysis:")
        print(f"  Complexity: {analysis['inferred_complexity']}")
        print(f"  Features: {analysis['required_features']}")
        print(f"  Suggested nodes: {analysis['suggested_node_types']}")
        
        # Retrieve workflows
        workflows = rag.retrieve_by_complexity(
            query,
            complexity=analysis['inferred_complexity'],
            n_results=3
        )
        
        print(f"\nTop {len(workflows)} matching workflows:")
        for idx, workflow in enumerate(workflows, 1):
            print(f"\n{idx}. {workflow.get('name', 'Untitled')}")
            print(f"   Nodes: {len(workflow.get('nodes', []))}")
            if '_rag_metadata' in workflow:
                print(f"   Similarity: {workflow['_rag_metadata']['similarity_score']:.3f}")
            node_types = set([n.get('type', '').replace('n8n-nodes-base.', '') for n in workflow.get('nodes', [])])
            print(f"   Node types: {', '.join(list(node_types)[:5])}...")

if __name__ == "__main__":
    main()

