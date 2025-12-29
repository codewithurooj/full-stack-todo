"""MCP tool endpoints for AI-powered task management"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.database import get_session
from app.mcp_server.auth import verify_jwt_token
from app.mcp_server.server import limiter, get_tool_handler, get_tool_rate_limit
from app.mcp_server.errors import MCPError
from app.mcp_server.tools.add_task import AddTaskRequest
from app.mcp_server.tools.list_tasks import ListTasksRequest
import logging

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/tools", tags=["mcp"])
security = HTTPBearer()


@router.post("/add_task")
@limiter.limit("100/hour")
async def add_task_endpoint(
    request: Request,
    task_request: AddTaskRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Create a new task via MCP tool.

    Rate limit: 100 requests per hour per IP
    """
    try:
        # Verify JWT and get authenticated user_id
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Get tool handler
        handler = get_tool_handler("add_task")

        # Execute tool
        result = handler(
            request=task_request,
            token_user_id=token_user_id,
            session=session
        )

        logger.info(f"add_task: user={token_user_id}, task_id={result.task_id}")

        return result

    except MCPError as e:
        logger.warning(f"add_task error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"add_task unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}}
        )


@router.get("/list_tasks")
@limiter.limit("1000/hour")
async def list_tasks_endpoint(
    request: Request,
    user_id: str,
    filter: str = "all",
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    List all tasks for authenticated user with optional filtering.

    Rate limit: 1000 requests per hour per IP
    """
    try:
        # Verify JWT and get authenticated user_id
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Build request
        task_request = ListTasksRequest(
            user_id=user_id,
            filter=filter,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get tool handler
        handler = get_tool_handler("list_tasks")

        # Execute tool
        result = handler(
            request=task_request,
            token_user_id=token_user_id,
            session=session
        )

        logger.info(f"list_tasks: user={token_user_id}, count={result.count}, filter={result.filter_applied}")

        return result

    except MCPError as e:
        logger.warning(f"list_tasks error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"list_tasks unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}}
        )


@router.patch("/complete_task")
@limiter.limit("200/hour")
async def complete_task_endpoint(
    request: Request,
    user_id: str,
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Toggle task completion status via MCP tool.

    Rate limit: 200 requests per hour per IP
    """
    try:
        # Verify JWT
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Build request
        from app.mcp_server.tools.complete_task import CompleteTaskRequest
        task_request = CompleteTaskRequest(user_id=user_id, task_id=task_id)

        # Execute tool
        handler = get_tool_handler("complete_task")
        result = handler(request=task_request, token_user_id=token_user_id, session=session)

        logger.info(f"complete_task: user={token_user_id}, task_id={result.task_id}, completed={result.completed}")
        return result

    except MCPError as e:
        logger.warning(f"complete_task error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"complete_task unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}})


@router.delete("/delete_task")
@limiter.limit("100/hour")
async def delete_task_endpoint(
    request: Request,
    user_id: str,
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Delete a task permanently via MCP tool.

    Rate limit: 100 requests per hour per IP
    """
    try:
        # Verify JWT
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Build request
        from app.mcp_server.tools.delete_task import DeleteTaskRequest
        task_request = DeleteTaskRequest(user_id=user_id, task_id=task_id)

        # Execute tool
        handler = get_tool_handler("delete_task")
        result = handler(request=task_request, token_user_id=token_user_id, session=session)

        logger.info(f"delete_task: user={token_user_id}, task_id={result.task_id}")
        return result

    except MCPError as e:
        logger.warning(f"delete_task error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"delete_task unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}})


@router.put("/update_task")
@limiter.limit("200/hour")
async def update_task_endpoint(
    request: Request,
    user_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Update task title and/or description via MCP tool.

    Rate limit: 200 requests per hour per IP
    """
    try:
        # Verify JWT
        token = credentials.credentials
        token_user_id = verify_jwt_token(token)

        # Build request
        from app.mcp_server.tools.update_task import UpdateTaskRequest
        task_request = UpdateTaskRequest(user_id=user_id, task_id=task_id, title=title, description=description)

        # Execute tool
        handler = get_tool_handler("update_task")
        result = handler(request=task_request, token_user_id=token_user_id, session=session)

        logger.info(f"update_task: user={token_user_id}, task_id={result.task_id}")
        return result

    except MCPError as e:
        logger.warning(f"update_task error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"update_task unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": "Internal server error", "code": "INTERNAL_ERROR"}})
