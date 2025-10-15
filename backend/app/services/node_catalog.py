"""
Node Capability Catalog for n8n nodes.
Comprehensive database of n8n node types, capabilities, and usage patterns.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class NodeCapability:
    """Represents capabilities of an n8n node."""
    
    node_type: str
    category: str
    purpose: str
    use_cases: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    common_combinations: List[List[str]] = field(default_factory=list)
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    requires_credentials: bool = False
    credential_types: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_type": self.node_type,
            "category": self.category,
            "purpose": self.purpose,
            "use_cases": self.use_cases,
            "parameters": self.parameters,
            "common_combinations": self.common_combinations,
            "code_examples": self.code_examples,
            "requires_credentials": self.requires_credentials,
            "credential_types": self.credential_types
        }


class NodeCatalog:
    """Catalog of n8n node capabilities and usage patterns."""
    
    def __init__(self):
        self.nodes = self._build_catalog()
    
    def _build_catalog(self) -> Dict[str, NodeCapability]:
        """Build comprehensive node catalog."""
        catalog = {}
        
        # Trigger Nodes
        catalog["webhook"] = NodeCapability(
            node_type="n8n-nodes-base.webhook",
            category="trigger",
            purpose="Receive HTTP requests and trigger workflows",
            use_cases=[
                "Receive data from external systems",
                "Create API endpoints",
                "Integrate with forms and webhooks",
                "Handle third-party service callbacks"
            ],
            parameters={
                "httpMethod": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                "path": "string",
                "authentication": ["none", "basicAuth", "headerAuth"],
                "responseMode": ["onReceived", "lastNode", "responseNode"]
            },
            common_combinations=[
                ["webhook", "function", "database"],
                ["webhook", "set", "httpRequest"],
                ["webhook", "if", "gmail"]
            ]
        )
        
        catalog["schedule"] = NodeCapability(
            node_type="n8n-nodes-base.scheduleTrigger",
            category="trigger",
            purpose="Trigger workflows on a schedule",
            use_cases=[
                "Run periodic tasks",
                "Daily/weekly/monthly automation",
                "Time-based data synchronization",
                "Scheduled reports and notifications"
            ],
            parameters={
                "mode": ["interval", "custom"],
                "interval": ["seconds", "minutes", "hours", "days", "weeks"],
                "cronExpression": "string"
            },
            common_combinations=[
                ["schedule", "httpRequest", "database"],
                ["schedule", "database", "email"],
                ["schedule", "function", "slack"]
            ]
        )
        
        catalog["emailTrigger"] = NodeCapability(
            node_type="n8n-nodes-base.emailReadImap",
            category="trigger",
            purpose="Trigger on new emails (IMAP)",
            use_cases=[
                "Process incoming emails",
                "Email-based automation",
                "Support ticket systems",
                "Email parsing and routing"
            ],
            requires_credentials=True,
            credential_types=["imap"],
            common_combinations=[
                ["emailTrigger", "function", "database"],
                ["emailTrigger", "if", "slack"]
            ]
        )
        
        # Data Processing Nodes
        catalog["function"] = NodeCapability(
            node_type="n8n-nodes-base.function",
            category="data_processing",
            purpose="Execute custom JavaScript code",
            use_cases=[
                "Data transformation and manipulation",
                "Complex calculations",
                "Data validation",
                "Custom business logic"
            ],
            code_examples=[
                {
                    "name": "Validate email format",
                    "code": """const email = $input.item.json.email;
const isValid = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
return { ...$input.item.json, emailValid: isValid };"""
                },
                {
                    "name": "Calculate lead score",
                    "code": """let score = 0;
if ($input.item.json.company_size > 100) score += 30;
if ($input.item.json.budget > 10000) score += 40;
if ($input.item.json.industry === 'tech') score += 20;
return { ...$input.item.json, score: score };"""
                },
                {
                    "name": "Transform data structure",
                    "code": """const items = $input.all();
