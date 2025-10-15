# RAG System Integration Guide

## Overview

This guide explains how the RAG system integrates with the existing n8n Flow Generator backend and how to use it.

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP POST /api/conversation/message
                         │
┌────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend Router                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  conversation.py Router                              │  │
│  │  - Receives user message                             │  │
│  │  - Manages conversation state                        │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │  RAGEnhancedWorkflowGenerator                        │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │ Has RAG System?                             │    │  │
│  │  │ Has Embeddings?                             │    │  │
│  │  └─────┬───────────────────────┬───────────────┘    │  │
│  │        │ YES                   │ NO                  │  │
│  │        ▼                       ▼                     │  │
│  │  ┌─────────────┐      ┌──────────────────┐         │  │
│  │  │ RAG         │      │ Fallback         │         │  │
│  │  │ Generation  │      │ Generator        │         │  │
│  │  │             │      │ (Original)       │         │  │
│  │  │ - Query     │      │                  │         │  │
│  │  │   Analysis  │      │ - Rule-based     │         │  │
│  │  │ - Template  │      │ - Pattern lib    │         │  │
│  │  │   Retrieval │      │ - Node catalog   │         │  │
│  │  │ - Workflow  │      │                  │         │  │
│  │  │   Enhance   │      │                  │         │  │
│  │  └─────────────┘      └──────────────────┘         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              Complete n8n Workflow JSON
```

## Step-by-Step Integration

### 1. Initial Setup (One-Time)

```bash
cd /Users/brett/Desktop/abacustest/n8n-flow-generator/backend

# Run automated setup
cd rag_system
./setup_rag.sh

# This creates:
# - raw_templates/        (500+ workflows downloaded)
# - processed_templates/  (validated workflows)
# - embeddings/chroma_db/ (vector database)
```

**Time:** 15-20 minutes  
**Disk:** ~500 MB

### 2. Backend Integration (Already Done)

The RAG system is already integrated via `app/services/rag_workflow_generator.py`:

```python
# app/services/rag_workflow_generator.py

class RAGEnhancedWorkflowGenerator:
    def __init__(self):
        # Attempts to load RAG system
        # Falls back to standard generator if unavailable
        
    def generate(self, requirements, conversation):
        # 1. Check if RAG is available
        # 2. Use RAG if available, fallback otherwise
        # 3. Return enhanced workflow
```

### 3. Using the RAG System

#### Option A: Through Conversation API (Recommended)

The conversation API already uses the enhanced generator:

```python
# In app/routers/conversation.py
from ..services.rag_workflow_generator import get_rag_workflow_generator

# The system automatically uses RAG when available
generator = get_rag_workflow_generator()
workflow = generator.generate(requirements, conversation_state)
```

**No code changes needed!** Just ensure RAG system is set up.

#### Option B: Direct Usage

```python
from app.services.rag_workflow_generator import get_rag_workflow_generator

generator = get_rag_workflow_generator()

requirements = {
    "trigger": "webhook",
    "needs_validation": True,
    "needs_scoring": True,
    "outputs": ["email", "slack"],
    "needs_error_handling": True
}

workflow = generator.generate(requirements)
```

#### Option C: Standalone Script

```python
import sys
sys.path.append('rag_system/scripts')

from rag_retriever import N8NWorkflowRAG

rag = N8NWorkflowRAG()

# Search for similar workflows
workflows = rag.retrieve_workflows(
    "Create a lead distribution workflow with scoring",
    n_results=5
)

# Use the best match as a template
best_match = workflows[0]
```

## Configuration

### Environment Variables

```bash
# Optional: Enable LLM-enhanced generation (uses OpenAI)
export OPENAI_API_KEY="sk-..."

# System automatically works without OpenAI
# It uses template-based enhancement instead
```

### Backend Configuration

No changes needed! The system automatically:
1. Detects if RAG is set up
2. Uses RAG when available
3. Falls back to standard generator if not

### Verification

Check if RAG is active:

```bash
# Start the backend
cd backend
source venv/bin/activate  # or your venv
uvicorn app.main:app --reload

# Check logs for:
# "✓ RAG system initialized successfully"
# "✓ XXX workflows indexed"

# If not set up:
# "Warning: RAG system not available. Using fallback generator."
```

## Testing

### Test 1: Verify RAG Setup

```bash
cd backend/rag_system/scripts
python3 rag_retriever.py

# Expected output:
# ✓ Connected to vector database
# ✓ XXX workflows indexed
# [Test search results...]
```

### Test 2: Test Workflow Generation

```bash
cd backend/rag_system/scripts
python3 generate_workflow.py

# Check generated_workflows/ for output files
```

### Test 3: Full Integration Test

```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# In another terminal, test the API:
curl -X POST http://localhost:8000/api/conversation/start \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a lead distribution workflow"}'

# Response should include complex workflow with 10+ nodes
```

### Test 4: Quality Check

```bash
cd backend/rag_system/scripts
python3 validate_generated.py

# Checks:
# ✓ Structure Valid
# ✓ Error Handling
# ✓ Data Validation
# ✓ Complexity
# ✓ Connections
```

## Monitoring

### Check RAG Status

```python
from app.services.rag_workflow_generator import get_rag_workflow_generator

generator = get_rag_workflow_generator()

# Check if RAG is active
if generator.rag and generator.rag.collection:
    count = generator.rag.collection.count()
    print(f"RAG active with {count} workflows")
