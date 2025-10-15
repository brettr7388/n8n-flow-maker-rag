# API Documentation

## Base URL

```
http://localhost:8000/api
```

## Endpoints

### Generate Workflow

Generate an n8n workflow from natural language.

**Endpoint:** `POST /generate`

**Request Body:**

```json
{
  "message": "Create a workflow that fetches data from an API",
  "conversationId": "optional-conversation-id",
  "previousWorkflow": {
    // Optional: previous workflow for modifications
  }
}
```

**Response:**

```json
{
  "workflowJSON": {
    "name": "API Data Fetch",
    "nodes": [...],
    "connections": {...}
  },
  "explanation": "This workflow fetches data from...",
  "validation": {
    "isValid": true,
    "errors": [],
    "warnings": []
  }
}
```

### Validate Workflow

Validate n8n workflow structure.

**Endpoint:** `POST /validate`

**Request Body:**

```json
{
  "workflow": {
    "name": "My Workflow",
    "nodes": [...],
    "connections": {...}
  }
}
```

**Response:**

```json
{
  "isValid": true,
  "errors": [],
  "warnings": ["Consider adding a description"]
}
```

### Health Check

Check API health status.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- 200: Success
- 400: Bad Request
- 500: Internal Server Error

