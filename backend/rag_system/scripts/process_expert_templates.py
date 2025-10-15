#!/usr/bin/env python3
"""
Process expert templates and add them to embeddings with high priority scores.
This script enhances the RAG system with curated expert workflows.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in backend directory
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from: {env_path}")
    else:
        # Try parent directories
        for parent in [Path(__file__).parent.parent.parent.parent, Path(__file__).parent.parent.parent.parent.parent]:
            env_path = parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✓ Loaded environment from: {env_path}")
                break
except ImportError:
    print("Warning: python-dotenv not installed. Using existing environment variables.")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import chromadb
    from chromadb.config import Settings
    from openai import OpenAI
except ImportError as e:
    print(f"Error: Missing required packages: {e}")
    print("Please run: pip install chromadb openai")
    sys.exit(1)


class ExpertTemplateProcessor:
    """Processes expert templates and adds them to ChromaDB with high priority."""
    
    def __init__(self):
        # Connect to ChromaDB
        embeddings_dir = Path(__file__).parent.parent / "embeddings"
        chroma_path = embeddings_dir / "chroma_db"
        
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name="n8n_workflows")
            print(f"✓ Connected to existing collection ({self.collection.count()} workflows)")
        except:
            self.collection = self.client.create_collection(
                name="n8n_workflows",
                metadata={"description": "n8n workflow templates with expert workflows"}
            )
            print("✓ Created new collection")
        
        # Initialize OpenAI for embeddings
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.openai_client = OpenAI(api_key=api_key)
    
    def process_expert_templates(self, expert_templates_dir: Path):
        """Process all expert templates from a directory."""
        
        if not expert_templates_dir.exists():
            print(f"Error: Directory not found: {expert_templates_dir}")
            return
        
        templates_processed = 0
        
        # Process each category (including 'expert' folder)
        for category in ['expert', 'social_media', 'ai_video_generation']:
            category_dir = expert_templates_dir / category
            
            if not category_dir.exists():
                print(f"Warning: Category directory not found: {category_dir}")
                continue
            
            # Check if there are any JSON files
            json_files = list(category_dir.glob('*.json'))
            if not json_files:
                continue
            
            print(f"\nProcessing {category} templates...")
            
            for filepath in json_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    self._add_expert_workflow(workflow, filepath, category)
                    templates_processed += 1
                    print(f"  ✓ Processed: {filepath.name}")
                    
                except Exception as e:
                    print(f"  ✗ Error processing {filepath.name}: {e}")
        
        print(f"\n✓ Processed {templates_processed} expert templates")
        print(f"✓ Total workflows in collection: {self.collection.count()}")
    
    def _add_expert_workflow(self, workflow: Dict[str, Any], filepath: Path, category: str):
        """Add a single expert workflow to the collection with high priority."""
        
        # Analyze workflow
        nodes = workflow.get('nodes', [])
        node_count = len(nodes)
        
        # Detect features
        has_webhook = any('webhook' in n.get('type', '').lower() for n in nodes)
        has_schedule = any('schedule' in n.get('type', '').lower() or 'cron' in n.get('type', '').lower() for n in nodes)
        has_error_handling = any('onError' in n or 'retryOnFail' in n for n in nodes)
        has_credentials = any('credentials' in n for n in nodes)
        has_ai = any('ai' in n.get('type', '').lower() or 'openai' in n.get('type', '').lower() or 'langchain' in n.get('type', '').lower() for n in nodes)
        has_conditionals = any(n.get('type') in ['n8n-nodes-base.if', 'n8n-nodes-base.switch'] for n in nodes)
        has_merge = any(n.get('type') == 'n8n-nodes-base.merge' for n in nodes)
        has_database = any('postgres' in n.get('type', '').lower() or 'mysql' in n.get('type', '').lower() or 'mongodb' in n.get('type', '').lower() for n in nodes)
        
        # Extract integrations
        node_types = list(set([n.get('type', '') for n in nodes]))
        integrations = ', '.join([nt.replace('n8n-nodes-base.', '').replace('@n8n/n8n-nodes-langchain.', '') for nt in node_types[:20]])
        
        # Create rich description for embedding
        workflow_name = workflow.get('name', filepath.stem)
        description = f"""EXPERT TEMPLATE: {workflow_name}

Category: {category}
Node Count: {node_count}
Complexity: {'very_high' if node_count >= 30 else 'high'}

Features:
- Error handling: {has_error_handling}
- Credentials configured: {has_credentials}
- AI integration: {has_ai}
- Conditional logic: {has_conditionals}
- Parallel execution: {has_merge}
- Webhook trigger: {has_webhook}
- Scheduled trigger: {has_schedule}
- Database integration: {has_database}

Integrations: {integrations}

