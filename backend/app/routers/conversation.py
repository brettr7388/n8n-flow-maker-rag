"""
API routes for conversation-based workflow generation.
Handles interactive question/answer flow.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..services.conversation_manager import get_conversation_manager, QuestionType
from ..services.llm_service import LLMService
from ..models.workflow import WorkflowJSON, ValidationResult
from ..services.validation_service import ValidationService

# RAG-Enhanced Workflow Generation
from ..services.rag_service import RAGService
from ..services.node_catalog import get_node_catalog

router = APIRouter()

conversation_manager = get_conversation_manager()
llm_service = LLMService()
validation_service = ValidationService()
rag_service = RAGService()
node_catalog = get_node_catalog()


def _enhance_questions_with_rag(questions: List[Any], user_request: str) -> List[Any]:
    """Enhance questions with RAG-retrieved node options."""
    try:
        for question in questions:
            # Enhance data source questions with actual n8n database nodes
            if question.type == QuestionType.DATA_SOURCE:
                db_nodes = node_catalog.find_nodes_by_category("database")
                if db_nodes:
                    # Add found nodes to options - use node_type instead of display_name
                    node_names = [_format_node_name(node.node_type) for node in db_nodes[:10]]
                    # Keep some existing options and add RAG ones
                    question.options = list(set(question.options[:3] + node_names))
            
            # Enhance email service questions with actual n8n email nodes
            elif question.type == QuestionType.EMAIL_SERVICE:
                email_nodes = node_catalog.find_nodes_by_category("communication")
                if email_nodes:
                    email_node_names = [
                        _format_node_name(node.node_type) for node in email_nodes 
                        if "mail" in node.node_type.lower() or "email" in node.node_type.lower()
                    ]
                    if email_node_names:
                        question.options = list(set(question.options[:3] + email_node_names[:7]))
            
            # Enhance integration questions with actual n8n app nodes
            elif question.type == QuestionType.INTEGRATION:
                # Try to find nodes mentioned in the user request
                relevant_nodes = node_catalog.find_best_nodes_for_request(user_request)
                if relevant_nodes:
                    app_names = [_format_node_name(node.node_type) for node in relevant_nodes[:10]]
                    question.options = app_names
    except Exception as e:
        # If RAG enhancement fails, just return original questions
        print(f"Warning: Failed to enhance questions with RAG: {e}")
    
    return questions


def _format_node_name(node_type: str) -> str:
    """Format node type to readable name."""
    # Remove the n8n-nodes-base. prefix
    name = node_type.replace("n8n-nodes-base.", "")
    # Convert camelCase to Title Case
    import re
    name = re.sub(r'([A-Z])', r' \1', name).strip()
    # Capitalize first letter of each word
    return name.title()


class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""
    message: str
    user_id: Optional[str] = None


class StartConversationResponse(BaseModel):
    """Response with conversation ID and initial questions."""
    conversation_id: str
    analysis: Dict[str, Any]
    questions: List[Dict[str, Any]]
    message: str


class AnswerQuestionRequest(BaseModel):
    """Request to answer a question."""
    conversation_id: str
    question_id: str
    answer: str


class AnswerQuestionResponse(BaseModel):
    """Response after answering a question."""
    status: str  # "more_questions", "continue", "ready_to_generate"
    next_questions: Optional[List[Dict[str, Any]]] = None
    unanswered_questions: Optional[List[Dict[str, Any]]] = None
    requirements: Optional[Dict[str, Any]] = None
    message: str


class GenerateFromConversationRequest(BaseModel):
    """Request to generate workflow from conversation."""
    conversation_id: str


class GenerateFromConversationResponse(BaseModel):
    """Response with generated workflow."""
    workflowJSON: WorkflowJSON
    explanation: str
    validation: ValidationResult
    conversation_summary: Dict[str, Any]


class EditWorkflowRequest(BaseModel):
    """Request to edit an existing workflow."""
    conversation_id: str
    edit_message: str


class EditWorkflowResponse(BaseModel):
    """Response with edited workflow."""
    workflowJSON: WorkflowJSON
    explanation: str
    validation: ValidationResult
    edit_summary: str


@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest) -> StartConversationResponse:
    """
    Start a new interactive conversation for workflow generation.
    
    This analyzes the user's request and generates relevant questions.
    """
    try:
        # Create new conversation
        conversation = conversation_manager.create_conversation(
            request.message,
            request.user_id
        )
        
        # Analyze the request
        analysis = conversation_manager.analyze_request(conversation.id)
        
        # Generate initial questions
        questions = conversation_manager.generate_questions(
            conversation.id,
            analysis
        )
        
        # Enhance questions with RAG data (add real n8n node options)
        questions = _enhance_questions_with_rag(questions, request.message)
        
        # Determine message based on complexity
        if analysis["complexity"] < 3:
            message = "I can generate this workflow for you. Just a couple of quick questions to make sure it's exactly what you need:"
        elif analysis["complexity"] < 7:
            message = "This looks like a medium-complexity workflow. I'll ask a few questions to ensure it meets your needs:"
        else:
            message = "This is a complex workflow! I'll ask several questions to make sure we build exactly what you need:"
        
        return StartConversationResponse(
            conversation_id=conversation.id,
            analysis=analysis,
            questions=[q.to_dict() for q in questions],
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting conversation: {str(e)}"
        )


@router.post("/answer", response_model=AnswerQuestionResponse)
async def answer_question(request: AnswerQuestionRequest) -> AnswerQuestionResponse:
    """
    Answer a question in the conversation.
    
    Returns next questions or indicates readiness to generate workflow.
    """
    try:
        result = conversation_manager.answer_question(
            request.conversation_id,
            request.question_id,
            request.answer
        )
        
        # Determine appropriate message
        if result["status"] == "more_questions":
            message = "Thanks! Based on your answer, I have a few follow-up questions:"
        elif result["status"] == "continue":
            message = "Got it! Please answer the remaining questions:"
        elif result["status"] == "ready_to_generate":
            message = "Perfect! I have all the information I need. Ready to generate your workflow?"
        else:
            message = "Response recorded."
        
        return AnswerQuestionResponse(
            status=result["status"],
            next_questions=result.get("next_questions"),
            unanswered_questions=result.get("unanswered_questions"),
            requirements=result.get("requirements"),
            message=message
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )


@router.post("/generate", response_model=GenerateFromConversationResponse)
async def generate_from_conversation(
    request: GenerateFromConversationRequest
) -> GenerateFromConversationResponse:
    """
    Generate workflow from completed conversation.
    
    Uses gathered requirements to create a production-ready workflow.
    """
    try:
        # Get conversation
        conversation = conversation_manager.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {request.conversation_id} not found"
            )
        
        # Check if we have sufficient information
        if not conversation_manager.has_sufficient_information(request.conversation_id):
            raise HTTPException(
                status_code=400,
                detail="Please answer all required questions before generating workflow"
            )
        
        # Get conversation summary
        summary = conversation_manager.get_summary(request.conversation_id)
        
        # Generate workflow using enhanced generator with detailed context
        result = llm_service.generate_workflow(
            user_request=conversation.initial_request,
            requirements=conversation.requirements,
            conversation_context=summary.get("detailed_context", ""),
            use_enhanced_generation=True
        )
        
        # Parse workflow
        workflow = WorkflowJSON(**result['workflowJSON'])
        
        # Validate workflow
        validation = validation_service.validate_workflow(workflow)
        
        # Update conversation with generated workflow
        conversation.generated_workflow = result['workflowJSON']
        conversation.phase = "complete"
        conversation.updated_at = datetime.utcnow()
        
        # Save the conversation
        conversation_manager._save_conversations()
        
        return GenerateFromConversationResponse(
            workflowJSON=workflow,
            explanation=result.get('explanation', 'Workflow generated successfully.'),
            validation=validation,
            conversation_summary=summary
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating workflow: {str(e)}"
        )


@router.get("/status/{conversation_id}")
async def get_conversation_status(conversation_id: str) -> Dict[str, Any]:
    """
    Get the current status of a conversation.
    """
    try:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Count answered vs total questions
        total_questions = len(conversation.questions)
        answered_questions = sum(1 for q in conversation.questions if q.answered)
        required_questions = sum(1 for q in conversation.questions if q.required)
        answered_required = sum(1 for q in conversation.questions if q.required and q.answered)
        
        return {
            "conversation_id": conversation.id,
            "phase": conversation.phase.value,
            "initial_request": conversation.initial_request,
            "complexity_score": conversation.complexity_score,
            "progress": {
                "total_questions": total_questions,
                "answered_questions": answered_questions,
                "required_questions": required_questions,
                "answered_required": answered_required,
                "percentage": (answered_questions / total_questions * 100) if total_questions > 0 else 0
            },
            "requirements": conversation.requirements,
            "ready_to_generate": conversation_manager.has_sufficient_information(conversation_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation status: {str(e)}"
        )


@router.post("/edit", response_model=EditWorkflowResponse)
async def edit_workflow(request: EditWorkflowRequest) -> EditWorkflowResponse:
    """
    Edit an existing workflow based on user feedback.
    
    This allows users to make modifications to a previously generated workflow.
    """
    try:
        # Get conversation
        conversation = conversation_manager.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {request.conversation_id} not found"
            )
        
        # Check if workflow exists
        if not conversation.generated_workflow:
            raise HTTPException(
                status_code=400,
                detail="No workflow found to edit. Please generate a workflow first."
            )
        
        # Get conversation summary for context
        summary = conversation_manager.get_summary(request.conversation_id)
        
        # Create edit prompt with original context and edit request
        edit_prompt = f"""
