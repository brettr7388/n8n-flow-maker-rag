from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./data/embeddings"
    chroma_collection_name: str = "n8n_knowledge"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Generation Configuration
    max_tokens: int = 4000
    temperature: float = 0.3
    top_k_retrieval: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Quality thresholds for workflow validation
QUALITY_CONFIG = {
    'min_node_count': {
        'simple': 15,
        'standard': 25,
        'complex': 35
    },
    'min_quality_score': 80,
    'min_error_handling_percentage': 0.3,
    'min_sticky_notes': 5,
    'max_generation_attempts': 3
}

# Node type configuration
NODE_TYPE_CONFIG = {
    'requires_credentials': [
        'n8n-nodes-base.httpRequest',
        '@blotato/n8n-nodes-blotato.blotato',
        'n8n-nodes-base.openAi',
        'n8n-nodes-base.gmail',
        'n8n-nodes-base.googleSheets',
        'n8n-nodes-base.slack',
        'n8n-nodes-base.postgres',
        'n8n-nodes-base.mysql',
        'n8n-nodes-base.mongodb',
        '@n8n/n8n-nodes-langchain.chatOpenAi',
        'n8n-nodes-base.perplexity'
    ],
    'requires_error_handling': [
        'n8n-nodes-base.httpRequest',
        '@blotato/n8n-nodes-blotato.blotato',
        'n8n-nodes-base.webhook',
        'n8n-nodes-base.openAi',
        'n8n-nodes-base.gmail',
        'n8n-nodes-base.slack',
        'n8n-nodes-base.googleSheets'
    ]
}

# RAG configuration for enhanced retrieval
RAG_CONFIG = {
    'expert_template_boost': 2.0,
    'complex_workflow_boost': 1.5,
    'min_node_count_filter': 15,
    'retrieval_stages': {
        'expert_templates': 3,
        'complex_workflows': 2,
        'patterns': 5,
        'node_configs': 10
    },
    'priority_levels': {
        'expert_template': 10,
        'complex_workflow': 8,
        'standard_workflow': 5,
        'basic_example': 2
    }
}

# Expert templates directory
def get_expert_templates_dir() -> Path:
    """Get path to expert templates directory."""
    return Path(__file__).parent.parent / "rag_system" / "expert_templates"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

