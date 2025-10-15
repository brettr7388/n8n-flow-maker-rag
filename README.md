# n8n Flow Generator

An AI-powered tool to generate n8n workflows from natural language descriptions.

## Features

- 🤖 Natural language to n8n workflow conversion
- 💬 Conversational interface for iterative refinement
- 🔍 RAG-powered documentation retrieval
- ✅ Automatic workflow validation
- 📊 Visual workflow preview
- 💾 Conversation history persistence
- 📥 Export workflows as JSON

## Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- ReactFlow
- Zustand

**Backend:**
- FastAPI (Python 3.11+)
- OpenAI GPT-4
- ChromaDB
- Pydantic

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your OpenAI API key to .env

# Setup knowledge base
python scripts/setup_knowledge_base.py

# Run server
python -m app.main
```

Backend will run on http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Run development server
npm run dev
```

Frontend will run on http://localhost:3000

## Usage

1. Open http://localhost:3000
2. Describe your workflow in natural language
3. Review the generated workflow
4. Iterate by asking for modifications
5. Download the JSON and import into n8n

## Example Prompts

- "Create a workflow that fetches data from an API"
- "Add a webhook that receives POST data and processes it"
- "Check if the status is success and send to different endpoints"
- "Add data transformation after the API call"

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Project Structure

```
n8n-flow-generator/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── data/        # Knowledge base data
│   └── scripts/     # Setup scripts
├── frontend/        # Next.js frontend
│   └── src/        # Source code
└── docs/           # Documentation
```

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

### Backend (Railway/Render/Fly.io)

1. Push to GitHub
2. Connect repository to hosting platform
3. Set environment variables
4. Deploy

### Frontend (Vercel)

```bash
cd frontend
vercel deploy
```

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT

## Acknowledgments

- n8n team for the amazing workflow automation tool
- OpenAI for GPT-4 API
- ChromaDB for vector storage