HIGHEST PRIORITY: Edit the existing workflow based on the user's request.

ORIGINAL WORKFLOW CONTEXT:
{summary.get("detailed_context", "")}

CURRENT WORKFLOW:
{conversation.generated_workflow}

USER'S EDIT REQUEST:
{request.edit_message}

Please modify the workflow to incorporate the user's changes while maintaining the original requirements and structure where possible.
"""
        
        # Generate edited workflow
        result = llm_service.generate_workflow(
            user_request=request.edit_message,
            requirements=conversation.requirements,
            conversation_context=edit_prompt,
            use_enhanced_generation=True,
            existing_workflow=conversation.generated_workflow
        )
        
        # Parse workflow
        workflow = WorkflowJSON(**result['workflowJSON'])
        
        # Validate workflow
        validation = validation_service.validate_workflow(workflow)
        
        # Update conversation with edited workflow
        conversation.generated_workflow = result['workflowJSON']
        conversation.updated_at = datetime.utcnow()
        
        # Save the conversation
        conversation_manager._save_conversations()
        
        return EditWorkflowResponse(
            workflowJSON=workflow,
            explanation=result.get('explanation', 'Workflow edited successfully.'),
            validation=validation,
            edit_summary=f"Applied edit: {request.edit_message}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error editing workflow: {str(e)}"
        )


@router.get("/summary/{conversation_id}")
async def get_conversation_summary(conversation_id: str) -> Dict[str, Any]:
    """
    Get a summary of the conversation.
    """
    try:
        summary = conversation_manager.get_summary(conversation_id)
        return summary
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation summary: {str(e)}"
        )

