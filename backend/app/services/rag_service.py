"""
RAG (Retrieval-Augmented Generation) service for n8n workflow generation.
Retrieves relevant documentation and examples from ChromaDB.
"""

import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from ..config import get_settings

class RAGService:
    """Handles retrieval of relevant n8n documentation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self._chroma_client = None
        self._collection = None
    
    @property
    def chroma_client(self):
        if self._chroma_client is None:
            self._chroma_client = chromadb.Client(Settings(
                persist_directory=self.settings.chroma_persist_directory,
                anonymized_telemetry=False
            ))
        return self._chroma_client
    
    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self.chroma_client.get_collection(
                    name=self.settings.chroma_collection_name
                )
            except Exception as e:
                # Collection doesn't exist, create it
                try:
                    self._collection = self.chroma_client.create_collection(
                        name=self.settings.chroma_collection_name,
                        metadata={"description": "n8n workflow documentation and examples"}
                    )
                except Exception as create_error:
                    print(f"Warning: Could not create ChromaDB collection: {create_error}")
                    # Return None to indicate collection is not available
                    return None
        return self._collection
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for query text."""
        response = self.openai_client.embeddings.create(
            model=self.settings.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def retrieve_relevant_context(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documentation chunks based on query.
        
        Args:
            query: User's request or question
            top_k: Number of results to return (default from settings)
        
        Returns:
            List of relevant documents with metadata
        """
        # If collection is not available, return empty list
        if self.collection is None:
            print("Warning: ChromaDB collection not available, skipping RAG retrieval")
            return []
        
        if top_k is None:
            top_k = self.settings.top_k_retrieval
        
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            context_items = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    context_items.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            return context_items
        except Exception as e:
            print(f"Warning: Error retrieving context: {e}")
            return []
    
    def format_context_for_llm(self, context_items: List[Dict[str, Any]]) -> str:
        """
        Format retrieved context into a string for LLM prompt.
        
        Args:
            context_items: List of retrieved documents
        
        Returns:
            Formatted context string
        """
        if not context_items:
            return "No specific documentation found. Use your general n8n knowledge."
        
        formatted = "# Relevant n8n Documentation\n\n"
        
        for i, item in enumerate(context_items, 1):
            metadata = item.get('metadata', {})
            title = metadata.get('title', f'Document {i}')
            content = item.get('content', '')
            
            formatted += f"## {title}\n\n{content}\n\n---\n\n"
        
        return formatted
    
    def get_context_for_generation(self, user_request: str) -> str:
        """
        Main method to get formatted context for workflow generation.
        
        Args:
            user_request: User's workflow request
        
        Returns:
            Formatted context string ready for LLM prompt
        """
        context_items = self.retrieve_relevant_context(user_request)
        return self.format_context_for_llm(context_items)

