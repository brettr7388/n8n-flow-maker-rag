"""
Pattern Library for common n8n workflow patterns.
Reusable workflow patterns that can be composed into complex workflows.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class WorkflowPattern:
    """Represents a reusable workflow pattern."""
    
    name: str
    description: str
    complexity_score: int
    when_to_use: List[str]
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    required_inputs: List[str] = field(default_factory=list)
    provides_outputs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "complexity_score": self.complexity_score,
            "when_to_use": self.when_to_use,
            "nodes": self.nodes,
            "connections": self.connections,
            "required_inputs": self.required_inputs,
            "provides_outputs": self.provides_outputs
        }


class PatternLibrary:
    """Library of reusable workflow patterns."""
    
    def __init__(self):
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, WorkflowPattern]:
        """Build library of workflow patterns."""
        patterns = {}
        
        # Pattern 1: Data Validation with Error Handling
        patterns["data_validation"] = WorkflowPattern(
            name="Data Validation with Error Handling",
            description="Validates incoming data and routes invalid items to error handler",
            complexity_score=3,
            when_to_use=[
                "Webhook inputs",
                "User-submitted data",
                "External API responses",
                "Form submissions"
            ],
            required_inputs=["data_to_validate"],
            provides_outputs=["validated_data", "validation_errors"],
            nodes=[
                {
                    "name": "Validate Data",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """// Validate incoming data
const item = $input.item.json;
const errors = [];

// Required fields check
const requiredFields = ['email', 'name'];
for (const field of requiredFields) {
  if (!item[field] || item[field].trim() === '') {
    errors.push(`Missing required field: ${field}`);
  }
}

// Email validation
if (item.email && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(item.email)) {
  errors.push('Invalid email format');
}

// Phone validation (if provided)
if (item.phone && !/^[\\d\\s\\-\\+\\(\\)]+$/.test(item.phone)) {
  errors.push('Invalid phone format');
}

return {
  ...item,
  validation: {
    is_valid: errors.length === 0,
    errors: errors,
    validated_at: new Date().toISOString()
  }
};"""
                    }
                },
                {
                    "name": "Is Valid?",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "boolean": [{
                                "value1": "={{$json.validation.is_valid}}",
                                "value2": True
                            }]
                        }
                    }
                },
                {
                    "name": "Log Validation Error",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """console.error('Validation failed:', $json.validation.errors);
return {
  error_type: 'validation_failed',
  data: $json,
  errors: $json.validation.errors,
  timestamp: new Date().toISOString()
};"""
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 2: Duplicate Check
        patterns["duplicate_check"] = WorkflowPattern(
            name="Duplicate Check in Database",
            description="Checks if a record already exists in database before processing",
            complexity_score=3,
            when_to_use=[
                "Prevent duplicate leads",
                "Avoid duplicate records",
                "Idempotent operations",
                "Data deduplication"
            ],
            required_inputs=["unique_field", "database_connection"],
            provides_outputs=["is_duplicate", "existing_record"],
            nodes=[
                {
                    "name": "Check for Duplicate",
                    "type": "n8n-nodes-base.postgres",
                    "parameters": {
                        "operation": "executeQuery",
                        "query": "SELECT * FROM {{$json.table}} WHERE {{$json.unique_field}} = $1 LIMIT 1",
                        "additionalFields": {
                            "queryParameters": "={{$json.unique_value}}"
                        }
                    }
                },
                {
                    "name": "Is New Record?",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "number": [{
                                "value1": "={{$json.length}}",
                                "operation": "equal",
                                "value2": 0
                            }]
                        }
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 3: Lead Scoring
        patterns["lead_scoring"] = WorkflowPattern(
            name="Lead Scoring Logic",
            description="Scores leads based on multiple criteria",
            complexity_score=2,
            when_to_use=[
                "Sales automation",
                "Lead qualification",
                "Priority routing",
                "Marketing automation"
            ],
            required_inputs=["lead_data"],
            provides_outputs=["lead_score", "priority_level"],
            nodes=[
                {
                    "name": "Calculate Lead Score",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """// Lead scoring algorithm
