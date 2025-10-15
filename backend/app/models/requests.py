from pydantic import BaseModel
from typing import Optional
from .workflow import WorkflowJSON

class GenerateRequest(BaseModel):
    """Request to generate a workflow."""
    message: str
    conversationId: Optional[str] = None
    previousWorkflow: Optional[WorkflowJSON] = None

class GenerateResponse(BaseModel):
    """Response containing generated workflow."""
    workflowJSON: WorkflowJSON
    explanation: str
    validation: 'ValidationResult'

class ValidateRequest(BaseModel):
    """Request to validate a workflow."""
    workflow: WorkflowJSON

# Import ValidationResult here to avoid circular imports
from .workflow import ValidationResult
GenerateResponse.model_rebuild()

