"""
Setup script to initialize ChromaDB with n8n documentation and examples.
This should be run once during initial setup and can be re-run to update the knowledge base.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KnowledgeBaseSetup:
    """Sets up the RAG knowledge base with n8n documentation."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Initialize ChromaDB
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/embeddings")
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=os.getenv("CHROMA_COLLECTION_NAME", "n8n_knowledge"),
            metadata={"description": "n8n workflow documentation and examples"}
        )
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a text using OpenAI."""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def add_n8n_core_concepts(self):
        """Add core n8n concepts to the knowledge base."""
        core_concepts = [
            {
                "id": "concept_workflow_basics",
                "title": "Workflow Basics",
                "content": """
n8n workflows are composed of nodes connected together. Each workflow must have:
1. A trigger node (to start the workflow)
2. One or more action nodes (to perform operations)
3. Connections between nodes (to define execution flow)

Basic workflow structure:
- Nodes are executed sequentially unless branched
- Data passes between nodes through connections
- Each node can transform or process data
- Workflows can be activated or run manually
                """,
                "category": "basics",
                "type": "concept"
            },
            {
                "id": "concept_node_types",
                "title": "Node Types",
                "content": """
n8n has several categories of nodes:

1. Trigger Nodes: Start workflows (Manual Trigger, Webhook, Schedule, etc.)
2. Action Nodes: Perform operations (HTTP Request, Set, Code, etc.)
3. Core Nodes: Built-in functionality (IF, Switch, Merge, etc.)
4. Integration Nodes: Connect to external services (Gmail, Slack, Airtable, etc.)

Common node types:
- Manual Trigger: For testing workflows manually
- Webhook: Receive HTTP requests
- Schedule Trigger: Run on a schedule
- HTTP Request: Make API calls
- Set: Manipulate data
- Code: Execute JavaScript/Python
- IF: Conditional branching
                """,
                "category": "basics",
                "type": "concept"
            },
            {
                "id": "concept_connections",
                "title": "Node Connections",
                "content": """
Connections define how data flows between nodes:

Connection structure:
{
  "SourceNodeName": {
    "main": [
      [
        {"node": "TargetNodeName", "type": "main", "index": 0}
      ]
    ]
  }
}

Rules:
- Connection keys use node names (not IDs)
- Most nodes use "main" output
- IF/Switch nodes can have multiple outputs
- Index 0 is the default output
- Multiple connections create parallel execution
                """,
                "category": "basics",
                "type": "concept"
            },
            {
                "id": "concept_node_structure",
                "title": "Node Structure",
                "content": """
Each n8n node has this structure:

{
  "id": "unique-uuid",
  "name": "Node Name",
  "type": "n8n-nodes-base.nodetype",
  "typeVersion": 1,
  "position": [x, y],
  "parameters": {
    // Node-specific parameters
  },
  "credentials": {
    // Optional credential references
  }
}

Important notes:
- id: Must be unique UUID
- name: Used in connections, must be unique in workflow
- type: Follows format "n8n-nodes-base.{nodeType}"
- position: [x, y] coordinates for visual layout
- parameters: Node-specific configuration
                """,
                "category": "basics",
                "type": "concept"
            },
            {
                "id": "node_manual_trigger",
                "title": "Manual Trigger Node",
                "content": """
The Manual Trigger node is used to start workflows manually (for testing).

Type: n8n-nodes-base.manualTrigger
Parameters: {} (usually empty)
Position: Typically [0, 0] (top-left)

Example:
{
  "id": "uuid",
  "name": "When clicking Test workflow",
  "type": "n8n-nodes-base.manualTrigger",
  "typeVersion": 1,
  "position": [240, 300],
  "parameters": {}
}

Usage:
- Always start simple workflows with Manual Trigger
- Good for testing and development
- Activated by clicking Test workflow button
                """,
                "category": "nodes",
                "type": "node_documentation"
            },
            {
                "id": "node_http_request",
                "title": "HTTP Request Node",
                "content": """
The HTTP Request node makes HTTP/API calls.

Type: n8n-nodes-base.httpRequest
Common parameters:
- method: GET, POST, PUT, DELETE, PATCH
- url: The endpoint URL
- authentication: none, basicAuth, oauth2, etc.
- sendQuery: boolean (send query parameters)
- sendHeaders: boolean (send custom headers)
- sendBody: boolean (send request body)
- jsonParameters: boolean (use JSON for body)
- options: Additional options

Example GET request:
{
  "id": "uuid",
  "name": "Fetch Data",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.1,
  "position": [460, 300],
  "parameters": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "authentication": "none",
    "options": {}
  }
}

Example POST request:
{
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/create",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {"name": "title", "value": "={{$json.title}}"},
        {"name": "content", "value": "={{$json.content}}"}
      ]
    }
  }
}
                """,
                "category": "nodes",
                "type": "node_documentation"
            },
            {
                "id": "node_webhook",
                "title": "Webhook Node",
                "content": """