const lead = $input.item.json;
let score = 0;

// Company size scoring
if (lead.company_size) {
  if (lead.company_size > 1000) score += 40;
  else if (lead.company_size > 100) score += 30;
  else if (lead.company_size > 10) score += 20;
  else score += 10;
}

// Budget scoring
if (lead.budget) {
  if (lead.budget > 100000) score += 30;
  else if (lead.budget > 10000) score += 20;
  else if (lead.budget > 1000) score += 10;
}

// Industry scoring
const highValueIndustries = ['technology', 'finance', 'healthcare'];
if (highValueIndustries.includes(lead.industry?.toLowerCase())) {
  score += 15;
}

// Engagement scoring
if (lead.visited_pricing_page) score += 10;
if (lead.downloaded_whitepaper) score += 5;
if (lead.requested_demo) score += 20;

// Determine priority level
let priority = 'low';
if (score >= 80) priority = 'high';
else if (score >= 50) priority = 'medium';

return {
  ...lead,
  score: score,
  priority: priority,
  scored_at: new Date().toISOString()
};"""
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 4: Priority Routing
        patterns["priority_routing"] = WorkflowPattern(
            name="Priority-Based Routing",
            description="Routes items to different paths based on priority/score",
            complexity_score=4,
            when_to_use=[
                "Lead distribution",
                "Support ticket routing",
                "Order processing",
                "Multi-tier workflows"
            ],
            required_inputs=["score_field"],
            provides_outputs=["routed_items"],
            nodes=[
                {
                    "name": "Route by Priority",
                    "type": "n8n-nodes-base.switch",
                    "parameters": {
                        "mode": "rules",
                        "rules": {
                            "rules": [
                                {
                                    "value1": "={{$json.score}}",
                                    "operation": "largerEqual",
                                    "value2": 80,
                                    "output": 0
                                },
                                {
                                    "value1": "={{$json.score}}",
                                    "operation": "largerEqual",
                                    "value2": 50,
                                    "output": 1
                                }
                            ]
                        },
                        "fallbackOutput": 2
                    }
                },
                {
                    "name": "High Priority Handler",
                    "type": "n8n-nodes-base.set",
                    "parameters": {
                        "values": {
                            "string": [{
                                "name": "priority_level",
                                "value": "high"
                            }]
                        }
                    }
                },
                {
                    "name": "Medium Priority Handler",
                    "type": "n8n-nodes-base.set",
                    "parameters": {
                        "values": {
                            "string": [{
                                "name": "priority_level",
                                "value": "medium"
                            }]
                        }
                    }
                },
                {
                    "name": "Low Priority Handler",
                    "type": "n8n-nodes-base.set",
                    "parameters": {
                        "values": {
                            "string": [{
                                "name": "priority_level",
                                "value": "low"
                            }]
                        }
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 5: Error Handling with Retry
        patterns["error_retry"] = WorkflowPattern(
            name="Error Handling with Exponential Backoff",
            description="Retries failed operations with increasing delays",
            complexity_score=5,
            when_to_use=[
                "Unreliable external APIs",
                "Network operations",
                "Rate-limited services",
                "Transient failures"
            ],
            required_inputs=[],
            provides_outputs=["retry_count", "final_status"],
            nodes=[
                {
                    "name": "Error Trigger",
                    "type": "n8n-nodes-base.errorTrigger",
                    "parameters": {}
                },
                {
                    "name": "Retry Logic",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """// Exponential backoff retry logic
const error = $input.item.json;
const retryCount = error.retryCount || 0;
const maxRetries = 3;

if (retryCount >= maxRetries) {
  return {
    ...error,
    retryCount: retryCount,
    status: 'max_retries_exceeded',
    message: 'Failed after maximum retries'
  };
}

// Calculate backoff delay (exponential)
const backoffMs = Math.pow(2, retryCount) * 1000;

