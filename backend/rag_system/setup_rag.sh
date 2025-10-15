#!/bin/bash
##############################################################################
# RAG System Setup Script
# 
# This script sets up the complete RAG (Retrieval-Augmented Generation)
# system for the n8n Flow Generator by:
# 1. Installing dependencies
# 2. Downloading real n8n workflow templates
# 3. Validating and cleaning templates
# 4. Analyzing templates for patterns
# 5. Creating vector embeddings
# 6. Testing the retrieval system
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}N8N RAG SYSTEM SETUP${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Python
echo -e "${YELLOW}[1/7] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}[2/7] Installing Python dependencies...${NC}"
if [ -f "requirements_rag.txt" ]; then
    python3 -m pip install -r requirements_rag.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements_rag.txt not found${NC}"
    exit 1
fi
echo ""

# Step 3: Download templates
echo -e "${YELLOW}[3/7] Downloading real n8n workflow templates...${NC}"
echo -e "${BLUE}This may take several minutes...${NC}"
if [ -f "scripts/download_templates.py" ]; then
    python3 scripts/download_templates.py
    echo -e "${GREEN}✓ Templates downloaded${NC}"
else
    echo -e "${RED}Error: download_templates.py not found${NC}"
    exit 1
fi
echo ""

# Step 4: Validate templates
echo -e "${YELLOW}[4/7] Validating and cleaning templates...${NC}"
if [ -f "scripts/validate_templates.py" ]; then
    python3 scripts/validate_templates.py
    echo -e "${GREEN}✓ Templates validated${NC}"
else
    echo -e "${RED}Error: validate_templates.py not found${NC}"
    exit 1
fi
echo ""

# Step 5: Analyze templates
echo -e "${YELLOW}[5/7] Analyzing template patterns...${NC}"
if [ -f "scripts/analyze_templates.py" ]; then
    python3 scripts/analyze_templates.py
    echo -e "${GREEN}✓ Templates analyzed${NC}"
else
    echo -e "${RED}Error: analyze_templates.py not found${NC}"
    exit 1
fi
echo ""

# Step 6: Create embeddings
echo -e "${YELLOW}[6/7] Creating vector embeddings...${NC}"
echo -e "${BLUE}This will download the sentence-transformers model (~420MB)${NC}"
echo -e "${BLUE}and may take 5-10 minutes...${NC}"
if [ -f "scripts/create_embeddings.py" ]; then
    python3 scripts/create_embeddings.py
    echo -e "${GREEN}✓ Embeddings created${NC}"
else
    echo -e "${RED}Error: create_embeddings.py not found${NC}"
    exit 1
fi
echo ""

# Step 7: Test retrieval
echo -e "${YELLOW}[7/7] Testing RAG retrieval system...${NC}"
if [ -f "scripts/rag_retriever.py" ]; then
    python3 scripts/rag_retriever.py
    echo -e "${GREEN}✓ RAG system tested${NC}"
else
    echo -e "${RED}Error: rag_retriever.py not found${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RAG SYSTEM SETUP COMPLETE!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. (Optional) Set OPENAI_API_KEY for LLM-enhanced generation:"
echo -e "   export OPENAI_API_KEY='your-key-here'"
echo ""
echo -e "2. Test workflow generation:"
echo -e "   cd scripts"
echo -e "   python3 generate_workflow.py"
echo ""
echo -e "3. Restart your n8n Flow Generator backend to use RAG:"
echo -e "   cd ../../"
echo -e "   # Restart your FastAPI server"
echo ""
echo -e "${BLUE}The RAG system is now integrated and will automatically${NC}"
echo -e "${BLUE}enhance workflow generation with real n8n templates!${NC}"
echo ""


