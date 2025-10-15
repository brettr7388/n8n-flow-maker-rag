"""
Enhanced Workflow Generator.
Generates complex, production-ready n8n workflows with 10+ nodes.
"""

from typing import Dict, List, Any, Optional, Tuple
import uuid
from .node_catalog import get_node_catalog, NodeCapability
from .pattern_library import get_pattern_library, WorkflowPattern
from .conversation_manager import ConversationState


class WorkflowGenerator:
    """Generates complex n8n workflows based on requirements."""
    
    def __init__(self):
        self.node_catalog = get_node_catalog()
        self.pattern_library = get_pattern_library()
        self.position_x = 240
        self.position_y = 300
        self.spacing_x = 220
        self.spacing_y = 150
    
    def calculate_complexity(self, requirements: Dict[str, Any]) -> int:
        """
        Calculate workflow complexity score (1-10).
        
        Based on:
        - Trigger complexity
        - Data validation needs
        - Conditional logic
        - Error handling
        - Number of integrations
        - Number of outputs
        """
        complexity = 1
        
        # Trigger complexity
        if requirements.get("trigger") == "webhook":
            complexity += 1
        if requirements.get("needs_auth"):
            complexity += 1
        
        # Data processing
        if requirements.get("needs_validation"):
            complexity += 2
        if requirements.get("needs_duplicate_check"):
            complexity += 2
        if requirements.get("needs_transformation"):
            complexity += 1
        if requirements.get("needs_scoring"):
            complexity += 2
        
        # Logic complexity
        if requirements.get("has_branching"):
            complexity += 2
        if requirements.get("has_loops"):
            complexity += 3
        
        # Error handling
        if requirements.get("needs_error_handling"):
            complexity += 2
        if requirements.get("needs_retry_logic"):
            complexity += 2
        
        # Integrations and outputs
        num_outputs = requirements.get("num_outputs", 1)
        complexity += num_outputs
        
        return min(complexity, 10)
    
    def generate(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete workflow from requirements.
        
        Args:
            requirements: Dictionary of workflow requirements
            conversation: Optional conversation state for context
            
        Returns:
            Complete n8n workflow JSON
        """
        nodes = []
        connections = {}
        position = [self.position_x, self.position_y]
        
        # Calculate complexity
        complexity = self.calculate_complexity(requirements)
        
        # 1. Add trigger node
        trigger_node, position = self._create_trigger_node(requirements, position)
        nodes.append(trigger_node)
        last_node = trigger_node
        
        # 2. Add authentication if needed
        if requirements.get("needs_auth"):
            auth_node, position = self._create_auth_node(position)
            nodes.append(auth_node)
            self._connect_nodes(connections, last_node, auth_node)
            last_node = auth_node
        
        # 3. Add data validation flow
        if requirements.get("needs_validation"):
            validation_nodes, validation_conns, position, success_node, error_node = \
                self._create_validation_flow(position)
            nodes.extend(validation_nodes)
            self._merge_connections(connections, validation_conns)
            self._connect_nodes(connections, last_node, validation_nodes[0])
            last_node = success_node
        
        # 4. Add duplicate check
        if requirements.get("needs_duplicate_check"):
            dup_nodes, dup_conns, position, new_node = \
                self._create_duplicate_check_flow(requirements, position)
            nodes.extend(dup_nodes)
            self._merge_connections(connections, dup_conns)
            self._connect_nodes(connections, last_node, dup_nodes[0])
            last_node = new_node
        
        # 5. Add data transformation/scoring
        if requirements.get("needs_scoring"):
            scoring_node, position = self._create_scoring_node(position)
            nodes.append(scoring_node)
            self._connect_nodes(connections, last_node, scoring_node)
            last_node = scoring_node
        
        # 6. Add branching logic if needed
        if requirements.get("has_branching") or complexity > 6:
            branch_nodes, branch_conns, position, merge_node = \
                self._create_branching_flow(requirements, position)
            nodes.extend(branch_nodes)
            self._merge_connections(connections, branch_conns)
            self._connect_nodes(connections, last_node, branch_nodes[0])
            last_node = merge_node
        
        # 7. Add action nodes (outputs)
        action_nodes, action_conns, position = \
            self._create_action_nodes(requirements, position)
        nodes.append(action_nodes)
        self._merge_connections(connections, action_conns)
        self._connect_nodes(connections, last_node, action_nodes)
        last_node = action_nodes
        
        # 8. Add logging if needed
        if requirements.get("needs_logging") or complexity > 5:
            log_node, position = self._create_logging_node(requirements, position)
            nodes.append(log_node)
            self._connect_nodes(connections, last_node, log_node)
            last_node = log_node
        
        # 9. Add notification nodes
        if requirements.get("needs_notification"):
            notif_nodes, notif_conns, position = \
                self._create_notification_nodes(requirements, position)
            nodes.extend(notif_nodes)
            self._merge_connections(connections, notif_conns)
            self._connect_nodes(connections, last_node, notif_nodes[0])
        
        # 10. Add error handling workflow
        if requirements.get("needs_error_handling"):
            error_nodes, error_conns = self._create_error_workflow(requirements)
            nodes.extend(error_nodes)
            self._merge_connections(connections, error_conns)
        
        # Generate workflow name
        workflow_name = self._generate_workflow_name(requirements, conversation)
        
        return {
            "name": workflow_name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {
                "executionOrder": "v1"
            },
            "meta": {
                "generatedBy": "n8n-flow-generator",
                "version": "2.0",
                "complexity": complexity,
                "nodeCount": len(nodes)
            }
        }
    
    def _create_trigger_node(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[Dict[str, Any], List[int]]:
        """Create appropriate trigger node."""
        trigger_type = requirements.get("trigger", "webhook")
        node_id = str(uuid.uuid4())
        
        if trigger_type == "webhook":
            node = {
                "id": node_id,
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": position.copy(),
                "webhookId": str(uuid.uuid4()),
                "parameters": {
                    "httpMethod": "POST",
                    "path": requirements.get("webhook_path", "workflow-trigger"),
                    "responseMode": "onReceived",
                    "options": {}
                }
            }
        elif trigger_type == "schedule":
            schedule_freq = requirements.get("schedule_frequency", "hour")
            node = {
                "id": node_id,
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "field": schedule_freq
                            }
                        ]
                    }
                }
            }
        elif trigger_type == "email":
            node = {
                "id": node_id,
                "name": "Email Trigger",
                "type": "n8n-nodes-base.emailReadImap",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "mailbox": "INBOX",
                    "options": {
                        "allowUnauthorizedCerts": False
                    }
                },
                "credentials": {
                    "imap": {
                        "id": "1",
                        "name": "IMAP Account (to be configured)"
                    }
                }
            }
        else:
            # Manual trigger
            node = {
                "id": node_id,
                "name": "Manual Trigger",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {}
            }
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return node, new_position
    
    def _create_auth_node(self, position: List[int]) -> Tuple[Dict[str, Any], List[int]]:
        """Create authentication validation node."""
        node = {
            "id": str(uuid.uuid4()),
            "name": "Validate API Key",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "functionCode": """// Validate API key from header
const providedKey = $input.item.json.headers?.['x-api-key'] || 
                     $input.item.json.headers?.['authorization']?.replace('Bearer ', '');

// Get valid keys from environment variable
const validKeys = (process.env.VALID_API_KEYS || 'your-api-key-here').split(',');

if (!validKeys.includes(providedKey)) {
  throw new Error('Invalid or missing API key');
}

return {
  ...$input.item.json,
  authenticated: true,
  timestamp: new Date().toISOString()
};"""
            }
        }
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return node, new_position
    
    def _create_validation_flow(
        self,
        position: List[int]
    ) -> Tuple[List[Dict], Dict, List[int], Dict, Dict]:
        """Create data validation flow with error handling."""
        nodes = []
        connections = {}
        
        # Validation function node
        validate_node = {
            "id": str(uuid.uuid4()),
            "name": "Validate Data",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "functionCode": """// Comprehensive data validation
const item = $input.item.json;
const errors = [];

// Required fields
const requiredFields = ['email', 'name'];
for (const field of requiredFields) {
  if (!item[field] || String(item[field]).trim() === '') {
    errors.push(`Missing required field: ${field}`);
  }
}

// Email format validation
if (item.email && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(item.email)) {
  errors.push('Invalid email format');
}

// Phone validation (if provided)
if (item.phone && item.phone.trim() && !/^[\\d\\s\\-\\+\\(\\)]+$/.test(item.phone)) {
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
        }
        nodes.append(validate_node)
        
        # IF node for branching
        position[0] += self.spacing_x
        if_node = {
            "id": str(uuid.uuid4()),
            "name": "Is Valid?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "conditions": {
                    "boolean": [{
                        "value1": "={{$json.validation.is_valid}}",
                        "value2": True
                    }]
                }
            }
        }
        nodes.append(if_node)
        
        # Connect validation to IF
        self._connect_nodes(connections, validate_node, if_node)
        
        # Error logging node (below main path)
        error_position = [position[0] + self.spacing_x, position[1] + self.spacing_y]
        error_node = {
            "id": str(uuid.uuid4()),
            "name": "Log Validation Error",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": error_position,
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
        nodes.append(error_node)
        
        # Connect IF false branch to error
        if_name = if_node["name"]
        if if_name not in connections:
            connections[if_name] = {"main": [[], []]}
        connections[if_name]["main"][1] = [{
            "node": error_node["name"],
            "type": "main",
            "index": 0
        }]
        
        # Update position for next node
        new_position = [position[0] + self.spacing_x, position[1]]
        
        return nodes, connections, new_position, if_node, error_node
    
    def _create_duplicate_check_flow(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[List[Dict], Dict, List[int], Dict]:
        """Create duplicate checking flow."""
        nodes = []
        connections = {}
        
        database = requirements.get("database", "postgres")
        
        # Database query node
        check_node = {
            "id": str(uuid.uuid4()),
            "name": "Check for Duplicates",
            "type": f"n8n-nodes-base.{database}",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "operation": "executeQuery",
                "query": "SELECT id FROM records WHERE email = $1 LIMIT 1",
                "additionalFields": {
                    "queryParameters": "={{$json.email}}"
                }
            },
            "credentials": {
                database: {
                    "id": "1",
                    "name": f"{database.title()} Database (to be configured)"
                }
            }
        }
        nodes.append(check_node)
        
        # IF node to check if new
        position[0] += self.spacing_x
        if_node = {
            "id": str(uuid.uuid4()),
            "name": "Is New Record?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "conditions": {
                    "number": [{
                        "value1": "={{$json.length || 0}}",
                        "operation": "equal",
                        "value2": 0
                    }]
                }
            }
        }
        nodes.append(if_node)
        
        self._connect_nodes(connections, check_node, if_node)
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return nodes, connections, new_position, if_node
    
    def _create_scoring_node(
        self,
        position: List[int]
    ) -> Tuple[Dict[str, Any], List[int]]:
        """Create lead/data scoring node."""
        node = {
            "id": str(uuid.uuid4()),
            "name": "Calculate Score",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "functionCode": """// Scoring algorithm
const item = $input.item.json;
let score = 0;

// Company size scoring
if (item.company_size) {
  if (item.company_size > 1000) score += 40;
  else if (item.company_size > 100) score += 30;
  else if (item.company_size > 10) score += 20;
  else score += 10;
}

// Budget scoring
if (item.budget) {
  if (item.budget > 100000) score += 30;
  else if (item.budget > 10000) score += 20;
  else if (item.budget > 1000) score += 10;
}

// Industry scoring
const highValueIndustries = ['technology', 'finance', 'healthcare'];
if (highValueIndustries.includes(item.industry?.toLowerCase())) {
  score += 15;
}

// Determine priority
let priority = 'low';
if (score >= 80) priority = 'high';
else if (score >= 50) priority = 'medium';

return {
  ...item,
  score: score,
  priority: priority,
  scored_at: new Date().toISOString()
};"""
            }
        }
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return node, new_position
    
    def _create_branching_flow(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[List[Dict], Dict, List[int], Dict]:
        """Create branching flow based on conditions."""
        nodes = []
        connections = {}
        
        # Switch node for routing
        switch_node = {
            "id": str(uuid.uuid4()),
            "name": "Route by Priority",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 1,
            "position": position.copy(),
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
        }
        nodes.append(switch_node)
        
        # High priority path
        high_pos = [position[0] + self.spacing_x, position[1] - self.spacing_y]
        high_node = {
            "id": str(uuid.uuid4()),
            "name": "High Priority Processing",
            "type": "n8n-nodes-base.set",
            "typeVersion": 1,
            "position": high_pos,
            "parameters": {
                "values": {
                    "string": [
                        {
                            "name": "priority_level",
                            "value": "high"
                        },
                        {
                            "name": "processing_speed",
                            "value": "immediate"
                        }
                    ]
                }
            }
        }
        nodes.append(high_node)
        
        # Medium priority path
        med_pos = [position[0] + self.spacing_x, position[1]]
        med_node = {
            "id": str(uuid.uuid4()),
            "name": "Medium Priority Processing",
            "type": "n8n-nodes-base.set",
            "typeVersion": 1,
            "position": med_pos,
            "parameters": {
                "values": {
                    "string": [
                        {
                            "name": "priority_level",
                            "value": "medium"
                        },
                        {
                            "name": "processing_speed",
                            "value": "standard"
                        }
                    ]
                }
            }
        }
        nodes.append(med_node)
        
        # Low priority path
        low_pos = [position[0] + self.spacing_x, position[1] + self.spacing_y]
        low_node = {
            "id": str(uuid.uuid4()),
            "name": "Low Priority Processing",
            "type": "n8n-nodes-base.set",
            "typeVersion": 1,
            "position": low_pos,
            "parameters": {
                "values": {
                    "string": [
                        {
                            "name": "priority_level",
                            "value": "low"
                        },
                        {
                            "name": "processing_speed",
                            "value": "batched"
                        }
                    ]
                }
            }
        }
        nodes.append(low_node)
        
        # Connect switch to paths
        switch_name = switch_node["name"]
        connections[switch_name] = {
            "main": [
                [{"node": high_node["name"], "type": "main", "index": 0}],
                [{"node": med_node["name"], "type": "main", "index": 0}],
                [{"node": low_node["name"], "type": "main", "index": 0}]
            ]
        }
        
        # Merge node
        merge_pos = [position[0] + self.spacing_x * 2, position[1]]
        merge_node = {
            "id": str(uuid.uuid4()),
            "name": "Merge Paths",
            "type": "n8n-nodes-base.merge",
            "typeVersion": 1,
            "position": merge_pos,
            "parameters": {
                "mode": "append"
            }
        }
        nodes.append(merge_node)
        
        # Connect all paths to merge
        for path_node in [high_node, med_node, low_node]:
            self._connect_nodes(connections, path_node, merge_node)
        
        new_position = [merge_pos[0] + self.spacing_x, position[1]]
        return nodes, connections, new_position, merge_node
    
    def _create_action_nodes(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[Dict[str, Any], Dict, List[int]]:
        """Create main action node(s)."""
        outputs = requirements.get("outputs", ["email"])
        primary_output = outputs[0] if outputs else "email"
        
        if primary_output == "email":
            node = {
                "id": str(uuid.uuid4()),
                "name": "Send Email",
                "type": "n8n-nodes-base.gmail",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "resource": "message",
                    "operation": "send",
                    "sendTo": "={{$json.email}}",
                    "subject": "={{$json.subject || 'Workflow Notification'}}",
                    "message": "={{$json.body || $json.message}}"
                },
                "credentials": {
                    "gmailOAuth2": {
                        "id": "1",
                        "name": "Gmail account (to be configured)"
                    }
                }
            }
        elif primary_output == "slack":
            node = {
                "id": str(uuid.uuid4()),
                "name": "Post to Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "resource": "message",
                    "operation": "post",
                    "channel": "#general",
                    "text": "={{$json.message}}"
                },
                "credentials": {
                    "slackApi": {
                        "id": "2",
                        "name": "Slack API (to be configured)"
                    }
                }
            }
        elif primary_output == "database":
            database = requirements.get("database", "postgres")
            node = {
                "id": str(uuid.uuid4()),
                "name": "Save to Database",
                "type": f"n8n-nodes-base.{database}",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "operation": "insert",
                    "table": "workflow_results"
                },
                "credentials": {
                    database: {
                        "id": "1",
                        "name": f"{database.title()} (to be configured)"
                    }
                }
            }
        else:
            # Default to HTTP request
            node = {
                "id": str(uuid.uuid4()),
                "name": "Send to Webhook",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "method": "POST",
                    "url": "={{$json.webhook_url}}",
                    "options": {}
                }
            }
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return node, {}, new_position
    
    def _create_logging_node(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[Dict[str, Any], List[int]]:
        """Create logging node for audit trail."""
        database = requirements.get("database", "postgres")
        
        node = {
            "id": str(uuid.uuid4()),
            "name": "Log to Database",
            "type": f"n8n-nodes-base.{database}",
            "typeVersion": 1,
            "position": position.copy(),
            "parameters": {
                "operation": "insert",
                "table": "workflow_logs",
                "columns": "workflow_id,execution_id,data,timestamp",
                "additionalFields": {}
            },
            "credentials": {
                database: {
                    "id": "1",
                    "name": f"{database.title()} (to be configured)"
                }
            }
        }
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return node, new_position
    
    def _create_notification_nodes(
        self,
        requirements: Dict[str, Any],
        position: List[int]
    ) -> Tuple[List[Dict], Dict, List[int]]:
        """Create notification nodes."""
        nodes = []
        connections = {}
        
        outputs = requirements.get("outputs", [])
        
        if "slack" in outputs or "notification" in requirements.get("needs_notification", "").lower():
            slack_node = {
                "id": str(uuid.uuid4()),
                "name": "Notify Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 1,
                "position": position.copy(),
                "parameters": {
                    "resource": "message",
                    "operation": "post",
                    "channel": "#notifications",
                    "text": "✅ Workflow completed successfully for: {{$json.name || $json.email}}"
                },
                "credentials": {
                    "slackApi": {
                        "id": "2",
                        "name": "Slack API (to be configured)"
                    }
                }
            }
            nodes.append(slack_node)
        
        new_position = [position[0] + self.spacing_x, position[1]]
        return nodes, connections, new_position
    
    def _create_error_workflow(
        self,
        requirements: Dict[str, Any]
    ) -> Tuple[List[Dict], Dict]:
        """Create error handling workflow."""
        nodes = []
        connections = {}
        
        # Error trigger (positioned below main workflow)
        error_trigger = {
            "id": str(uuid.uuid4()),
            "name": "Error Trigger",
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [self.position_x, self.position_y + 400],
            "parameters": {}
        }
        nodes.append(error_trigger)
        
        # Log error
        log_error = {
            "id": str(uuid.uuid4()),
            "name": "Log Error Details",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [self.position_x + self.spacing_x, self.position_y + 400],
            "parameters": {
                "functionCode": """const error = $input.item.json;
return {
  workflow_id: $workflow.id,
  execution_id: $execution.id,
  node_name: error.node?.name,
  error_message: error.error?.message,
  error_stack: error.error?.stack,
  timestamp: new Date().toISOString(),
  input_data: error.itemIndex !== undefined ? 
    $input.all()[error.itemIndex]?.json : null
};"""
            }
        }
        nodes.append(log_error)
        
        self._connect_nodes(connections, error_trigger, log_error)
        
        # Send alert
        if requirements.get("needs_error_alerts"):
            alert_node = {
                "id": str(uuid.uuid4()),
                "name": "Alert Admin",
                "type": "n8n-nodes-base.gmail",
                "typeVersion": 1,
                "position": [self.position_x + self.spacing_x * 2, self.position_y + 400],
                "parameters": {
                    "resource": "message",
                    "operation": "send",
                    "sendTo": "admin@company.com",
                    "subject": "🚨 Workflow Error Alert",
                    "message": "Error in workflow {{$json.workflow_id}}: {{$json.error_message}}"
                },
                "credentials": {
                    "gmailOAuth2": {
                        "id": "1",
                        "name": "Gmail account (to be configured)"
                    }
                }
            }
            nodes.append(alert_node)
            self._connect_nodes(connections, log_error, alert_node)
        
        return nodes, connections
    
    def _connect_nodes(
        self,
        connections: Dict,
        from_node: Dict,
        to_node: Dict,
        output_index: int = 0
    ):
        """Connect two nodes."""
        from_name = from_node["name"]
        to_name = to_node["name"]
        
        if from_name not in connections:
            connections[from_name] = {"main": [[]]}
        
        # Ensure we have enough output arrays
        while len(connections[from_name]["main"]) <= output_index:
            connections[from_name]["main"].append([])
        
        connections[from_name]["main"][output_index].append({
            "node": to_name,
            "type": "main",
            "index": 0
        })
    
    def _merge_connections(self, target: Dict, source: Dict):
        """Merge source connections into target."""
        for node_name, conn_data in source.items():
            if node_name not in target:
                target[node_name] = conn_data
            else:
                # Merge connection arrays
                for conn_type, conn_list in conn_data.items():
                    if conn_type not in target[node_name]:
                        target[node_name][conn_type] = conn_list
                    else:
                        for i, connections in enumerate(conn_list):
                            if i >= len(target[node_name][conn_type]):
                                target[node_name][conn_type].append(connections)
                            else:
                                target[node_name][conn_type][i].extend(connections)
    
    def _generate_workflow_name(
        self,
        requirements: Dict[str, Any],
        conversation: Optional[ConversationState]
    ) -> str:
        """Generate a descriptive workflow name."""
        if conversation:
            # Extract key terms from initial request
            request = conversation.initial_request
            words = request.split()[:5]
            name = " ".join(words).title()
            return f"{name} Workflow"
        
        # Generate from requirements
        trigger = requirements.get("trigger", "workflow")
        action = requirements.get("outputs", ["processing"])[0]
        return f"{trigger.title()} to {action.title()} Workflow"


# Global instance
_generator_instance = None

def get_workflow_generator() -> WorkflowGenerator:
    """Get singleton instance of workflow generator."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = WorkflowGenerator()
    return _generator_instance