return {
  ...error,
  retryCount: retryCount + 1,
  nextRetryDelay: backoffMs,
  shouldRetry: true,
  retryAt: new Date(Date.now() + backoffMs).toISOString()
};"""
                    }
                },
                {
                    "name": "Should Retry?",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "boolean": [{
                                "value1": "={{$json.shouldRetry}}",
                                "value2": True
                            }]
                        }
                    }
                },
                {
                    "name": "Wait Before Retry",
                    "type": "n8n-nodes-base.wait",
                    "parameters": {
                        "unit": "ms",
                        "amount": "={{$json.nextRetryDelay}}"
                    }
                },
                {
                    "name": "Alert Admin",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """return {
  alert_type: 'max_retries_exceeded',
  workflow_id: $workflow.id,
  execution_id: $execution.id,
  error_details: $json,
  timestamp: new Date().toISOString()
};"""
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 6: Batch Processing
        patterns["batch_processing"] = WorkflowPattern(
            name="Batch Processing with Rate Limiting",
            description="Processes large datasets in batches to avoid timeouts",
            complexity_score=4,
            when_to_use=[
                "Large data imports",
                "API rate limiting",
                "Bulk operations",
                "Memory management"
            ],
            required_inputs=["items_to_process"],
            provides_outputs=["processed_batches"],
            nodes=[
                {
                    "name": "Split Into Batches",
                    "type": "n8n-nodes-base.splitInBatches",
                    "parameters": {
                        "batchSize": 10,
                        "options": {
                            "reset": False
                        }
                    }
                },
                {
                    "name": "Process Batch",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """// Process current batch
const items = $input.all();
const processedItems = items.map(item => {
  // Your processing logic here
  return {
    ...item.json,
    processed: true,
    processed_at: new Date().toISOString()
  };
});

return processedItems;"""
                    }
                },
                {
                    "name": "Rate Limit Delay",
                    "type": "n8n-nodes-base.wait",
                    "parameters": {
                        "unit": "seconds",
                        "amount": 1
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 7: API Pagination
        patterns["api_pagination"] = WorkflowPattern(
            name="API Pagination Handler",
            description="Handles paginated API responses automatically",
            complexity_score=5,
            when_to_use=[
                "External API integration",
                "Large dataset retrieval",
                "Multi-page results"
            ],
            required_inputs=["api_endpoint", "page_size"],
            provides_outputs=["all_results"],
            nodes=[
                {
                    "name": "Initialize Pagination",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """return {
  page: 1,
  hasMore: true,
  allResults: []
};"""
                    }
                },
                {
                    "name": "Fetch Page",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "method": "GET",
                        "url": "={{$json.api_url}}&page={{$json.page}}",
                        "authentication": "predefinedCredentialType"
                    }
                },
                {
                    "name": "Check for More Pages",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """const response = $input.item.json;
const prevData = $input.all()[0].json;

// Accumulate results
const allResults = [...(prevData.allResults || []), ...response.data];

// Check if there are more pages
const hasMore = response.data.length > 0 && response.hasNextPage !== false;

return {
  page: prevData.page + 1,
  hasMore: hasMore,
  allResults: allResults,
  totalFetched: allResults.length
};"""
                    }
                },
                {
                    "name": "Has More Pages?",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "boolean": [{
                                "value1": "={{$json.hasMore}}",
                                "value2": True
                            }]
                        }
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 8: Email Template Selection
        patterns["email_template_selection"] = WorkflowPattern(
            name="Dynamic Email Template Selection",
            description="Selects and personalizes email templates based on data",
            complexity_score=3,
            when_to_use=[
                "Email automation",
                "Personalized campaigns",
                "Multi-template workflows",
                "Dynamic content"
            ],
            required_inputs=["template_type", "recipient_data"],
            provides_outputs=["personalized_email"],
            nodes=[
                {
                    "name": "Select Template",
                    "type": "n8n-nodes-base.switch",
                    "parameters": {
                        "mode": "expression",
                        "output": "={{$json.template_type}}"
                    }
                },
                {
                    "name": "High Priority Template",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """const data = $input.item.json;
