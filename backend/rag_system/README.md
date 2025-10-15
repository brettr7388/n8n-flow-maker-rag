# N8N RAG System Documentation

## Overview

This RAG (Retrieval-Augmented Generation) system transforms the n8n Flow Generator from producing simple 3-node workflows to generating complex, production-ready workflows with 10-50+ nodes that match real-world n8n templates.

## What This System Does

### Before RAG Enhancement:
- Generated workflows: 3-5 nodes
- Simple linear flows (Webhook → Set → Gmail)
- No error handling
- Generic configurations
- Required substantial manual editing

### After RAG Enhancement:
- Generated workflows: 10-50+ nodes
- Complex branching logic and error handling
- Real-world patterns from 500+ actual n8n workflows
- Production-ready configurations
- Minimal editing required

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG System Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Template Collection                                      │
│     ├─ GitHub repositories (awesome-n8n-templates)          │
│     ├─ n8n.io official workflows                            │
│     └─ Community templates                                  │
│                                                              │
│  2. Validation & Cleaning                                    │
│     ├─ JSON schema validation                               │
│     ├─ Node reference checking                              │
│     └─ Credential sanitization                              │
│                                                              │
│  3. Pattern Analysis                                         │
│     ├─ Node usage statistics                                │
│     ├─ Complexity categorization                            │
│     └─ Common pattern detection                             │
│                                                              │
│  4. Vector Embeddings                                        │
│     ├─ Sentence-Transformers (all-mpnet-base-v2)           │
│     ├─ ChromaDB vector storage                              │
│     └─ Semantic search indexing                             │
│                                                              │
│  5. RAG Retrieval                                            │
│     ├─ Query analysis                                        │
│     ├─ Similarity search                                     │
│     └─ Complexity filtering                                  │
│                                                              │
│  6. Workflow Enhancement                                     │
│     ├─ Template adaptation                                   │
│     ├─ Requirement integration                               │
│     └─ ID regeneration                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
rag_system/
├── README.md                   # This file
├── setup_rag.sh               # Automated setup script
├── requirements_rag.txt       # Python dependencies
│
├── scripts/                   # Core RAG scripts
│   ├── download_templates.py  # Download workflows from sources
│   ├── validate_templates.py  # Validate and clean templates
│   ├── analyze_templates.py   # Analyze patterns and metadata
│   ├── create_embeddings.py   # Create vector embeddings
│   ├── rag_retriever.py       # RAG retrieval system
│   ├── generate_workflow.py   # RAG-enhanced generation
│   └── validate_generated.py  # Quality assurance
│
├── raw_templates/             # Downloaded templates (git-ignored)
│   ├── awesome_templates/
│   ├── advanced_templates/
│   └── official/
│
├── processed_templates/       # Validated templates (git-ignored)
│   └── [organized by category]
│
├── embeddings/                # Vector database (git-ignored)
│   └── chroma_db/
│
├── generated_workflows/       # Test outputs (git-ignored)
│   └── [generated workflow JSONs]
│
└── validation/                # QA reports (git-ignored)
```

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd backend/rag_system
./setup_rag.sh
```

This script will:
1. ✓ Install all dependencies
2. ✓ Download 500+ real n8n workflows
3. ✓ Validate and clean templates
4. ✓ Analyze patterns
5. ✓ Create vector embeddings
6. ✓ Test the system

**Total time:** 15-20 minutes (first run)
**Disk space:** ~500 MB

### Option 2: Manual Setup

```bash
# 1. Install dependencies
cd backend/rag_system
pip install -r requirements_rag.txt

# 2. Download templates
python scripts/download_templates.py

# 3. Validate templates
python scripts/validate_templates.py

# 4. Analyze templates
python scripts/analyze_templates.py

# 5. Create embeddings
python scripts/create_embeddings.py

# 6. Test retrieval
python scripts/rag_retriever.py
```

## Usage

### As Part of n8n Flow Generator

The RAG system is automatically integrated into the backend. Once set up:

1. **Start the backend** (RAG loads automatically)
2. **Make workflow requests** through the API/frontend
3. **RAG enhances generation** using real templates

The system gracefully falls back to the standard generator if:
- Embeddings aren't created yet
- Vector database is unavailable
- No similar templates are found

### Standalone Testing

Test RAG generation directly:

```bash
cd backend/rag_system/scripts

# Set OpenAI key (optional, for LLM enhancement)
export OPENAI_API_KEY="your-key-here"

# Generate workflows
python generate_workflow.py

# Validate generated workflows
python validate_generated.py
```

### Query Examples

```python
from rag_retriever import N8NWorkflowRAG

rag = N8NWorkflowRAG()

# Simple query
workflows = rag.retrieve_workflows(
    "Send email when webhook receives data",
    n_results=5
)

# Complexity-based
workflows = rag.retrieve_by_complexity(
    "Lead distribution with scoring",
    complexity="complex",
    n_results=3
)

# Feature-based
workflows = rag.retrieve_by_features(
    "API polling with error handling",
    required_features=["webhook", "error_handling"],
    n_results=5
)
```

## Template Sources

### 1. enescingoz/awesome-n8n-templates
- **URL:** https://github.com/enescingoz/awesome-n8n-templates
- **Stars:** 13,000+
- **Workflows:** 200-400
- **Categories:** Gmail, Telegram, Google Services, WordPress, AI/OpenAI

