"""
API routes for workflow validation.
"""

from fastapi import APIRouter, HTTPException
from ..models.requests import ValidateRequest
from ..models.workflow import ValidationResult
from ..services.validation_service import ValidationService

router = APIRouter()

validation_service = ValidationService()

@router.post("/validate", response_model=ValidationResult)
async def validate_workflow(request: ValidateRequest) -> ValidationResult:
    """
    Validate an n8n workflow structure.
    
    Args:
        request: ValidateRequest containing workflow to validate
    
    Returns:
        ValidationResult with errors and warnings
    """
    try:
        result = validation_service.validate_workflow(request.workflow)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating workflow: {str(e)}"
        )

