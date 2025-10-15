"""
Conversation Manager for interactive workflow generation.
Manages question generation, conversation state, and requirement gathering.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid
import json
import os


class QuestionType(Enum):
    """Types of questions that can be asked."""
    TRIGGER = "trigger"
    DATA_SOURCE = "data_source"
    DATABASE = "database"
    VALIDATION = "validation"
    ERROR_HANDLING = "error_handling"
    OUTPUT = "output"
    NOTIFICATION = "notification"
    AUTHENTICATION = "authentication"
    PROCESSING = "processing"
    ROUTING = "routing"
    INTEGRATION = "integration"
    EMAIL_SERVICE = "email_service"
    TIMING = "timing"
    CONTENT = "content"
    RECIPIENTS = "recipients"
    TRANSFORMATIONS = "transformations"
    API_DETAILS = "api_details"
    DATA_MAPPING = "data_mapping"
    RESPONSE_HANDLING = "response_handling"
    FREQUENCY = "frequency"
    TIMEZONE = "timezone"
    CONDITIONS = "conditions"
    CONCURRENCY = "concurrency"
    SYNC_DIRECTION = "sync_direction"
    MATCHING = "matching"
    CONFLICTS = "conflicts"
    SCOPE = "scope"


class ConversationPhase(Enum):
    """Phases of the conversation."""
    INITIAL = "initial"
    ANALYZING = "analyzing"
    QUESTIONING = "questioning"
    GENERATING = "generating"
    COMPLETE = "complete"


@dataclass
class Question:
    """Represents a single question."""
    id: str
    type: QuestionType
    question: str
    options: List[str] = field(default_factory=list)
    required: bool = True
    answered: bool = False
    answer: Optional[str] = None
    answered_at: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "question": self.question,
            "options": self.options,
            "required": self.required,
            "answered": self.answered,
            "answer": self.answer,
            "answered_at": self.answered_at
        }


@dataclass
class ConversationState:
    """State of a workflow generation conversation."""
    id: str
    user_id: Optional[str]
    phase: ConversationPhase
    initial_request: str
    created_at: str
    updated_at: str
    questions: List[Question] = field(default_factory=list)
    answers: Dict[str, Any] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    complexity_score: int = 0
    similar_workflows: List[Dict[str, Any]] = field(default_factory=list)
    selected_patterns: List[str] = field(default_factory=list)
    generated_workflow: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "phase": self.phase.value,
            "initial_request": self.initial_request,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "questions": [q.to_dict() for q in self.questions],
            "answers": self.answers,
            "requirements": self.requirements,
            "complexity_score": self.complexity_score,
            "similar_workflows": self.similar_workflows,
            "selected_patterns": self.selected_patterns,
            "generated_workflow": self.generated_workflow
        }


class ConversationManager:
    """Manages interactive conversations for workflow generation."""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.storage_file = "conversations.json"
        self._load_conversations()
    
    def create_conversation(
        self,
        initial_request: str,
        user_id: Optional[str] = None
    ) -> ConversationState:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        conversation = ConversationState(
            id=conversation_id,
            user_id=user_id,
            phase=ConversationPhase.INITIAL,
            initial_request=initial_request,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.conversations[conversation_id] = conversation
        print(f"DEBUG: Created conversation {conversation_id}, saving...")
        self._save_conversations()
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def analyze_request(self, conversation_id: str) -> Dict[str, Any]:
        """
        Analyze initial request and determine what questions to ask.
        
        Returns:
            Analysis results including complexity estimate and question categories
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        request = conversation.initial_request.lower()
        
        # Determine complexity
        complexity = self._estimate_complexity(request)
        conversation.complexity_score = complexity
        
        # Categorize workflow type
        workflow_category = self._categorize_workflow(request)
        
        # Identify what's mentioned and what's missing
        analysis = {
            "complexity": complexity,
            "workflow_category": workflow_category,
            "has_trigger": self._has_trigger(request),
            "has_data_source": self._has_data_source(request),
            "has_action": self._has_action(request),
            "mentions_database": any(db in request for db in ["database", "db", "postgres", "mysql", "mongo"]),
            "mentions_email": any(term in request for term in ["email", "gmail", "mail", "send mail", "sendgrid", "mailgun"]),
            "mentions_webhook": "webhook" in request,
            "mentions_schedule": any(term in request for term in ["schedule", "daily", "hourly", "cron", "every day", "every hour"]),
            "mentions_validation": any(term in request for term in ["validate", "check", "verify"]),
            "mentions_error_handling": any(term in request for term in ["error", "fail", "retry"]),
            "mentions_api": any(term in request for term in ["api", "rest", "endpoint", "http"]),
            "mentions_sync": any(term in request for term in ["sync", "synchronize", "integrate", "connect"]),
            "mentions_notification": any(term in request for term in ["notify", "alert", "notification", "slack", "teams"]),
            "question_categories": []
        }
        
        # Store workflow category in conversation
        conversation.requirements["workflow_category"] = workflow_category
        
        # Determine questions based on workflow category
        if workflow_category == "email_workflow":
            analysis["question_categories"] = self._get_email_workflow_questions(request, analysis)
        elif workflow_category == "data_processing":
            analysis["question_categories"] = self._get_data_processing_questions(request, analysis)
        elif workflow_category == "api_integration":
            analysis["question_categories"] = self._get_api_integration_questions(request, analysis)
        elif workflow_category == "scheduled_task":
            analysis["question_categories"] = self._get_scheduled_task_questions(request, analysis)
        elif workflow_category == "data_sync":
            analysis["question_categories"] = self._get_data_sync_questions(request, analysis)
        else:
            # Generic workflow - use existing logic
            if not analysis["has_trigger"]:
                analysis["question_categories"].append(QuestionType.TRIGGER)
            
            if not analysis["has_data_source"] and ("fetch" in request or "get" in request):
                analysis["question_categories"].append(QuestionType.DATA_SOURCE)
            
            if analysis["mentions_database"] or conversation.complexity_score > 5:
                analysis["question_categories"].append(QuestionType.DATABASE)
            
            if conversation.complexity_score > 3:
                analysis["question_categories"].append(QuestionType.VALIDATION)
                analysis["question_categories"].append(QuestionType.ERROR_HANDLING)
            
            if analysis["has_action"]:
                analysis["question_categories"].append(QuestionType.OUTPUT)
        
        conversation.phase = ConversationPhase.ANALYZING
        conversation.updated_at = datetime.utcnow().isoformat()
        
        return analysis
    
    def _categorize_workflow(self, request: str) -> str:
        """Categorize the workflow based on keywords."""
        # Email workflow patterns
        if any(term in request for term in ["send email", "email to", "mail to", "email campaign", "notify via email"]):
            return "email_workflow"
        
        # Data sync patterns
        if any(term in request for term in ["sync", "synchronize", "connect", "integrate between", "two-way"]):
            return "data_sync"
        
        # API integration patterns
        if any(term in request for term in ["api call", "rest api", "fetch from api", "post to api", "api integration"]):
            return "api_integration"
        
        # Scheduled task patterns
        if any(term in request for term in ["daily", "hourly", "every hour", "every day", "schedule", "cron"]):
            return "scheduled_task"
        
        # Data processing patterns
        if any(term in request for term in ["process data", "transform", "filter", "aggregate", "parse", "extract"]):
            return "data_processing"
        
        # Notification patterns
        if any(term in request for term in ["notify", "alert", "notification", "send message"]):
            return "notification"
        
        return "generic"
    
    def _get_email_workflow_questions(self, request: str, analysis: Dict[str, Any]) -> List[QuestionType]:
        """Get questions for email workflow."""
        categories = []
        
        # Always ask about data source for email workflows
        categories.append(QuestionType.DATA_SOURCE)
        
        # Always ask about email service
        categories.append(QuestionType.EMAIL_SERVICE)
        
        # Ask about timing/schedule
        if not analysis["mentions_schedule"]:
            categories.append(QuestionType.TIMING)
        
        # Ask about email content
        categories.append(QuestionType.CONTENT)
        
        # Ask about recipients/filtering
        categories.append(QuestionType.RECIPIENTS)
        
        # Ask about error handling for production workflows
        categories.append(QuestionType.ERROR_HANDLING)
        
        return categories
    
    def _get_data_processing_questions(self, request: str, analysis: Dict[str, Any]) -> List[QuestionType]:
        """Get questions for data processing workflow."""
        categories = []
        
        # Ask about input source
        categories.append(QuestionType.DATA_SOURCE)
        
        # Ask about transformations
        categories.append(QuestionType.TRANSFORMATIONS)
        
        # Ask about output destination
        categories.append(QuestionType.OUTPUT)
        
        # Ask about trigger
        if not analysis["has_trigger"]:
            categories.append(QuestionType.TRIGGER)
        
        # Ask about validation
        categories.append(QuestionType.VALIDATION)
        
        return categories
    
    def _get_api_integration_questions(self, request: str, analysis: Dict[str, Any]) -> List[QuestionType]:
        """Get questions for API integration workflow."""
        categories = []
        
        # Ask about API details
        categories.append(QuestionType.API_DETAILS)
        
        # Ask about authentication
        categories.append(QuestionType.AUTHENTICATION)
        
        # Ask about data mapping
        categories.append(QuestionType.DATA_MAPPING)
        
        # Ask about error handling
        categories.append(QuestionType.ERROR_HANDLING)
        
        # Ask about response handling
        categories.append(QuestionType.RESPONSE_HANDLING)
        
        return categories
    
    def _get_scheduled_task_questions(self, request: str, analysis: Dict[str, Any]) -> List[QuestionType]:
        """Get questions for scheduled task workflow."""
        categories = []
        
        # Ask about frequency
        categories.append(QuestionType.FREQUENCY)
        
        # Ask about timezone
        categories.append(QuestionType.TIMEZONE)
        
        # Ask about what action to perform
        categories.append(QuestionType.PROCESSING)
        
        # Ask about conditions
        categories.append(QuestionType.CONDITIONS)
        
        # Ask about notifications
        categories.append(QuestionType.NOTIFICATION)
        
        return categories
    
    def _get_data_sync_questions(self, request: str, analysis: Dict[str, Any]) -> List[QuestionType]:
        """Get questions for data sync workflow."""
        categories = []
        
        # Ask about systems to sync
        categories.append(QuestionType.INTEGRATION)
        
        # Ask about sync direction
        categories.append(QuestionType.SYNC_DIRECTION)
        
        # Ask about matching records
        categories.append(QuestionType.MATCHING)
        
        # Ask about conflict resolution
        categories.append(QuestionType.CONFLICTS)
        
        # Ask about scope
        categories.append(QuestionType.SCOPE)
        
        return categories
    
    def _estimate_complexity(self, request: str) -> int:
        """Estimate workflow complexity from request (1-10)."""
        score = 1
        
        # Keywords that indicate complexity
        complex_keywords = [
            "manage", "system", "process", "automate", "integrate",
            "track", "monitor", "analyze", "distribute", "route"
        ]
        
        for keyword in complex_keywords:
            if keyword in request:
                score += 1
        
        # Multiple integrations
        integrations = ["database", "email", "slack", "api", "crm", "sheets"]
        mentioned_integrations = sum(1 for integration in integrations if integration in request)
        score += mentioned_integrations
        
        # Conditional logic indicators
        if any(word in request for word in ["if", "when", "based on", "depending", "priority"]):
            score += 2
        
        # Error handling
        if any(word in request for word in ["error", "fail", "retry"]):
            score += 1
        
        return min(score, 10)
    
    def _has_trigger(self, request: str) -> bool:
        """Check if request mentions a trigger."""
        triggers = ["webhook", "schedule", "email", "form", "trigger", "when", "every"]
        return any(trigger in request for trigger in triggers)
    
    def _has_data_source(self, request: str) -> bool:
        """Check if request mentions a data source."""
        sources = ["from", "fetch", "get", "retrieve", "pull", "read"]
        return any(source in request for source in sources)
    
    def _has_action(self, request: str) -> bool:
        """Check if request mentions an action."""
        actions = ["send", "create", "update", "delete", "post", "write", "save"]
        return any(action in request for action in actions)
    
    def generate_questions(
        self,
        conversation_id: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[Question]:
        """
        Generate questions based on analysis.
        
        Returns:
            List of questions to ask
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if analysis is None:
            analysis = self.analyze_request(conversation_id)
        
        questions = []
        question_categories = analysis.get("question_categories", [])
        
        # Generate questions for each category
        for category in question_categories:
            category_questions = self._generate_questions_for_category(
                category,
                conversation,
                analysis
            )
            questions.extend(category_questions)
        
        # Add questions to conversation
        for question in questions:
            conversation.questions.append(question)
        
        conversation.phase = ConversationPhase.QUESTIONING
        conversation.updated_at = datetime.utcnow().isoformat()
        
        return questions
    
    def _generate_questions_for_category(
        self,
        category: QuestionType,
        conversation: ConversationState,
        analysis: Dict[str, Any]
    ) -> List[Question]:
        """Generate questions for a specific category."""
        questions = []
        
        if category == QuestionType.TRIGGER:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.TRIGGER,
                question="What should trigger this workflow?",
                options=[
                    "Webhook (external system calls it)",
                    "Schedule (runs at specific times)",
                    "Email (triggered by incoming email)",
                    "Manual (I'll trigger it manually)",
                    "Form submission"
                ],
                required=True
            ))
        
        elif category == QuestionType.DATA_SOURCE:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.DATA_SOURCE,
                question="Where should the data come from?",
                options=[
                    "PostgreSQL database",
                    "MySQL database",
                    "MongoDB database",
                    "Google Sheets",
                    "Airtable",
                    "API endpoint",
                    "CSV/Excel file",
                    "Email inbox",
                    "The trigger itself (webhook/form data)"
                ],
                required=True
            ))
        
        elif category == QuestionType.EMAIL_SERVICE:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.EMAIL_SERVICE,
                question="Which email service do you want to use?",
                options=[
                    "Gmail",
                    "SendGrid",
                    "Mailgun",
                    "AWS SES",
                    "SMTP server (custom)",
                    "Outlook/Office 365",
                    "Other email service"
                ],
                required=True
            ))
        
        elif category == QuestionType.TIMING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.TIMING,
                question="When should the workflow run? (e.g., 'Daily at 9:00 AM EST' or 'Every hour')",
                options=[],
                required=True
            ))
        
        elif category == QuestionType.CONTENT:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.CONTENT,
                question="How should the email content be defined?",
                options=[
                    "Static template (same for all)",
                    "Dynamic content from data fields",
                    "HTML template file",
                    "Template ID from email service",
                    "Custom HTML per recipient"
                ],
                required=True
            ))
        
        elif category == QuestionType.RECIPIENTS:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.RECIPIENTS,
                question="Should all records receive emails or only filtered ones? (e.g., 'All customers' or 'Only active customers with status=active')",
                options=[],
                required=False
            ))
        
        elif category == QuestionType.TRANSFORMATIONS:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.TRANSFORMATIONS,
                question="What operations need to be performed on the data?",
                options=[
                    "Filter rows based on conditions",
                    "Map/transform field values",
                    "Aggregate data (sum, count, average)",
                    "Merge data from multiple sources",
                    "Split data into separate records",
                    "No transformation needed"
                ],
                required=True
            ))
        
        elif category == QuestionType.API_DETAILS:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.API_DETAILS,
                question="What API endpoint will you be calling? (Please provide URL or describe the API)",
                options=[],
                required=True
            ))
        
        elif category == QuestionType.DATA_MAPPING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.DATA_MAPPING,
                question="How should data be mapped between systems?",
                options=[
                    "Direct field mapping (same field names)",
                    "Custom field transformation",
                    "Use lookup tables for mapping",
                    "Complex mapping logic needed"
                ],
                required=True
            ))
        
        elif category == QuestionType.RESPONSE_HANDLING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.RESPONSE_HANDLING,
                question="What should be done with API responses?",
                options=[
                    "Store in database",
                    "Send to another API",
                    "Generate report/notification",
                    "Update original records",
                    "Multiple actions"
                ],
                required=True
            ))
        
        elif category == QuestionType.FREQUENCY:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.FREQUENCY,
                question="How often should this workflow run?",
                options=[
                    "Every hour",
                    "Daily at specific time",
                    "Weekly (specific day)",
                    "Monthly",
                    "Custom cron schedule"
                ],
                required=True
            ))
        
        elif category == QuestionType.TIMEZONE:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.TIMEZONE,
                question="What timezone should be used for scheduling?",
                options=[
                    "UTC",
                    "America/New_York (EST/EDT)",
                    "America/Los_Angeles (PST/PDT)",
                    "America/Chicago (CST/CDT)",
                    "Europe/London",
                    "Europe/Paris",
                    "Asia/Tokyo",
                    "Other timezone"
                ],
                required=True
            ))
        
        elif category == QuestionType.CONDITIONS:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.CONDITIONS,
                question="Should the workflow run conditionally?",
                options=[
                    "Always run",
                    "Only if data exists",
                    "Only on weekdays",
                    "Only if specific conditions are met",
                    "Custom conditional logic"
                ],
                required=False
            ))
        
        elif category == QuestionType.SYNC_DIRECTION:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.SYNC_DIRECTION,
                question="What's the sync direction between systems?",
                options=[
                    "One-way: System A → System B",
                    "One-way: System B → System A",
                    "Bi-directional (two-way sync)",
                    "Multiple sources → One destination"
                ],
                required=True
            ))
        
        elif category == QuestionType.MATCHING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.MATCHING,
                question="How should records be matched between systems?",
                options=[
                    "By ID field",
                    "By email address",
                    "By multiple fields",
                    "Custom matching logic",
                    "Always create new records"
                ],
                required=True
            ))
        
        elif category == QuestionType.CONFLICTS:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.CONFLICTS,
                question="How should conflicts be resolved?",
                options=[
                    "Source system wins",
                    "Destination system wins",
                    "Most recently updated wins",
                    "Manual review required",
                    "Skip conflicting records"
                ],
                required=True
            ))
        
        elif category == QuestionType.SCOPE:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.SCOPE,
                question="What data should be synced?",
                options=[
                    "All records",
                    "Only new records",
                    "Only changed records",
                    "Filtered subset of records",
                    "Custom scope definition"
                ],
                required=True
            ))
        
        elif category == QuestionType.DATABASE:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.DATABASE,
                question="Do you want to store data in a database?",
                options=[
                    "Yes - PostgreSQL",
                    "Yes - MySQL",
                    "Yes - MongoDB",
                    "Yes - Other database",
                    "No - Not needed"
                ],
                required=False
            ))
        
        elif category == QuestionType.VALIDATION:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.VALIDATION,
                question="Should the workflow validate incoming data?",
                options=[
                    "Yes - Validate required fields and format",
                    "Yes - Just check required fields",
                    "Yes - Custom validation logic",
                    "No - Skip validation"
                ],
                required=False
            ))
        
        elif category == QuestionType.ERROR_HANDLING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.ERROR_HANDLING,
                question="How should errors be handled?",
                options=[
                    "Retry automatically (3 times with delays)",
                    "Send alert to admin and stop",
                    "Log error and continue",
                    "Both retry and alert if all retries fail",
                    "No special error handling"
                ],
                required=False
            ))
        
        elif category == QuestionType.OUTPUT:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.OUTPUT,
                question="Where should results be sent?",
                options=[
                    "Email (Gmail, Outlook, etc.)",
                    "Slack / Teams notification",
                    "Database",
                    "Webhook to another system",
                    "Google Sheets",
                    "Multiple destinations"
                ],
                required=True
            ))
        
        elif category == QuestionType.NOTIFICATION:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.NOTIFICATION,
                question="Should you be notified about workflow execution?",
                options=[
                    "On success",
                    "On failure only",
                    "Always (success and failure)",
                    "Never"
                ],
                required=False
            ))
        
        elif category == QuestionType.PROCESSING:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.PROCESSING,
                question="What action should the workflow perform? (Describe the main operation)",
                options=[],
                required=True
            ))
        
        elif category == QuestionType.AUTHENTICATION:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.AUTHENTICATION,
                question="What authentication method does the API/service use?",
                options=[
                    "API key in header",
                    "OAuth 2.0",
                    "Basic authentication (username/password)",
                    "Bearer token",
                    "No authentication required"
                ],
                required=True
            ))
        
        elif category == QuestionType.INTEGRATION:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.INTEGRATION,
                question="Which systems need to be integrated? (Please specify both systems)",
                options=[],
                required=True
            ))
        
        elif category == QuestionType.CONCURRENCY:
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType.CONCURRENCY,
                question="Should multiple instances run simultaneously?",
                options=[
                    "Allow parallel execution",
                    "Queue executions (one at a time)",
                    "Skip if already running"
                ],
                required=False
            ))
        
        return questions
    
    def answer_question(
        self,
        conversation_id: str,
        question_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Record an answer to a question.
        
        Returns:
            Result including next question or completion status
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Find the question
        question = None
        for q in conversation.questions:
            if q.id == question_id:
                question = q
                break
        
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        # Record answer
        question.answered = True
        question.answer = answer
        question.answered_at = datetime.utcnow().isoformat()
        
        # Store in answers dict
        conversation.answers[question_id] = answer
        
        # Update requirements based on answer
        self._update_requirements(conversation, question, answer)
        
        # Check if there are follow-up questions
        follow_ups = self._generate_follow_up_questions(conversation, question, answer)
        
        if follow_ups:
            conversation.questions.extend(follow_ups)
            conversation.updated_at = datetime.utcnow()
            self._save_conversations()
            return {
                "status": "more_questions",
                "next_questions": [q.to_dict() for q in follow_ups]
            }
        
        # Check if all required questions are answered
        unanswered_required = [
            q for q in conversation.questions
            if q.required and not q.answered
        ]
        
        if unanswered_required:
            conversation.updated_at = datetime.utcnow()
            self._save_conversations()
            return {
                "status": "continue",
                "unanswered_questions": [q.to_dict() for q in unanswered_required]
            }
        
        # All questions answered, ready to generate
        conversation.phase = ConversationPhase.GENERATING
        conversation.updated_at = datetime.utcnow()
        self._save_conversations()
        
        return {
            "status": "ready_to_generate",
            "requirements": conversation.requirements
        }
    
    def _update_requirements(
        self,
        conversation: ConversationState,
        question: Question,
        answer: str
    ):
        """Update workflow requirements based on answer."""
        answer_lower = answer.lower()
        
        # Store raw answer
        conversation.requirements[f"answer_{question.type.value}"] = answer
        
        if question.type == QuestionType.TRIGGER:
            if "webhook" in answer_lower:
                conversation.requirements["trigger"] = "webhook"
                conversation.requirements["needs_auth"] = True
            elif "schedule" in answer_lower:
                conversation.requirements["trigger"] = "schedule"
                conversation.requirements["needs_cron"] = True
            elif "email" in answer_lower:
                conversation.requirements["trigger"] = "email"
                conversation.requirements["needs_imap"] = True
            elif "manual" in answer_lower:
                conversation.requirements["trigger"] = "manual"
            elif "form" in answer_lower:
                conversation.requirements["trigger"] = "form"
        
        elif question.type == QuestionType.DATA_SOURCE:
            if "postgresql" in answer_lower or "postgres" in answer_lower:
                conversation.requirements["data_source"] = "postgres"
            elif "mysql" in answer_lower:
                conversation.requirements["data_source"] = "mysql"
            elif "mongodb" in answer_lower:
                conversation.requirements["data_source"] = "mongodb"
            elif "google sheets" in answer_lower or "sheets" in answer_lower:
                conversation.requirements["data_source"] = "google_sheets"
            elif "airtable" in answer_lower:
                conversation.requirements["data_source"] = "airtable"
            elif "api" in answer_lower:
                conversation.requirements["data_source"] = "api"
            elif "email" in answer_lower:
                conversation.requirements["data_source"] = "email"
            elif "trigger" in answer_lower:
                conversation.requirements["data_source"] = "trigger_data"
        
        elif question.type == QuestionType.EMAIL_SERVICE:
            if "gmail" in answer_lower:
                conversation.requirements["email_service"] = "gmail"
            elif "sendgrid" in answer_lower:
                conversation.requirements["email_service"] = "sendgrid"
            elif "mailgun" in answer_lower:
                conversation.requirements["email_service"] = "mailgun"
            elif "aws ses" in answer_lower or "ses" in answer_lower:
                conversation.requirements["email_service"] = "aws_ses"
            elif "smtp" in answer_lower:
                conversation.requirements["email_service"] = "smtp"
            elif "outlook" in answer_lower or "office 365" in answer_lower:
                conversation.requirements["email_service"] = "outlook"
        
        elif question.type == QuestionType.TIMING:
            conversation.requirements["schedule_timing"] = answer
        
        elif question.type == QuestionType.CONTENT:
            if "static" in answer_lower:
                conversation.requirements["content_type"] = "static"
            elif "dynamic" in answer_lower:
                conversation.requirements["content_type"] = "dynamic"
            elif "html template" in answer_lower or "template file" in answer_lower:
                conversation.requirements["content_type"] = "html_template"
            elif "template id" in answer_lower:
                conversation.requirements["content_type"] = "template_id"
        
        elif question.type == QuestionType.RECIPIENTS:
            conversation.requirements["recipient_filter"] = answer
        
        elif question.type == QuestionType.TRANSFORMATIONS:
            transformations = []
            if "filter" in answer_lower:
                transformations.append("filter")
            if "map" in answer_lower or "transform" in answer_lower:
                transformations.append("map")
            if "aggregate" in answer_lower:
                transformations.append("aggregate")
            if "merge" in answer_lower:
                transformations.append("merge")
            if "split" in answer_lower:
                transformations.append("split")
            if "no" in answer_lower and "transformation" in answer_lower:
                transformations = []
            conversation.requirements["transformations"] = transformations
        
        elif question.type == QuestionType.API_DETAILS:
            conversation.requirements["api_endpoint"] = answer
        
        elif question.type == QuestionType.DATA_MAPPING:
            if "direct" in answer_lower:
                conversation.requirements["mapping_type"] = "direct"
            elif "custom" in answer_lower:
                conversation.requirements["mapping_type"] = "custom"
            elif "lookup" in answer_lower:
                conversation.requirements["mapping_type"] = "lookup"
            elif "complex" in answer_lower:
                conversation.requirements["mapping_type"] = "complex"
        
        elif question.type == QuestionType.RESPONSE_HANDLING:
            if "database" in answer_lower:
                conversation.requirements["response_handling"] = "database"
            elif "another api" in answer_lower:
                conversation.requirements["response_handling"] = "api"
            elif "report" in answer_lower or "notification" in answer_lower:
                conversation.requirements["response_handling"] = "report"
            elif "update" in answer_lower:
                conversation.requirements["response_handling"] = "update"
            elif "multiple" in answer_lower:
                conversation.requirements["response_handling"] = "multiple"
        
        elif question.type == QuestionType.FREQUENCY:
            conversation.requirements["frequency"] = answer
        
        elif question.type == QuestionType.TIMEZONE:
            conversation.requirements["timezone"] = answer
        
        elif question.type == QuestionType.CONDITIONS:
            conversation.requirements["conditions"] = answer
        
        elif question.type == QuestionType.SYNC_DIRECTION:
            conversation.requirements["sync_direction"] = answer
        
        elif question.type == QuestionType.MATCHING:
            conversation.requirements["matching_strategy"] = answer
        
        elif question.type == QuestionType.CONFLICTS:
            conversation.requirements["conflict_resolution"] = answer
        
        elif question.type == QuestionType.SCOPE:
            conversation.requirements["sync_scope"] = answer
        
        elif question.type == QuestionType.DATABASE:
            if "postgresql" in answer_lower:
                conversation.requirements["database"] = "postgres"
                conversation.requirements["needs_database"] = True
            elif "mysql" in answer_lower:
                conversation.requirements["database"] = "mysql"
                conversation.requirements["needs_database"] = True
            elif "mongodb" in answer_lower:
                conversation.requirements["database"] = "mongodb"
                conversation.requirements["needs_database"] = True
            elif "no" in answer_lower:
                conversation.requirements["needs_database"] = False
        
        elif question.type == QuestionType.VALIDATION:
            if "yes" in answer_lower:
                conversation.requirements["needs_validation"] = True
                if "custom" in answer_lower:
                    conversation.requirements["validation_type"] = "custom"
                elif "required" in answer_lower:
                    conversation.requirements["validation_type"] = "required_only"
                else:
                    conversation.requirements["validation_type"] = "full"
            else:
                conversation.requirements["needs_validation"] = False
        
        elif question.type == QuestionType.ERROR_HANDLING:
            if "retry" in answer_lower:
                conversation.requirements["needs_error_handling"] = True
                conversation.requirements["needs_retry_logic"] = True
                conversation.requirements["max_retries"] = 3
            if "alert" in answer_lower:
                conversation.requirements["needs_error_alerts"] = True
            if "log" in answer_lower:
                conversation.requirements["needs_error_logging"] = True
        
        elif question.type == QuestionType.OUTPUT:
            outputs = []
            if "email" in answer_lower or "gmail" in answer_lower:
                outputs.append("email")
            if "slack" in answer_lower or "teams" in answer_lower:
                outputs.append("slack")
            if "database" in answer_lower:
                outputs.append("database")
            if "webhook" in answer_lower:
                outputs.append("webhook")
            if "sheets" in answer_lower:
                outputs.append("sheets")
            
            conversation.requirements["outputs"] = outputs
            conversation.requirements["num_outputs"] = len(outputs)
        
        elif question.type == QuestionType.NOTIFICATION:
            conversation.requirements["notification_preference"] = answer
        
        elif question.type == QuestionType.PROCESSING:
            conversation.requirements["processing_action"] = answer
        
        elif question.type == QuestionType.AUTHENTICATION:
            if "api key" in answer_lower:
                conversation.requirements["auth_type"] = "api_key"
            elif "oauth" in answer_lower:
                conversation.requirements["auth_type"] = "oauth2"
            elif "basic" in answer_lower:
                conversation.requirements["auth_type"] = "basic"
            elif "bearer" in answer_lower:
                conversation.requirements["auth_type"] = "bearer"
            elif "no" in answer_lower:
                conversation.requirements["auth_type"] = "none"
        
        elif question.type == QuestionType.INTEGRATION:
            conversation.requirements["integration_systems"] = answer
        
        elif question.type == QuestionType.CONCURRENCY:
            conversation.requirements["concurrency"] = answer
    
    def _generate_follow_up_questions(
        self,
        conversation: ConversationState,
        question: Question,
        answer: str
    ) -> List[Question]:
        """Generate follow-up questions based on answer."""
        follow_ups = []
        answer_lower = answer.lower()
        
        if question.type == QuestionType.TRIGGER:
            if "webhook" in answer_lower:
                follow_ups.append(Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.AUTHENTICATION,
                    question="How should the webhook be secured?",
                    options=[
                        "API key in header (recommended)",
                        "Basic authentication",
                        "No authentication (not recommended)"
                    ],
                    required=False
                ))
            
            elif "schedule" in answer_lower:
                follow_ups.append(Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.TRIGGER,
                    question="How often should it run?",
                    options=[
                        "Every hour",
                        "Daily at specific time",
                        "Weekly",
                        "Custom schedule"
                    ],
                    required=True
                ))
        
        elif question.type == QuestionType.VALIDATION:
            if "yes" in answer_lower:
                follow_ups.append(Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.VALIDATION,
                    question="Should duplicate records be checked?",
                    options=[
                        "Yes - Check in database",
                        "Yes - Check in spreadsheet",
                        "No - Allow duplicates"
                    ],
                    required=False
                ))
        
        return follow_ups
    
    def has_sufficient_information(self, conversation_id: str) -> bool:
        """Check if enough information has been gathered."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        required_questions = [q for q in conversation.questions if q.required]
        return all(q.answered for q in required_questions)
    
    def get_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation for generation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Build detailed context for workflow generation
        detailed_context = self._build_detailed_context(conversation)
        
        return {
            "initial_request": conversation.initial_request,
            "complexity_score": conversation.complexity_score,
            "workflow_category": conversation.requirements.get("workflow_category", "generic"),
            "requirements": conversation.requirements,
            "answers": {
                q.question: q.answer
                for q in conversation.questions
                if q.answered
            },
            "detailed_context": detailed_context,
            "patterns_needed": conversation.selected_patterns
        }
    
    def _build_detailed_context(self, conversation: ConversationState) -> str:
        """Build detailed context string for LLM workflow generation."""
        req = conversation.requirements
        context_parts = []
        
        context_parts.append(f"User Request: {conversation.initial_request}")
        context_parts.append(f"Workflow Type: {req.get('workflow_category', 'generic')}")
        context_parts.append("")
        context_parts.append("DETAILED SPECIFICATIONS:")
        
        # Trigger information
        if "trigger" in req:
            context_parts.append(f"- Trigger: {req['trigger']}")
            if req.get("schedule_timing"):
                context_parts.append(f"  Timing: {req['schedule_timing']}")
            if req.get("timezone"):
                context_parts.append(f"  Timezone: {req['timezone']}")
        
        # Data source information
        if "data_source" in req:
            context_parts.append(f"- Data Source: {req['data_source']}")
        
        # Email workflow specifics
        if req.get("email_service"):
            context_parts.append(f"- Email Service: {req['email_service']}")
        if req.get("content_type"):
            context_parts.append(f"- Email Content Type: {req['content_type']}")
        if req.get("recipient_filter"):
            context_parts.append(f"- Recipient Filter: {req['recipient_filter']}")
        
        # API integration specifics
        if req.get("api_endpoint"):
            context_parts.append(f"- API Endpoint: {req['api_endpoint']}")
        if req.get("auth_type"):
            context_parts.append(f"- Authentication: {req['auth_type']}")
        
        # Data processing specifics
        if req.get("transformations"):
            context_parts.append(f"- Data Transformations: {', '.join(req['transformations'])}")
        
        # Data sync specifics
        if req.get("sync_direction"):
            context_parts.append(f"- Sync Direction: {req['sync_direction']}")
        if req.get("matching_strategy"):
            context_parts.append(f"- Record Matching: {req['matching_strategy']}")
        if req.get("conflict_resolution"):
            context_parts.append(f"- Conflict Resolution: {req['conflict_resolution']}")
        
        # Output/destination
        if req.get("outputs"):
            context_parts.append(f"- Outputs: {', '.join(req['outputs'])}")
        if req.get("response_handling"):
            context_parts.append(f"- Response Handling: {req['response_handling']}")
        
        # Database requirements
        if req.get("needs_database"):
            context_parts.append(f"- Database: {req.get('database', 'required')}")
        
        # Error handling
        if req.get("needs_error_handling"):
            error_details = []
            if req.get("needs_retry_logic"):
                error_details.append(f"retry up to {req.get('max_retries', 3)} times")
            if req.get("needs_error_alerts"):
                error_details.append("send alerts on failure")
            if req.get("needs_error_logging"):
                error_details.append("log errors")
            if error_details:
                context_parts.append(f"- Error Handling: {', '.join(error_details)}")
        
        # Validation
        if req.get("needs_validation"):
            context_parts.append(f"- Validation: {req.get('validation_type', 'full')}")
        
        # Notifications
        if req.get("notification_preference"):
            context_parts.append(f"- Notifications: {req['notification_preference']}")
        
        # Additional context from free-text answers
        for key, value in req.items():
            if key.startswith("answer_") and value and isinstance(value, str) and len(value) > 20:
                question_type = key.replace("answer_", "").replace("_", " ").title()
                context_parts.append(f"- {question_type}: {value}")
        
        return "\n".join(context_parts)
    
    def _load_conversations(self):
        """Load conversations from file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for conv_id, conv_data in data.items():
                        # Convert datetime strings back to datetime objects if they're strings
                        if isinstance(conv_data.get('created_at'), str):
                            conv_data['created_at'] = datetime.fromisoformat(conv_data['created_at'])
                        if isinstance(conv_data.get('updated_at'), str):
                            conv_data['updated_at'] = datetime.fromisoformat(conv_data['updated_at'])
                        
                        # Recreate the conversation object
                        conversation = ConversationState(**conv_data)
                        self.conversations[conv_id] = conversation
        except Exception as e:
            print(f"Warning: Could not load conversations from file: {e}")
            self.conversations = {}
    
    def _save_conversations(self):
        """Save conversations to file."""
        try:
            print(f"DEBUG: Saving {len(self.conversations)} conversations to {self.storage_file}")
            data = {}
            for conv_id, conversation in self.conversations.items():
                # Convert to dict and handle datetime serialization
                conv_dict = asdict(conversation)
                conv_dict['created_at'] = conversation.created_at.isoformat()
                conv_dict['updated_at'] = conversation.updated_at.isoformat()
                data[conv_id] = conv_dict
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"DEBUG: Successfully saved conversations to {self.storage_file}")
        except Exception as e:
            print(f"Warning: Could not save conversations to file: {e}")
            import traceback
            traceback.print_exc()


# Global instance
_manager_instance = None

def get_conversation_manager() -> ConversationManager:
    """Get singleton instance of conversation manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConversationManager()
    return _manager_instance