else:
    print("Using fallback generator")
```

### View Template Statistics

```bash
cd backend/rag_system
cat workflow_metadata.json

# Shows:
# - Total workflows
# - Complexity distribution
# - Node type usage
# - Pattern frequencies
```

## Updating Templates

### Add New Templates

```bash
cd backend/rag_system

# 1. Add new JSON files to raw_templates/custom/
# 2. Revalidate
python3 scripts/validate_templates.py

# 3. Recreate embeddings
python3 scripts/create_embeddings.py

# 4. Restart backend (auto-loads new embeddings)
```

### Scheduled Updates (Recommended)

```bash
# Add to crontab for weekly updates
0 2 * * 0 cd /path/to/backend/rag_system && ./scripts/download_templates.py && ./scripts/validate_templates.py && ./scripts/create_embeddings.py
```

## Performance Tuning

### Optimize Query Speed

```python
# Reduce number of results for faster queries
workflows = rag.retrieve_workflows(
    query,
    n_results=3  # Default is 5, reduce for speed
)
```

### Reduce Memory Usage

```python
# Use smaller embedding model
# Edit create_embeddings.py:
model_name = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB vs 420MB
```

### Cache Frequently Used Queries

```python
# Implement caching in rag_workflow_generator.py
from functools import lru_cache

@lru_cache(maxsize=100)
def _cached_retrieve(query: str, complexity: str):
    return self.rag.retrieve_by_complexity(query, complexity)
```

## Troubleshooting Integration

### Issue: Backend starts but RAG not loading

**Check:**
```bash
cd backend/rag_system/embeddings
ls -la chroma_db/

# Should contain ChromaDB files
# If empty, run:
cd ../scripts
python3 create_embeddings.py
```

### Issue: Import errors

**Solution:**
```bash
# Ensure dependencies are installed
cd backend/rag_system
pip install -r requirements_rag.txt

# Check Python path
cd ../app/services
python3 -c "import sys; sys.path.insert(0, '../../rag_system/scripts'); from rag_retriever import N8NWorkflowRAG"
```

### Issue: Workflows too complex

**Adjust complexity:**
```python
# In rag_workflow_generator.py
# Modify complexity mapping
def _build_query(self, requirements, conversation):
    # Force simpler workflows
    if len(requirements.get("outputs", [])) <= 1:
        return f"simple workflow that {query}"
```

## Migration from Old Generator

### Gradual Migration

```python
# In app/routers/conversation.py

# Option 1: A/B testing (50% RAG, 50% old)
import random
if random.random() < 0.5:
    generator = get_rag_workflow_generator()
else:
    generator = get_workflow_generator()  # Old

# Option 2: Feature flag
USE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"
generator = get_rag_workflow_generator() if USE_RAG else get_workflow_generator()
```

### Full Migration (Recommended)

Already done! The system automatically uses:
1. RAG when available (better results)
2. Fallback when RAG unavailable (original behavior)

**Best of both worlds!**

## API Changes

### No Breaking Changes

The API remains identical:

```json
POST /api/conversation/message
{
  "conversationId": "...",
  "message": "Create workflow"
}

Response:
{
  "workflowJSON": { ... },  // Now 10-50 nodes instead of 3-5!
  "explanation": "...",
  "validation": { ... }
}
```

### Optional: Expose RAG Metadata

Add to response:

```python
# In conversation.py
response = {
    "workflowJSON": workflow,
    "explanation": explanation,
    "validation": validation,
    "rag_info": {
        "enhanced": True,
        "template_used": workflow.get("meta", {}).get("basedOnTemplate"),
        "similarity": workflow.get("meta", {}).get("templateSimilarity")
    }
}
```

## Best Practices

### 1. Keep Templates Updated
```bash
# Weekly or monthly
./setup_rag.sh  # Re-runs full pipeline
```

### 2. Monitor Quality
```bash
# Track metrics
python3 scripts/validate_generated.py > quality_report.txt
```

### 3. Gradual Rollout
- Start with RAG enabled for internal testing
- Monitor user feedback
- Gradually increase usage
- Keep fallback available

### 4. Feedback Loop
- Collect user-created workflows
- Add good examples to templates
- Retrain embeddings
- Continuous improvement!

## Support

### Quick Checks

```bash
# 1. Is RAG set up?
ls backend/rag_system/embeddings/chroma_db/

# 2. Can it be imported?
cd backend
python3 -c "from app.services.rag_workflow_generator import get_rag_workflow_generator; g=get_rag_workflow_generator(); print('OK' if g.rag else 'Not loaded')"

# 3. Are workflows indexed?
cd rag_system/scripts
python3 -c "from rag_retriever import N8NWorkflowRAG; r=N8NWorkflowRAG(); print(f'{r.collection.count()} workflows' if r.collection else 'No collection')"
```

### Get Help

1. Check logs in `backend/rag_system/`
2. Review README.md for troubleshooting
3. Test with standalone scripts
4. System automatically falls back on errors

## Next Steps

1. ✅ Run setup: `./setup_rag.sh`
2. ✅ Verify: `python3 scripts/rag_retriever.py`
3. ✅ Test: Make workflow request through API
4. ✅ Monitor: Check generated workflow complexity
5. ✅ Iterate: Update templates periodically

**The integration is complete and automatic!**

---

**Questions?** Check README.md or test with standalone scripts.


