"""
Script to scrape n8n workflows and populate knowledge base.
Run this to enhance the RAG system with real workflow examples.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.workflow_scraper import WorkflowScraper
from app.services.rag_service import RAGService
from app.config import get_settings


async def main():
    """Main scraping workflow."""
    print("=" * 80)
    print("n8n Workflow Scraper")
    print("=" * 80)
    print()
    
    settings = get_settings()
    rag_service = RAGService()
    
    # Create output directory
    output_dir = Path("./data/workflows")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Starting workflow scraper...")
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    async with WorkflowScraper() as scraper:
        # Scrape workflows from all categories
        print("Scraping workflows from n8n.io...")
        print("This may take several minutes...")
        print()
        
        all_workflows = {}
        total_scraped = 0
        
        # Scrape a few workflows from each category
        max_per_category = 20  # Limit for initial testing
        
        for category in scraper.CATEGORIES:
            print(f"📦 Scraping category: {category}")
            workflows = await scraper.scrape_category(category, max_per_category)
            all_workflows[category] = workflows
            total_scraped += len(workflows)
            print(f"   ✅ Found {len(workflows)} workflows")
            print()
        
        print(f"\n✨ Total workflows scraped: {total_scraped}\n")
        
        # Save workflows to JSON files
        print("💾 Saving workflows to disk...")
        for category, workflows in all_workflows.items():
            if workflows:
                category_file = output_dir / f"{category}.json"
                with open(category_file, 'w') as f:
                    json.dump(workflows, f, indent=2)
                print(f"   Saved {len(workflows)} workflows to {category_file.name}")
        
        print()
        print("=" * 80)
        print("📊 Scraping Statistics")
        print("=" * 80)
        
        # Calculate statistics
        total_nodes = sum(
            wf['node_count']
            for workflows in all_workflows.values()
            for wf in workflows
        )
        
        avg_complexity = sum(
            wf['complexity_score']
            for workflows in all_workflows.values()
            for wf in workflows
        ) / max(total_scraped, 1)
        
        all_patterns = set()
        for workflows in all_workflows.values():
            for wf in workflows:
                all_patterns.update(wf['patterns'])
        
        all_node_types = set()
        for workflows in all_workflows.values():
            for wf in workflows:
                all_node_types.update(wf['nodes_used'])
        
        print(f"Total workflows: {total_scraped}")
        print(f"Total nodes: {total_nodes}")
        print(f"Average complexity: {avg_complexity:.2f}/10")
        print(f"Unique patterns: {len(all_patterns)}")
        print(f"Unique node types: {len(all_node_types)}")
        print()
        
        print("🎯 Most Common Patterns:")
        pattern_counts = {}
        for workflows in all_workflows.values():
            for wf in workflows:
                for pattern in wf['patterns']:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {pattern}: {count}")
        
        print()
        print("=" * 80)
        print("🚀 Adding workflows to RAG knowledge base...")
        print("=" * 80)
        print()
        
        # Add to RAG system
        added_count = 0
        for category, workflows in all_workflows.items():
            for workflow in workflows:
                try:
                    # Create document text for embedding
                    doc_text = f"""
Title: {workflow['title']}
Category: {category}
Description: {workflow['description']}
Nodes Used: {', '.join(workflow['nodes_used'])}
Patterns: {', '.join(workflow['patterns'])}
Complexity: {workflow['complexity_score']}/10
Node Count: {workflow['node_count']}
"""
                    
                    # Create embedding
                    embedding = rag_service.create_embedding(doc_text)
                    
                    # Add to collection
                    rag_service.collection.add(
                        ids=[workflow['id']],
                        embeddings=[embedding],
                        documents=[doc_text],
                        metadatas=[{
                            "title": workflow['title'],
                            "category": category,
                            "url": workflow['url'],
                            "node_count": workflow['node_count'],
                            "complexity": workflow['complexity_score'],
                            "nodes_used": json.dumps(workflow['nodes_used']),
                            "patterns": json.dumps(workflow['patterns'])
                        }]
                    )
                    
                    added_count += 1
                    if added_count % 10 == 0:
                        print(f"   Added {added_count} workflows to knowledge base...")
                
                except Exception as e:
                    print(f"   ⚠️  Error adding workflow {workflow['id']}: {e}")
        
        print(f"\n✅ Successfully added {added_count} workflows to RAG knowledge base")
        print()
        print("=" * 80)
        print("✨ Scraping Complete!")
        print("=" * 80)
        print()
        print("The n8n Flow Generator is now enhanced with real workflow examples.")
        print("You can now generate more complex and accurate workflows!")
        print()


if __name__ == "__main__":
    asyncio.run(main())

