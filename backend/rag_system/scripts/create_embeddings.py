#!/usr/bin/env python3
"""
Create vector embeddings for n8n workflows
"""
import json
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

class WorkflowEmbedder:
    def __init__(self, 
                 templates_dir="../processed_templates",
                 embeddings_dir="../embeddings",
                 model_name="sentence-transformers/all-mpnet-base-v2"):
        self.templates_dir = Path(__file__).parent.parent / templates_dir.lstrip('../')
        self.embeddings_dir = Path(__file__).parent.parent / embeddings_dir.lstrip('../')
        self.embeddings_dir.mkdir(exist_ok=True)
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        chroma_path = self.embeddings_dir / "chroma_db"
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Delete collection if it exists (for fresh start)
        try:
            self.client.delete_collection(name="n8n_workflows")
        except:
            pass
        
        # Create collection
        self.collection = self.client.get_or_create_collection(
            name="n8n_workflows",
            metadata={"description": "N8N workflow templates for RAG"}
        )
    
    def workflow_to_text(self, workflow: Dict) -> str:
        """Convert workflow JSON to searchable text representation"""
        parts = []
        
        # Basic info
        parts.append(f"Workflow: {workflow.get('name', 'Untitled')}")
        
        if 'description' in workflow:
            parts.append(f"Description: {workflow['description']}")
        
        # Node information
        nodes = workflow.get('nodes', [])
        node_types = [n.get('type', '').replace('n8n-nodes-base.', '') for n in nodes]
        parts.append(f"Nodes: {', '.join(set(node_types))}")
        parts.append(f"Total nodes: {len(nodes)}")
        
        # Node names and purposes
        for node in nodes:
            node_name = node.get('name', '')
            node_type = node.get('type', '').replace('n8n-nodes-base.', '')
            parts.append(f"{node_name} ({node_type})")
        
        # Connection patterns
        connections = workflow.get('connections', {})
        parts.append(f"Connections: {len(connections)}")
        
        # Tags
        if 'tags' in workflow:
            tag_names = [tag.get('name', '') for tag in workflow.get('tags', [])]
            parts.append(f"Tags: {', '.join(tag_names)}")
        
        return " | ".join(parts)
    
    def create_metadata(self, workflow: Dict, filepath: str) -> Dict:
        """Extract metadata for ChromaDB"""
        nodes = workflow.get('nodes', [])
        node_types = [n.get('type', '') for n in nodes]
        
        return {
            "name": workflow.get('name', 'Untitled')[:100],  # Truncate for ChromaDB
            "filepath": filepath,
            "node_count": len(nodes),
            "has_webhook": str('n8n-nodes-base.webhook' in node_types),
            "has_error_handling": str('n8n-nodes-base.errorTrigger' in node_types),
            "has_database": str(any('postgres' in nt or 'mysql' in nt for nt in node_types)),
            "has_ai": str(any('openai' in nt.lower() for nt in node_types))
        }
    
    def process_all_workflows(self):
        """Process and embed all workflows"""
        json_files = list(self.templates_dir.rglob("*.json"))
        
        print(f"Processing {len(json_files)} workflows...")
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, filepath in enumerate(tqdm(json_files, desc="Creating embeddings")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                
                # Convert to text
                text = self.workflow_to_text(workflow)
                documents.append(text)
                
                # Extract metadata
                metadata = self.create_metadata(workflow, str(filepath))
                metadatas.append(metadata)
                
                # Create unique ID
                ids.append(f"workflow_{idx}")
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        
        if not documents:
            print("No documents to embed!")
            return
        
        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
        
        print(f"\n✓ Created embeddings for {len(documents)} workflows")
        print(f"✓ Saved to: {self.embeddings_dir / 'chroma_db'}")
    
    def test_search(self, query: str, n_results: int = 5):
        """Test the embedding search"""
        print(f"\nTest search: '{query}'")
        print("-" * 70)
        
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        for idx, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n{idx+1}. {meta['name']}")
            print(f"   Nodes: {meta['node_count']}")
            print(f"   Similarity: {1 - distance:.3f}")
            print(f"   Preview: {doc[:150]}...")

def main():
    embedder = WorkflowEmbedder()
    
    print("=" * 70)
    print("CREATING WORKFLOW EMBEDDINGS")
    print("=" * 70)
    
    embedder.process_all_workflows()
    
    # Test searches
    if embedder.collection.count() > 0:
        print("\n" + "=" * 70)
        print("TESTING SEARCH FUNCTIONALITY")
        print("=" * 70)
        
        test_queries = [
            "Send email when webhook receives data",
            "Process leads and distribute to sales team",
            "Monitor API and send alerts",
            "Generate AI content and post to social media"
        ]
        
        for query in test_queries:
            embedder.test_search(query, n_results=3)
    else:
        print("\nNo workflows embedded, skipping search test.")

if __name__ == "__main__":
    main()