The Webhook node receives HTTP requests to trigger workflows.

Type: n8n-nodes-base.webhook
Common parameters:
- httpMethod: GET, POST, PUT, DELETE, PATCH, HEAD
- path: Webhook path (e.g., "my-webhook")
- responseMode: onReceived, lastNode, responseNode
- responseData: Text to return

Example:
{
  "id": "uuid",
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 1.1,
  "position": [240, 300],
  "parameters": {
    "httpMethod": "POST",
    "path": "my-webhook",
    "responseMode": "onReceived",
    "responseData": "allEntries"
  },
  "webhookId": "auto-generated"
}

Usage:
- Creates publicly accessible endpoint
- Useful for integrations with external services
- Can be production or test webhook
- Response modes control when to respond to caller
                """,
                "category": "nodes",
                "type": "node_documentation"
            },
            {
                "id": "node_set",
                "title": "Set Node",
                "content": """
The Set node (now called Edit Fields) manipulates data.

Type: n8n-nodes-base.set
Common parameters:
- keepOnlySet: boolean (keep only set fields)
- values: Array of field operations

Operations:
- string: Set text value
- number: Set numeric value
- boolean: Set true/false
- dateTime: Set date/time
- object: Set object value
- array: Set array value

Example:
{
  "id": "uuid",
  "name": "Set Values",
  "type": "n8n-nodes-base.set",
  "typeVersion": 3,
  "position": [680, 300],
  "parameters": {
    "assignments": {
      "assignments": [
        {
          "id": "uuid",
          "name": "fullName",
          "value": "={{$json.firstName}} {{$json.lastName}}",
          "type": "string"
        },
        {
          "id": "uuid",
          "name": "timestamp",
          "value": "={{$now}}",
          "type": "dateTime"
        }
      ]
    },
    "options": {}
  }
}
                """,
                "category": "nodes",
                "type": "node_documentation"
            },
            {
                "id": "node_if",
                "title": "IF Node",
                "content": """
The IF node provides conditional branching.

Type: n8n-nodes-base.if
Common parameters:
- conditions: Array of condition groups
- combineOperation: AND/OR logic

Condition types:
- string: Text comparison
- number: Numeric comparison
- boolean: True/false check
- dateTime: Date comparison

Example:
{
  "id": "uuid",
  "name": "Check Status",
  "type": "n8n-nodes-base.if",
  "typeVersion": 2,
  "position": [680, 300],
  "parameters": {
    "conditions": {
      "options": {
        "combineOperation": "all"
      },
      "conditions": [
        {
          "id": "uuid",
          "leftValue": "={{$json.status}}",
          "rightValue": "success",
          "operation": {
            "type": "string",
            "operation": "equals",
            "singleValue": true
          }
        }
      ],
      "combineOperation": "all"
    }
  }
}

Connections:
- IF nodes have two outputs: true (index 0) and false (index 1)
- Connect both paths or leave one empty
                """,
                "category": "nodes",
                "type": "node_documentation"
            },
            {
                "id": "node_code",
                "title": "Code Node",
                "content": """
The Code node executes custom JavaScript or Python code.

Type: n8n-nodes-base.code
Common parameters:
- mode: runOnceForAllItems, runOnceForEachItem
- language: javaScript, python
- jsCode or pythonCode: The code to execute

JavaScript Example:
{
  "id": "uuid",
  "name": "Process Data",
  "type": "n8n-nodes-base.code",
  "typeVersion": 2,
  "position": [680, 300],
  "parameters": {
    "mode": "runOnceForAllItems",
    "jsCode": "// Access input data\\nconst items = $input.all();\\n\\n// Process data\\nconst processed = items.map(item => ({\\n  json: {\\n    ...item.json,\\n    processed: true,\\n    timestamp: new Date().toISOString()\\n  }\\n}));\\n\\nreturn processed;"
  }
}

Available variables:
- $input: Access input data
- $json: Current item data (in runOnceForEachItem mode)
- $node: Node information
- $workflow: Workflow information
                """,
                "category": "nodes",
                "type": "node_documentation"
            }
        ]
        
        print("Adding core n8n concepts...")
        for concept in core_concepts:
            embedding = self.create_embedding(concept["content"])
            self.collection.add(
                ids=[concept["id"]],
                embeddings=[embedding],
                documents=[concept["content"]],
                metadatas=[{
                    "title": concept["title"],
                    "category": concept["category"],
                    "type": concept["type"]
                }]
            )
        print(f"Added {len(core_concepts)} core concepts")
    
    def add_example_workflows(self):
        """Add example workflows to the knowledge base."""
        examples = [
            {
                "id": "example_simple_api",
                "title": "Simple API Request",
                "description": "Make a simple GET request to an API",
                "content": """
Example: Simple API GET Request

User request: "Create a workflow that fetches data from JSONPlaceholder API"

Workflow structure:
1. Manual Trigger (for testing)
2. HTTP Request to https://jsonplaceholder.typicode.com/posts