return items.map(item => ({
  id: item.json.id,
  fullName: `${item.json.firstName} ${item.json.lastName}`,
  email: item.json.email.toLowerCase()
}));"""
                }
            ],
            common_combinations=[
                ["function", "if", "set"],
                ["webhook", "function", "httpRequest"],
                ["database", "function", "gmail"]
            ]
        )
        
        catalog["set"] = NodeCapability(
            node_type="n8n-nodes-base.set",
            category="data_processing",
            purpose="Set or transform data values",
            use_cases=[
                "Add new fields to data",
                "Rename fields",
                "Set static values",
                "Prepare data for next node"
            ],
            parameters={
                "values": {
                    "string": "array of string values",
                    "number": "array of number values",
                    "boolean": "array of boolean values"
                },
                "options": {
                    "dotNotation": "boolean"
                }
            },
            common_combinations=[
                ["webhook", "set", "gmail"],
                ["function", "set", "httpRequest"],
                ["database", "set", "slack"]
            ]
        )
        
        catalog["code"] = NodeCapability(
            node_type="n8n-nodes-base.code",
            category="data_processing",
            purpose="Execute JavaScript or Python code",
            use_cases=[
                "Advanced data processing",
                "Custom algorithms",
                "Integration with libraries",
                "Complex transformations"
            ],
            parameters={
                "language": ["javaScript", "python"],
                "code": "string"
            }
        )
        
        # Logic & Control Flow Nodes
        catalog["if"] = NodeCapability(
            node_type="n8n-nodes-base.if",
            category="logic",
            purpose="Conditional routing based on conditions",
            use_cases=[
                "Route data based on conditions",
                "Validate data and handle errors",
                "Priority-based routing",
                "Decision trees"
            ],
            parameters={
                "conditions": {
                    "boolean": "array of boolean conditions",
                    "number": "array of number conditions",
                    "string": "array of string conditions",
                    "dateTime": "array of date conditions"
                },
                "combineOperation": ["all", "any"]
            },
            common_combinations=[
                ["function", "if", "gmail"],
                ["webhook", "if", "database"],
                ["if", "slack", "email"]
            ]
        )
        
        catalog["switch"] = NodeCapability(
            node_type="n8n-nodes-base.switch",
            category="logic",
            purpose="Route data to different paths based on rules",
            use_cases=[
                "Multi-way branching",
                "Priority routing",
                "Category-based routing",
                "Complex decision logic"
            ],
            parameters={
                "mode": ["rules", "expression"],
                "rules": "array of routing rules",
                "fallbackOutput": "number"
            },
            common_combinations=[
                ["function", "switch", "multiple_actions"],
                ["webhook", "switch", "database"]
            ]
        )
        
        catalog["merge"] = NodeCapability(
            node_type="n8n-nodes-base.merge",
            category="logic",
            purpose="Merge data from multiple branches",
            use_cases=[
                "Combine data from parallel paths",
                "Join results from multiple sources",
                "Aggregate parallel operations"
            ],
            parameters={
                "mode": ["append", "mergeByIndex", "mergeByKey"],
                "joinMode": ["inner", "left", "outer"]
            }
        )
        
        # Loop & Batch Processing
        catalog["splitInBatches"] = NodeCapability(
            node_type="n8n-nodes-base.splitInBatches",
            category="loop",
            purpose="Process items in batches",
            use_cases=[
                "Rate limiting API calls",
                "Batch database operations",
                "Process large datasets",
                "Prevent timeouts"
            ],
            parameters={
                "batchSize": "number",
                "options": {
                    "reset": "boolean"
                }
            }
        )
        
        # Error Handling
        catalog["errorTrigger"] = NodeCapability(
            node_type="n8n-nodes-base.errorTrigger",
            category="error_handling",
            purpose="Trigger error workflow when any node fails",
            use_cases=[
                "Global error handling",
                "Error logging and alerts",
                "Retry logic",
                "Failure notifications"
            ],
            common_combinations=[
                ["errorTrigger", "function", "slack"],
                ["errorTrigger", "gmail", "database"]
            ]
        )
        
        # Communication Nodes
        catalog["gmail"] = NodeCapability(
            node_type="n8n-nodes-base.gmail",
            category="communication",
            purpose="Send and manage Gmail emails",
            use_cases=[
                "Send automated emails",
                "Email notifications",
                "Email marketing campaigns",
                "Support ticket responses"
            ],
            requires_credentials=True,
            credential_types=["gmailOAuth2"],
            parameters={
                "resource": ["message", "draft", "label"],
                "operation": ["send", "get", "getAll", "delete"],
                "sendTo": "string",
                "subject": "string",
                "message": "string"
            },
            common_combinations=[
                ["webhook", "set", "gmail"],
                ["schedule", "database", "gmail"],
                ["if", "gmail", "slack"]
            ]
        )
        
        catalog["slack"] = NodeCapability(
            node_type="n8n-nodes-base.slack",
            category="communication",
            purpose="Send messages to Slack",
            use_cases=[
                "Team notifications",
                "Alert systems",
                "Status updates",
                "Workflow completion notices"
            ],
            requires_credentials=True,
            credential_types=["slackApi"],
            parameters={
                "resource": ["message", "channel", "user"],
                "operation": ["post", "update", "delete"],
                "channel": "string",
                "text": "string"
            },
            common_combinations=[
                ["errorTrigger", "slack"],
                ["webhook", "function", "slack"],
                ["database", "slack"]
            ]
        )
        
        # Database Nodes
        catalog["postgres"] = NodeCapability(
            node_type="n8n-nodes-base.postgres",
            category="database",
            purpose="Execute PostgreSQL database operations",
            use_cases=[
                "Store workflow data",
                "Query databases",
                "Data synchronization",
                "Audit logs"
            ],
            requires_credentials=True,
            credential_types=["postgres"],
            parameters={
                "operation": ["executeQuery", "insert", "update", "delete"],
                "query": "string",
                "table": "string"
            },
            common_combinations=[
                ["webhook", "postgres", "gmail"],
                ["schedule", "postgres", "slack"],
                ["function", "postgres"]
            ]
        )
        
        catalog["mysql"] = NodeCapability(
            node_type="n8n-nodes-base.mysql",
            category="database",
            purpose="Execute MySQL database operations",
            use_cases=[
                "Store workflow data",
                "Query databases",
                "Data synchronization"
            ],
            requires_credentials=True,
            credential_types=["mysql"]
        )
        
        catalog["mongodb"] = NodeCapability(
            node_type="n8n-nodes-base.mongoDb",
            category="database",
            purpose="MongoDB database operations",
            use_cases=[
                "NoSQL data storage",
                "Document-based storage",
                "Flexible data structures"
            ],
            requires_credentials=True,
            credential_types=["mongoDb"]
        )
        
        # HTTP & API
        catalog["httpRequest"] = NodeCapability(
            node_type="n8n-nodes-base.httpRequest",
            category="api",
            purpose="Make HTTP requests to any API",
            use_cases=[
                "API integration",
                "Fetch external data",
                "Send data to services",
                "Custom integrations"
            ],
            parameters={
                "method": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                "url": "string",
                "authentication": ["none", "basicAuth", "oAuth1", "oAuth2", "apiKey"],
                "bodyParametersUi": "object"
            },
            common_combinations=[
                ["webhook", "httpRequest", "set"],
                ["schedule", "httpRequest", "database"],
                ["function", "httpRequest", "if"]
            ]
        )
        
        # Productivity Tools
        catalog["googleSheets"] = NodeCapability(
            node_type="n8n-nodes-base.googleSheets",
            category="productivity",
            purpose="Read and write Google Sheets data",
            use_cases=[
                "Data storage and retrieval",
                "Reporting and dashboards",
                "Data collection forms",
                "Simple databases"
            ],
            requires_credentials=True,
            credential_types=["googleSheetsOAuth2Api"],
            common_combinations=[
                ["webhook", "googleSheets"],
                ["schedule", "googleSheets", "gmail"]
            ]
        )
        
        return catalog
    
    def get_node(self, node_type: str) -> Optional[NodeCapability]:
        """Get node capability by type."""
        # Remove prefix if present
        clean_type = node_type.replace("n8n-nodes-base.", "")
        return self.nodes.get(clean_type)
    
    def get_by_category(self, category: str) -> List[NodeCapability]:
        """Get all nodes in a category."""
        return [
            node for node in self.nodes.values()
            if node.category == category
        ]
    
    def get_by_use_case(self, use_case_keyword: str) -> List[NodeCapability]:
        """Find nodes that match a use case keyword."""
        keyword_lower = use_case_keyword.lower()
        matching = []
        
        for node in self.nodes.values():
            if any(keyword_lower in uc.lower() for uc in node.use_cases):
                matching.append(node)
            elif keyword_lower in node.purpose.lower():
                matching.append(node)
        
        return matching
    
    def find_best_nodes_for_request(self, request: str) -> List[NodeCapability]:
        """Find the best nodes for a user request."""
        request_lower = request.lower()
        scored_nodes = []
        
        for node in self.nodes.values():
            score = 0
            
            # Check purpose
            if any(word in node.purpose.lower() for word in request_lower.split()):
                score += 2
            
            # Check use cases
            for use_case in node.use_cases:
                if any(word in use_case.lower() for word in request_lower.split()):
                    score += 1
            
            # Check category
            if node.category in request_lower:
                score += 1
            
            if score > 0:
                scored_nodes.append((score, node))
        
        # Sort by score
        scored_nodes.sort(reverse=True, key=lambda x: x[0])
        
        return [node for score, node in scored_nodes[:10]]
    
    def get_common_patterns(self) -> Dict[str, List[str]]:
        """Get common node combination patterns."""
        patterns = {}
        
        for node_name, node in self.nodes.items():
            if node.common_combinations:
                patterns[node_name] = node.common_combinations
        
        return patterns
    
    def to_json(self) -> str:
        """Convert catalog to JSON."""
        catalog_dict = {
            name: node.to_dict()
            for name, node in self.nodes.items()
        }
        return json.dumps(catalog_dict, indent=2)
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(node.category for node in self.nodes.values()))


# Global instance
_catalog_instance = None

def get_node_catalog() -> NodeCatalog:
    """Get singleton instance of node catalog."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = NodeCatalog()
    return _catalog_instance

