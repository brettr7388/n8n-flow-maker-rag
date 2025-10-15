from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class WorkflowNode(BaseModel):
    """Represents a single node in an n8n workflow."""
    id: str
    name: str
    type: str
    typeVersion: int
    position: List[int]  # [x, y]
    parameters: Dict[str, Any]
    credentials: Optional[Dict[str, Dict[str, str]]] = None

class WorkflowConnection(BaseModel):
    """Represents a connection between nodes."""
    node: str
    type: str
    index: int

class WorkflowJSON(BaseModel):
    """Complete n8n workflow structure."""
    name: str
    nodes: List[WorkflowNode]
    connections: Dict[str, Dict[str, List[List[WorkflowConnection]]]]
    active: Optional[bool] = False
    settings: Optional[Dict[str, Any]] = {}
    meta: Optional[Dict[str, Any]] = None

class ValidationError(BaseModel):
    """Validation error details."""
    type: str
    message: str
    nodeId: Optional[str] = None

class ValidationResult(BaseModel):
    """Workflow validation result."""
    isValid: bool
    errors: List[ValidationError] = []
    warnings: List[str] = []