Complete workflow JSON:
{
  "name": "Simple API Request",
  "nodes": [
    {
      "id": "uuid-1",
      "name": "When clicking Test workflow",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [240, 300],
      "parameters": {}
    },
    {
      "id": "uuid-2",
      "name": "Get Posts",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [460, 300],
      "parameters": {
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "options": {}
      }
    }
  ],
  "connections": {
    "When clicking Test workflow": {
      "main": [[{"node": "Get Posts", "type": "main", "index": 0}]]
    }
  }
}

Key points:
- Always start with a trigger
- Position nodes left to right
- Use descriptive node names
- Connect trigger to first action node
                """,
                "category": "examples",
                "difficulty": "simple"
            },
            {
                "id": "example_webhook_processing",
                "title": "Webhook with Data Processing",
                "description": "Receive webhook and process data",
                "content": """
Example: Webhook with Data Processing

User request: "Create a workflow that receives POST data via webhook and formats it"

Workflow structure:
1. Webhook (POST) - receives data
2. Set node - formats the data
3. HTTP Request - sends to another API

Complete workflow JSON:
{
  "name": "Webhook Data Processing",
  "nodes": [
    {
      "id": "uuid-1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1.1,
      "position": [240, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "process-data",
        "responseMode": "onReceived"
      }
    },
    {
      "id": "uuid-2",
      "name": "Format Data",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3,
      "position": [460, 300],
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "uuid",
              "name": "processedData",
              "value": "={{$json.body}}",
              "type": "object"
            },
            {
              "id": "uuid",
              "name": "receivedAt",
              "value": "={{$now}}",
              "type": "dateTime"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Format Data", "type": "main", "index": 0}]]
    }
  }
}

Key points:
- Webhooks can receive external data
- Use Set node to format/transform data
- responseMode controls when webhook responds
                """,
                "category": "examples",
                "difficulty": "simple"
            },
            {
                "id": "example_conditional_flow",
                "title": "Conditional Workflow",
                "description": "Branch workflow based on conditions",
                "content": """
Example: Conditional Workflow with IF Node

User request: "Check if API response status is success, then send to different endpoints"

Workflow structure:
1. Manual Trigger
2. HTTP Request - fetch data
3. IF node - check status
4. Two different paths based on condition

Complete workflow JSON:
{
  "name": "Conditional API Flow",
  "nodes": [
    {
      "id": "uuid-1",
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [240, 300],
      "parameters": {}
    },
    {
      "id": "uuid-2",
      "name": "Fetch Data",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [460, 300],
      "parameters": {
        "method": "GET",
        "url": "https://api.example.com/status"
      }
    },
    {
      "id": "uuid-3",
      "name": "Check Status",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [680, 300],
      "parameters": {
        "conditions": {
          "conditions": [
            {
              "id": "uuid",
              "leftValue": "={{$json.status}}",
              "rightValue": "success",
              "operation": {
                "type": "string",
                "operation": "equals"
              }
            }
          ]
        }
      }
    },
    {
      "id": "uuid-4",
      "name": "Success Path",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3,
      "position": [900, 200],
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "uuid",
              "name": "result",
              "value": "Success processed",
              "type": "string"
            }
          ]
        }
      }
    },
    {
      "id": "uuid-5",
      "name": "Failure Path",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3,
      "position": [900, 400],
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "uuid",
              "name": "result",
              "value": "Failure handled",
              "type": "string"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Fetch Data", "type": "main", "index": 0}]]
    },
    "Fetch Data": {
      "main": [[{"node": "Check Status", "type": "main", "index": 0}]]
    },
    "Check Status": {
      "main": [
        [{"node": "Success Path", "type": "main", "index": 0}],
        [{"node": "Failure Path", "type": "main", "index": 0}]
      ]
    }
  }
}

Key points:
- IF nodes create branching logic
- First output (index 0) is true path
- Second output (index 1) is false path
- Position true path higher, false path lower visually
                """,
                "category": "examples",
                "difficulty": "moderate"
            }
        ]
        
        print("Adding example workflows...")
        for example in examples:
            embedding = self.create_embedding(example["content"])
            self.collection.add(
                ids=[example["id"]],
                embeddings=[embedding],
                documents=[example["content"]],
                metadatas=[{
                    "title": example["title"],
                    "description": example["description"],
                    "category": example["category"],
                    "difficulty": example["difficulty"],
                    "type": "example"
                }]
            )
        print(f"Added {len(examples)} example workflows")
    
    def setup(self):
        """Run complete knowledge base setup."""
        print("Starting knowledge base setup...")
        print(f"Collection: {self.collection.name}")
        print(f"Existing documents: {self.collection.count()}")
        
        # Add all knowledge
        self.add_n8n_core_concepts()
        self.add_example_workflows()
        
        print(f"\nSetup complete! Total documents: {self.collection.count()}")
        print("Knowledge base is ready for use.")

if __name__ == "__main__":
    setup = KnowledgeBaseSetup()
    setup.setup()

