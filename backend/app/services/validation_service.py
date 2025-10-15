"""
Validation service for n8n workflows.
Ensures generated workflows are valid and complete.
"""

from typing import List, Set
from ..models.workflow import WorkflowJSON, ValidationResult, ValidationError

class ValidationService:
    """Validates n8n workflow structure and integrity."""
    
    REQUIRED_WORKFLOW_FIELDS = ['name', 'nodes', 'connections']
    REQUIRED_NODE_FIELDS = ['id', 'name', 'type', 'typeVersion', 'position', 'parameters']
    TRIGGER_NODE_TYPES = [
        'n8n-nodes-base.manualTrigger',
        'n8n-nodes-base.webhook',
        'n8n-nodes-base.scheduleTrigger',
        'n8n-nodes-base.cronTrigger'
    ]
    
    def validate_workflow(self, workflow: WorkflowJSON) -> ValidationResult:
        """
        Perform comprehensive validation of workflow.
        
        Args:
            workflow: The workflow to validate
        
        Returns:
            ValidationResult with errors and warnings
        """
        errors: List[ValidationError] = []
        warnings: List[str] = []
        
        # Validate structure
        errors.extend(self._validate_structure(workflow))
        
        # Validate nodes
        errors.extend(self._validate_nodes(workflow))
        
        # Validate connections
        errors.extend(self._validate_connections(workflow))
        
        # Validate trigger
        trigger_warnings = self._validate_trigger(workflow)
        warnings.extend(trigger_warnings)
        
        # Validate node names are unique
        errors.extend(self._validate_unique_names(workflow))
        
        # Additional warnings
        warnings.extend(self._generate_warnings(workflow))
        
        return ValidationResult(
            isValid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_structure(self, workflow: WorkflowJSON) -> List[ValidationError]:
        """Validate basic workflow structure."""
        errors = []
        
        # Check required fields
        workflow_dict = workflow.model_dump()
        for field in self.REQUIRED_WORKFLOW_FIELDS:
            if field not in workflow_dict or workflow_dict[field] is None:
                errors.append(ValidationError(
                    type="structure",
                    message=f"Missing required field: {field}"
                ))
        
        # Check nodes exist
        if not workflow.nodes or len(workflow.nodes) == 0:
            errors.append(ValidationError(
                type="structure",
                message="Workflow must contain at least one node"
            ))
        
        return errors
    
    def _validate_nodes(self, workflow: WorkflowJSON) -> List[ValidationError]:
        """Validate individual nodes."""
        errors = []
        
        for node in workflow.nodes:
            node_dict = node.model_dump()
            
            # Check required fields
            for field in self.REQUIRED_NODE_FIELDS:
                if field not in node_dict or node_dict[field] is None:
                    errors.append(ValidationError(
                        type="node",
                        message=f"Node missing required field: {field}",
                        nodeId=node.id
                    ))
            
            # Validate position
            if len(node.position) != 2:
                errors.append(ValidationError(
                    type="node",
                    message=f"Node position must be [x, y]",
                    nodeId=node.id
                ))
            
            # Validate type format
            if not node.type.startswith('n8n-nodes-base.'):
                errors.append(ValidationError(
                    type="node",
                    message=f"Invalid node type format: {node.type}",
                    nodeId=node.id
                ))
        
        return errors
    
    def _validate_connections(self, workflow: WorkflowJSON) -> List[ValidationError]:
        """Validate workflow connections."""
        errors = []
        
        # Get all node names
        node_names = {node.name for node in workflow.nodes}
        
        # Check each connection
        for source_name, outputs in workflow.connections.items():
            # Validate source node exists
            if source_name not in node_names:
                errors.append(ValidationError(
                    type="connection",
                    message=f"Connection source node not found: {source_name}"
                ))
                continue
            
            # Check main connections
            if 'main' in outputs:
                for output_group in outputs['main']:
                    for connection in output_group:
                        # Validate target node exists
                        if connection.node not in node_names:
                            errors.append(ValidationError(
                                type="connection",
                                message=f"Connection target node not found: {connection.node}",
                                nodeId=source_name
                            ))
        
        return errors
    
    def _validate_trigger(self, workflow: WorkflowJSON) -> List[str]:
        """Validate workflow has appropriate trigger."""
        warnings = []
        
        # Check for trigger nodes
        has_trigger = any(
            node.type in self.TRIGGER_NODE_TYPES
            for node in workflow.nodes
        )
        
        if not has_trigger:
            warnings.append(
                "Workflow does not contain a trigger node. "
                "It may need to be started manually or have a trigger added."
            )
        
        return warnings
    
    def _validate_unique_names(self, workflow: WorkflowJSON) -> List[ValidationError]:
        """Validate all node names are unique."""
        errors = []
        seen_names: Set[str] = set()
        
        for node in workflow.nodes:
            if node.name in seen_names:
                errors.append(ValidationError(
                    type="node",
                    message=f"Duplicate node name: {node.name}",
                    nodeId=node.id
                ))
            seen_names.add(node.name)
        
        return errors
    
    def _generate_warnings(self, workflow: WorkflowJSON) -> List[str]:
        """Generate helpful warnings."""
        warnings = []
        
        # Check for disconnected nodes
        connected_nodes = set()
        for source_name, outputs in workflow.connections.items():
            connected_nodes.add(source_name)
            if 'main' in outputs:
                for output_group in outputs['main']:
                    for connection in output_group:
                        connected_nodes.add(connection.node)
        
        disconnected = []
        for node in workflow.nodes:
            if node.name not in connected_nodes:
                disconnected.append(node.name)
        
        if disconnected:
            warnings.append(
                f"Disconnected nodes found: {', '.join(disconnected)}. "
                "These nodes will not execute."
            )
        
        # Check workflow name
        if not workflow.name or workflow.name == "My Workflow":
            warnings.append("Consider giving the workflow a more descriptive name")
        
        return warnings