This is a production-ready expert workflow template suitable for reference when generating similar workflows.
"""
        
        # Create embedding
        try:
            # Use the same embedding model as the existing collection
            # Check the .env file or use text-embedding-3-small with dimension 384
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=description,
                dimensions=384  # Match existing collection dimension
            )
            embedding = response.data[0].embedding
        except Exception as e:
            print(f"    Warning: Failed to create embedding: {e}")
            return
        
        # Create metadata
        metadata = {
            "filepath": str(filepath.absolute()),
            "name": workflow_name,
            "node_count": node_count,
            "category": category,
            "priority": 10,  # HIGHEST PRIORITY for expert templates
            "source": "expert_template",
            "has_webhook": str(has_webhook),
            "has_error_handling": str(has_error_handling),
            "has_credentials": str(has_credentials),
            "has_ai": str(has_ai),
            "has_database": str(has_database),
            "complexity": "very_high" if node_count >= 30 else "high"
        }
        
        # Generate unique ID
        doc_id = f"expert_{category}_{filepath.stem}"
        
        # Add to collection
        try:
            # Check if already exists
            try:
                existing = self.collection.get(ids=[doc_id])
                if existing['ids']:
                    # Update existing
                    self.collection.update(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        documents=[description]
                    )
                    return
            except:
                pass
            
            # Add new
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[description]
            )
        except Exception as e:
            print(f"    Warning: Failed to add to collection: {e}")
    
    def create_metadata_file(self, expert_templates_dir: Path):
        """Create workflow metadata file for expert templates."""
        
        metadata_dir = expert_templates_dir / 'metadata'
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "1_post_everywhere.json": {
                "tags": ["social_media", "multi_platform", "scheduling", "google_sheets"],
                "complexity": "high",
                "node_count": 23,
                "use_cases": ["content_distribution", "social_media_automation"],
                "integrations": ["blotato", "google_sheets"],
                "priority": "VERY_HIGH",
                "features": ["error_handling", "scheduling", "data_transformation"]
            },
            "2_email_to_longform_thread.json": {
                "tags": ["social_media", "ai", "email", "content_generation"],
                "complexity": "high",
                "node_count": 19,
                "use_cases": ["email_automation", "ai_content", "social_media"],
                "integrations": ["gmail", "langchain", "openai", "blotato"],
                "priority": "VERY_HIGH",
                "features": ["ai_agent", "email_trigger", "multi_platform_posting"]
            },
            "3_hackernews_to_ai_videos.json": {
                "tags": ["ai", "video_generation", "social_media", "hackernews"],
                "complexity": "very_high",
                "node_count": 36,
                "use_cases": ["ai_video", "content_automation", "trend_monitoring"],
                "integrations": ["blotato", "openai", "hackernews", "langchain"],
                "priority": "VERY_HIGH",
                "features": ["ai_agent", "error_handling", "retry_logic", "conditional_branching", "async_operations"]
            },
            "4_viral_news_to_avatar.json": {
                "tags": ["ai", "video_generation", "news", "social_media"],
                "complexity": "very_high",
                "node_count": 35,
                "use_cases": ["ai_video", "news_automation", "viral_content"],
                "integrations": ["perplexity", "openai", "blotato", "http_request"],
                "priority": "VERY_HIGH",
                "features": ["ai_research", "error_handling", "conditional_logic", "async_operations"]
            },
            "5_instagram_carousels_ai_chat.json": {
                "tags": ["social_media", "instagram", "ai", "interactive"],
                "complexity": "very_high",
                "node_count": 29,
                "use_cases": ["instagram_automation", "ai_chat", "carousel_creation"],
                "integrations": ["chat_trigger", "langchain", "openai", "blotato"],
                "priority": "VERY_HIGH",
                "features": ["conversational_ai", "memory_buffer", "image_generation", "conditional_logic"]
            },
            "6_ai_avatar_trending_news.json": {
                "tags": ["ai", "video_generation", "trending", "news"],
                "complexity": "high",
                "node_count": 27,
                "use_cases": ["ai_video", "trend_monitoring", "news_automation"],
                "integrations": ["hackernews", "http_request", "openai", "langchain", "blotato"],
                "priority": "VERY_HIGH",
                "features": ["ai_agent", "trend_discovery", "multi_platform_distribution"]
            },
            "7_repost_tiktok_videos.json": {
                "tags": ["social_media", "tiktok", "video", "automation"],
                "complexity": "medium_high",
                "node_count": 21,
                "use_cases": ["video_automation", "content_distribution", "tiktok"],
                "integrations": ["rss", "http_request", "google_drive", "code"],
                "priority": "VERY_HIGH",
                "features": ["rss_monitoring", "api_interactions", "file_storage", "custom_logic"]
            }
        }
        
        metadata_file = metadata_dir / 'workflow_tags.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Created metadata file: {metadata_file}")


def main():
    """Main entry point."""
    print("="*70)
    print("EXPERT TEMPLATE PROCESSOR")
    print("="*70)
    
    # Get expert templates directory
    rag_system_dir = Path(__file__).parent.parent
    expert_templates_dir = rag_system_dir / "expert_templates"
    
    # Create processor
    try:
        processor = ExpertTemplateProcessor()
    except Exception as e:
        print(f"\nError initializing processor: {e}")
        return
    
    # Process expert templates
    processor.process_expert_templates(expert_templates_dir)
    
    # Create metadata file
    processor.create_metadata_file(expert_templates_dir)
    
    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print("\nExpert templates have been added to the RAG system with priority=10")
    print("They will be retrieved first for relevant workflow generation requests.")


if __name__ == "__main__":
    main()

