"""Chat endpoint for AI-powered task management"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from openai import OpenAI
from app.config import settings
from app.database import get_session
from app.middleware.auth import get_current_user_id
from app.mcp_server.server import get_all_tool_schemas, get_tool_handler
from app.mcp_server.errors import MCPError
from app.models.conversation import Conversation
from app.models.message import Message
import logging
import json

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/chat", tags=["chat"])

# Initialize OpenAI client (with 30-second timeout per spec)
openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=30.0
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="User message to AI assistant")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID (optional)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    conversation_id: int
    assistant_message: str
    tool_calls: List[str] = Field(default_factory=list)
    created_at: datetime


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    user_id: str,
    chat_request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    AI-powered chat endpoint with task management tools.

    Stateless flow (8 steps):
    1. Fetch conversation history from database
    2. Build messages array (system + history + user message)
    3. Store user message
    4. Call OpenAI with tool schemas
    5. If tool calls: invoke tools and get results
    6. If tool calls: call OpenAI again with results
    7. Store assistant message
    8. Return response
    """
    import time
    start_time = time.time()

    try:
        # Verify user_id matches JWT token
        if user_id != current_user_id:
            raise HTTPException(
                status_code=403,
                detail={"error": {"message": "Unauthorized access", "code": "AUTHORIZATION_ERROR"}}
            )

        # Step 1: Get or create conversation
        conversation_id = chat_request.conversation_id

        if conversation_id:
            # Verify conversation belongs to user
            conversation = session.get(Conversation, conversation_id)
            if not conversation or conversation.user_id != user_id:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=user_id,
                started_at=datetime.utcnow(),
                last_message_at=datetime.utcnow()
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            conversation_id = conversation.id

        # Step 2: Build messages array from history (configurable limit from settings)
        db_fetch_start = time.time()
        statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at).limit(settings.CHAT_HISTORY_LIMIT)
        history = session.exec(statement).all()
        db_fetch_time = time.time() - db_fetch_start
        logger.info(f"Database fetch time: {db_fetch_time * 1000:.2f}ms (target: <100ms)")

        system_prompt = f"{settings.CHAT_SYSTEM_PROMPT} The authenticated user ID is: {user_id}. When calling tools, ALWAYS use this exact user_id parameter."
        logger.info(f"System prompt: {system_prompt}")

        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Add conversation history
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": chat_request.message})

        # Step 3: Store user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=chat_request.message,
            created_at=datetime.utcnow()
        )
        session.add(user_message)
        session.commit()

        # Step 4: Call OpenAI with tool schemas
        tool_schemas = get_all_tool_schemas()

        response = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else "gpt-4o",
            messages=messages,
            tools=tool_schemas if tool_schemas else None,
            tool_choice="auto" if tool_schemas else None
        )

        assistant_message_content = ""
        tool_calls_executed = []

        # Step 5 & 6: Handle tool calls if present
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls

            # Add assistant message with tool calls to messages
            messages.append(response.choices[0].message.model_dump())

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                tool_calls_executed.append(tool_name)

                try:
                    # Get tool handler
                    handler = get_tool_handler(tool_name)

                    # Build request object based on tool
                    if tool_name == "add_task":
                        from app.mcp_server.tools.add_task import AddTaskRequest
                        request_obj = AddTaskRequest(**tool_args)
                    elif tool_name == "list_tasks":
                        from app.mcp_server.tools.list_tasks import ListTasksRequest
                        request_obj = ListTasksRequest(**tool_args)
                    elif tool_name == "complete_task":
                        from app.mcp_server.tools.complete_task import CompleteTaskRequest
                        request_obj = CompleteTaskRequest(**tool_args)
                    elif tool_name == "delete_task":
                        from app.mcp_server.tools.delete_task import DeleteTaskRequest
                        request_obj = DeleteTaskRequest(**tool_args)
                    elif tool_name == "update_task":
                        from app.mcp_server.tools.update_task import UpdateTaskRequest
                        request_obj = UpdateTaskRequest(**tool_args)
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    # Execute tool
                    result = handler(request=request_obj, token_user_id=current_user_id, session=session)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.model_dump_json()
                    })

                except MCPError as e:
                    # Return error to OpenAI
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"error": e.to_dict()})
                    })

            # Call OpenAI again with tool results
            response = openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else "gpt-4o",
                messages=messages
            )

        # Get final assistant message
        assistant_message_content = response.choices[0].message.content or "I encountered an issue processing your request."

        # Step 7: Store assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message_content,
            created_at=datetime.utcnow()
        )
        session.add(assistant_message)

        # Update conversation timestamp
        conversation.last_message_at = datetime.utcnow()
        session.add(conversation)
        session.commit()

        # Step 8: Return response
        total_time = time.time() - start_time
        logger.info(f"Total request time: {total_time:.2f}s (target: <3s p95) | user={user_id} | conversation={conversation_id}")

        return ChatResponse(
            conversation_id=conversation_id,
            assistant_message=assistant_message_content,
            tool_calls=tool_calls_executed,
            created_at=assistant_message.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}}
        )