return {
  subject: `Urgent: ${data.subject}`,
  body: `Dear ${data.name},\\n\\nThis is a high-priority matter...`,
  ...data
};"""
                    }
                },
                {
                    "name": "Standard Template",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """const data = $input.item.json;
return {
  subject: `Hello ${data.name}`,
  body: `Hi ${data.name},\\n\\nThank you for your interest...`,
  ...data
};"""
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 9: Webhook Authentication
        patterns["webhook_auth"] = WorkflowPattern(
            name="Webhook API Key Authentication",
            description="Validates API key for webhook security",
            complexity_score=2,
            when_to_use=[
                "Secure webhooks",
                "API authentication",
                "Access control"
            ],
            required_inputs=["api_key"],
            provides_outputs=["is_authenticated"],
            nodes=[
                {
                    "name": "Validate API Key",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """// Extract API key from headers
const providedKey = $input.item.json.headers?.['x-api-key'] || 
                     $input.item.json.headers?.['authorization']?.replace('Bearer ', '');

// Validate against stored keys (use environment variable in production)
const validKeys = (process.env.VALID_API_KEYS || '').split(',');

const isValid = validKeys.includes(providedKey);

if (!isValid) {
  throw new Error('Invalid API key');
}

return {
  ...$input.item.json,
  authenticated: true,
  api_key_valid: true
};"""
                    }
                }
            ],
            connections={}
        )
        
        # Pattern 10: Logging and Audit Trail
        patterns["audit_logging"] = WorkflowPattern(
            name="Comprehensive Audit Logging",
            description="Logs workflow execution details for audit trail",
            complexity_score=2,
            when_to_use=[
                "Compliance requirements",
                "Debugging",
                "Monitoring",
                "Analytics"
            ],
            required_inputs=["workflow_data"],
            provides_outputs=["log_entry"],
            nodes=[
                {
                    "name": "Create Log Entry",
                    "type": "n8n-nodes-base.function",
                    "parameters": {
                        "functionCode": """return {
  workflow_id: $workflow.id,
  workflow_name: $workflow.name,
  execution_id: $execution.id,
  execution_mode: $execution.mode,
  timestamp: new Date().toISOString(),
  data: $input.item.json,
  node_name: $node.name,
  success: true
};"""
                    }
                },
                {
                    "name": "Store Log",
                    "type": "n8n-nodes-base.postgres",
                    "parameters": {
                        "operation": "insert",
                        "table": "workflow_audit_log"
                    }
                }
            ],
            connections={}
        )
        
        return patterns
    
    def get_pattern(self, pattern_name: str) -> Optional[WorkflowPattern]:
        """Get a specific pattern by name."""
        return self.patterns.get(pattern_name)
    
    def find_patterns_for_request(self, request: str) -> List[WorkflowPattern]:
        """Find relevant patterns based on user request."""
        request_lower = request.lower()
        scored_patterns = []
        
        for pattern in self.patterns.values():
            score = 0
            
            # Check description
            if any(word in pattern.description.lower() for word in request_lower.split()):
                score += 2
            
            # Check when_to_use
            for use_case in pattern.when_to_use:
                if any(word in use_case.lower() for word in request_lower.split()):
                    score += 3
            
            if score > 0:
                scored_patterns.append((score, pattern))
        
        # Sort by score
        scored_patterns.sort(reverse=True, key=lambda x: x[0])
        
        return [pattern for score, pattern in scored_patterns]
    
    def get_all_patterns(self) -> List[WorkflowPattern]:
        """Get all patterns."""
        return list(self.patterns.values())


# Global instance
_library_instance = None

def get_pattern_library() -> PatternLibrary:
    """Get singleton instance of pattern library."""
    global _library_instance
    if _library_instance is None:
        _library_instance = PatternLibrary()
    return _library_instance

