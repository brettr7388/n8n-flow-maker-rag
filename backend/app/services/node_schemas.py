"""
Node schema definitions and validation for n8n nodes.
Based on the flowfix.txt requirements for proper parameter validation.
"""

from typing import Dict, List, Any, Optional


class NodeSchemaValidator:
    """Validates node configurations against expected schemas."""
    
    def __init__(self):
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load node schemas with required/optional parameters."""
        return {
            "n8n-nodes-base.httpRequest": {
                "required": ["method", "url"],
                "optional": ["authentication", "options", "bodyParametersJson", "headerParametersJson"],
                "requires_credentials": False,
                "error_handling_recommended": True,
                "typical_config": {
                    "method": "GET",
                    "url": "https://api.example.com/endpoint",
                    "options": {}
                }
            },
            "@blotato/n8n-nodes-blotato.blotato": {
                "required": ["resource"],
                "optional": ["operation", "mediaUrl", "caption", "platform"],
                "requires_credentials": True,
                "credential_type": "blotatoApi",
                "error_handling_recommended": True,
                "typical_config": {
                    "resource": "post",
                    "operation": "create"
                }
            },
            "n8n-nodes-base.openAi": {
                "required": ["resource", "operation"],
                "optional": ["options", "prompt", "model"],
                "requires_credentials": True,
                "credential_type": "openAiApi",
                "typical_config": {
                    "resource": "text",
                    "operation": "complete",
                    "options": {
                        "model": "gpt-4",
                        "temperature": 0.7
                    }
                }
            },
            "@n8n/n8n-nodes-langchain.agent": {
                "required": ["promptType"],
                "optional": ["text", "options"],
                "requires_credentials": False,
                "error_handling_recommended": False
            },
            "@n8n/n8n-nodes-langchain.chatOpenAi": {
                "required": [],
                "optional": ["model", "temperature", "maxTokens"],
                "requires_credentials": True,
                "credential_type": "openAiApi"
            },
            "n8n-nodes-base.if": {
                "required": ["conditions"],
                "optional": ["options"],
                "requires_credentials": False
            },
            "n8n-nodes-base.switch": {
                "required": ["mode"],
                "optional": ["rules", "output"],
                "requires_credentials": False
            },
            "n8n-nodes-base.merge": {
                "required": [],
                "optional": ["mode", "options"],
                "requires_credentials": False
            },
            "n8n-nodes-base.set": {
                "required": [],
                "optional": ["values", "options"],
                "requires_credentials": False
            },
            "n8n-nodes-base.code": {
                "required": ["mode"],
                "optional": ["jsCode", "pythonCode"],
                "requires_credentials": False
            },
            "n8n-nodes-base.function": {
                "required": ["functionCode"],
                "optional": [],
                "requires_credentials": False
            },
            "n8n-nodes-base.googleSheets": {
                "required": ["resource", "operation"],
                "optional": ["sheetId", "range", "documentId"],
                "requires_credentials": True,
                "credential_type": "googleSheetsOAuth2Api",
                "error_handling_recommended": True
            },
            "n8n-nodes-base.gmail": {
                "required": ["resource", "operation"],
                "optional": ["sendTo", "subject", "message"],
                "requires_credentials": True,
                "credential_type": "gmailOAuth2",
                "error_handling_recommended": True
            },
            "n8n-nodes-base.slack": {
                "required": ["resource", "operation"],
                "optional": ["channel", "text", "username"],
                "requires_credentials": True,
                "credential_type": "slackApi",
                "error_handling_recommended": True
            },
            "n8n-nodes-base.postgres": {
                "required": ["operation"],
                "optional": ["table", "query", "columns"],
                "requires_credentials": True,
                "credential_type": "postgres",
                "error_handling_recommended": True
            },
            "n8n-nodes-base.mysql": {
                "required": ["operation"],
                "optional": ["table", "query", "columns"],
                "requires_credentials": True,
                "credential_type": "mySql",
                "error_handling_recommended": True
            },
            "n8n-nodes-base.webhook": {
                "required": [],
                "optional": ["path", "httpMethod", "responseMode"],
                "requires_credentials": False
            },
            "n8n-nodes-base.scheduleTrigger": {
                "required": [],
                "optional": ["rule", "triggerTimes"],
                "requires_credentials": False
            },
            "n8n-nodes-base.manualTrigger": {
                "required": [],
                "optional": [],
                "requires_credentials": False
            },
            "n8n-nodes-base.stickyNote": {
                "required": [],
                "optional": ["content", "height", "width"],
                "requires_credentials": False
            },
            "n8n-nodes-base.wait": {
                "required": ["resume"],
                "optional": ["amount", "unit"],
                "requires_credentials": False
            },
            "n8n-nodes-base.errorTrigger": {
                "required": [],
                "optional": [],
                "requires_credentials": False
            },
            "@n8n/n8n-nodes-langchain.toolHackerNews": {
                "required": [],
                "optional": ["operation", "articleId"],
                "requires_credentials": False
            },
            "n8n-nodes-base.perplexity": {
                "required": ["operation"],
                "optional": ["prompt", "model"],
                "requires_credentials": True,
                "credential_type": "perplexityApi"
            }
        }
    
    def validate_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a node against its schema.
        
        Returns:
            Dict with keys:
                - valid: bool
                - errors: List[str]
                - warnings: List[str]
        """
        node_type = node.get('type')
        schema = self.schemas.get(node_type)
        
        if not schema:
            return {
                'valid': True,
                'warnings': [f"No schema found for node type: {node_type}"],
                'errors': []
            }
        
        errors = []
        warnings = []
        
        # Check required parameters
        params = node.get('parameters', {})
        for req_param in schema.get('required', []):
            if req_param not in params:
                errors.append(f"Missing required parameter: {req_param}")
        
        # Check if parameters is empty when it shouldn't be
        if schema.get('required') and not params:
            errors.append("Parameters object is empty but required parameters are needed")
        
        # Check credentials
        if schema.get('requires_credentials'):
            if 'credentials' not in node:
                errors.append("Missing credentials configuration")
            else:
                cred_type = schema.get('credential_type')
                if cred_type and cred_type not in node['credentials']:
                    errors.append(f"Missing credential type: {cred_type}")
        
        # Check error handling recommendation
        if schema.get('error_handling_recommended'):
            if 'onError' not in node and 'retryOnFail' not in node:
                warnings.append("Error handling recommended but not configured")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_typical_config(self, node_type: str) -> Dict[str, Any]:
        """Get typical configuration for a node type."""
        schema = self.schemas.get(node_type, {})
        return schema.get('typical_config', {})
    
    def requires_credentials(self, node_type: str) -> bool:
        """Check if a node type requires credentials."""
        schema = self.schemas.get(node_type, {})
        return schema.get('requires_credentials', False)
    
    def get_credential_type(self, node_type: str) -> Optional[str]:
        """Get the credential type for a node."""
        schema = self.schemas.get(node_type, {})
        return schema.get('credential_type')
    
    def needs_error_handling(self, node_type: str) -> bool:
        """Check if a node type should have error handling."""
        schema = self.schemas.get(node_type, {})
        return schema.get('error_handling_recommended', False)


# Global instance
_validator_instance = None


def get_node_schema_validator() -> NodeSchemaValidator:
    """Get singleton instance of node schema validator."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = NodeSchemaValidator()
    return _validator_instance