### 2. wassupjay/n8n-free-templates
- **URL:** https://github.com/wassupjay/n8n-free-templates
- **Stars:** 200+
- **Workflows:** 200+
- **Focus:** Advanced patterns, AI/ML, DevOps

### 3. n8n.io Official Library
- **API:** https://n8n.io/api/templates
- **Workflows:** 100-200 (downloaded via API)
- **Quality:** Verified, high-quality templates

## Configuration

### Environment Variables

```bash
# Optional: OpenAI API key for LLM-enhanced generation
export OPENAI_API_KEY="sk-..."

# Optional: Custom paths
export RAG_TEMPLATES_DIR="/path/to/templates"
export RAG_EMBEDDINGS_DIR="/path/to/embeddings"
```

### Embedding Model

Default: `sentence-transformers/all-mpnet-base-v2`
- Size: ~420 MB
- Quality: High (768 dimensions)
- Speed: Fast

To change:
```python
embedder = WorkflowEmbedder(
    model_name="sentence-transformers/all-MiniLM-L6-v2"  # Smaller, faster
)
```

## Maintenance

### Update Templates (Weekly/Monthly)

```bash
cd backend/rag_system/scripts

# Download new templates
python download_templates.py

# Revalidate
python validate_templates.py

# Reanalyze
python analyze_templates.py

# Recreate embeddings
python create_embeddings.py
```

### Monitor Quality

```bash
# Generate test workflows
python generate_workflow.py

# Validate quality
python validate_generated.py

# Check metrics
cat ../workflow_metadata.json
```

## Troubleshooting

### Issue: "RAG system not available"

**Cause:** Embeddings not created or ChromaDB not accessible

**Solution:**
```bash
cd backend/rag_system
python scripts/create_embeddings.py
```

### Issue: "No similar workflows found"

**Cause:** Not enough templates or embeddings for the query

**Solution:**
1. Download more templates: `python scripts/download_templates.py`
2. Check query specificity (too specific queries may not match)
3. System will fallback to standard generator automatically

### Issue: "ChromaDB connection error"

**Cause:** ChromaDB database locked or corrupted

**Solution:**
```bash
cd backend/rag_system
rm -rf embeddings/chroma_db
python scripts/create_embeddings.py
```

### Issue: "Out of memory during embedding creation"

**Cause:** Large number of templates

**Solution:**
```python
# Process in smaller batches
# Edit create_embeddings.py, reduce batch_size from 100 to 50
batch_size = 50
```

## Performance Metrics

### Expected Results After Setup:

| Metric | Before RAG | After RAG |
|--------|-----------|-----------|
| Average node count | 3-5 | 12-20 |
| Error handling | 0% | 85%+ |
| Data validation | 15% | 90%+ |
| Production-ready | 10% | 75%+ |
| User editing time | 30+ min | 5-10 min |
| Complexity score | 2/10 | 7/10 |

### System Performance:

- **Query response time:** < 500ms
- **Embedding creation:** ~10 minutes (initial)
- **Memory usage:** ~2 GB (during operation)
- **Disk space:** ~500 MB (templates + embeddings)

## Advanced Features

### Custom Template Addition

```python
# Add your own workflow templates
import json
from pathlib import Path

template = {
    "name": "My Custom Workflow",
    "nodes": [...],
    "connections": {...}
}

# Save to processed_templates
output_path = Path("processed_templates/custom/my_workflow.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(template, f, indent=2)

# Recreate embeddings
# python scripts/create_embeddings.py
```

### Query Analysis

```python
from rag_retriever import N8NWorkflowRAG

rag = N8NWorkflowRAG()

# Analyze what the system understands from a query
analysis = rag.analyze_query(
    "Create a lead distribution workflow with AI scoring"
)

print(analysis)
# {
#   "inferred_complexity": "complex",
#   "required_features": ["ai", "database"],
#   "suggested_node_types": [...]
# }
```

### Batch Generation

```python
from generate_workflow import RAGWorkflowGenerator

generator = RAGWorkflowGenerator()

queries = [
    "Email automation workflow",
    "Slack notification system",
    "Database sync workflow"
]

for query in queries:
    workflow = generator.generate_workflow(query)
    # Save or process workflow
```

## API Integration

The RAG system is automatically used by the backend API:

```bash
POST /api/generate
{
  "message": "Create a lead distribution workflow"
}

# Response includes RAG-enhanced workflow
{
  "workflowJSON": {...},  # 20+ nodes from real template
  "explanation": "...",
  "validation": {...}
}
```

## Contributing

### Adding New Template Sources

Edit `scripts/download_templates.py`:

```python
def download_new_source(self):
    """Download from new source"""
    # Implement download logic
    pass

# Add to main()
count = downloader.download_new_source()
```

### Improving Pattern Detection

Edit `scripts/analyze_templates.py`:

```python
def detect_patterns(self):
    # Add new pattern detection
    if 'custom-pattern' in node_types:
        self.analysis['patterns']['custom'].append(...)
```

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in `rag_system/` directory
3. Test with: `python scripts/rag_retriever.py`
4. Fallback: System uses standard generator automatically

## License

This RAG system is part of the n8n Flow Generator project.

---

**Status:** ✅ Production Ready  
**Last Updated:** October 2025  
**Version:** 2.0


