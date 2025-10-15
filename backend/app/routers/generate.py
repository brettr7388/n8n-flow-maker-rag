"""
API routes for workflow generation.
"""

from fastapi import APIRouter, HTTPException
from ..models.requests import GenerateRequest, GenerateResponse
from ..models.workflow import ValidationResult
from ..services.llm_service import LLMService
from ..services.validation_service import ValidationService

router = APIRouter()

llm_service = LLMService()
validation_service = ValidationService()

@router.post("/generate", response_model=GenerateResponse)
async def generate_workflow(request: GenerateRequest) -> GenerateResponse:
    """
    Generate an n8n workflow from a natural language request.
    
    Args:
        request: GenerateRequest containing user message and optional context
    
    Returns:
        GenerateResponse with workflow JSON, explanation, and validation
    """
    try:
        # Generate workflow using LLM
        result = llm_service.generate_workflow(
            user_request=request.message,
            previous_workflow=request.previousWorkflow
        )
        
        # Parse workflow
        from ..models.workflow import WorkflowJSON
        workflow = WorkflowJSON(**result['workflowJSON'])
        
        # Validate workflow
        validation = validation_service.validate_workflow(workflow)
        
        # Return response
        return GenerateResponse(
            workflowJSON=workflow,
            explanation=result.get('explanation', 'Workflow generated successfully.'),
            validation=validation
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating workflow: {str(e)}"
        )

