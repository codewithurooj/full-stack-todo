"""MCP Server with tool registrations and rate limiting"""
from typing import Dict, Any, Callable
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter with in-memory storage
limiter = Limiter(key_func=get_remote_address)

# Tool registry: Maps tool names to their handler functions and rate limits
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    handler: Callable,
    rate_limit: str,
    description: str
) -> None:
    """
    Register an MCP tool with its handler and rate limit.

    Args:
        name: Tool name (e.g., "add_task")
        handler: Function that implements the tool
        rate_limit: Rate limit string (e.g., "100/hour")
        description: Tool description for OpenAI function calling
    """
    TOOL_REGISTRY[name] = {
        "handler": handler,
        "rate_limit": rate_limit,
        "description": description
    }


def get_tool_handler(tool_name: str) -> Callable:
    """
    Get the handler function for a registered tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Handler function

    Raises:
        KeyError: If tool is not registered
    """
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' is not registered")

    return TOOL_REGISTRY[tool_name]["handler"]


def get_tool_rate_limit(tool_name: str) -> str:
    """
    Get the rate limit for a registered tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Rate limit string (e.g., "100/hour")

    Raises:
        KeyError: If tool is not registered
    """
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' is not registered")

    return TOOL_REGISTRY[tool_name]["rate_limit"]


def get_all_tool_schemas() -> list[Dict[str, Any]]:
    """
    Get OpenAI function schemas for all registered tools.

    Returns:
        List of tool schemas in OpenAI function calling format
    """
    schemas = []

    # add_task schema
    if "add_task" in TOOL_REGISTRY:
        schemas.append({
            "type": "function",
            "function": {
                "name": "add_task",
                "description": "Create a new task with optional priority and tags. Supports NLP extraction from title/description (e.g., 'urgent' → high priority, '#work' → work tag)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (must match JWT token)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Task title (1-200 characters)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional task description (max 1000 characters)"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Task priority (default: medium). Auto-detected from keywords: urgent/critical → high, normal → medium, someday → low"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Task tags (optional). Auto-extracted from patterns like 'with tags work', '#work', or 'tagged as work'"
                        }
                    },
                    "required": ["user_id", "title"]
                }
            }
        })

    # list_tasks schema
    if "list_tasks" in TOOL_REGISTRY:
        schemas.append({
            "type": "function",
            "function": {
                "name": "list_tasks",
                "description": "Get tasks with advanced filtering by priority, tags, search, and status. Supports natural language queries like 'show high priority work tasks'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (must match JWT token)"
                        },
                        "filter": {
                            "type": "string",
                            "enum": ["all", "pending", "completed"],
                            "description": "Filter tasks by completion status (default: all)"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Filter by priority level (optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags - returns tasks with any of the specified tags (optional)"
                        },
                        "search": {
                            "type": "string",
                            "description": "Search keyword for title/description (case-insensitive, optional)"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["created_at", "title", "priority"],
                            "description": "Field to sort by (default: created_at)"
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "Sort order (default: desc)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Natural language query for filtering (e.g., 'show high priority work tasks', 'find tasks about meeting'). Overrides other filters if provided."
                        }
                    },
                    "required": ["user_id"]
                }
            }
        })

    # complete_task schema
    if "complete_task" in TOOL_REGISTRY:
        schemas.append({
            "type": "function",
            "function": {
                "name": "complete_task",
                "description": "Toggle task completion status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (must match JWT token)"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "Task UUID to toggle completion"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            }
        })

    # delete_task schema
    if "delete_task" in TOOL_REGISTRY:
        schemas.append({
            "type": "function",
            "function": {
                "name": "delete_task",
                "description": "Delete a task permanently",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (must match JWT token)"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "Task UUID to delete"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            }
        })

    # update_task schema
    if "update_task" in TOOL_REGISTRY:
        schemas.append({
            "type": "function",
            "function": {
                "name": "update_task",
                "description": "Modify task properties including title, description, priority, and tags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (must match JWT token)"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "Task UUID to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New task title (optional, 1-200 characters)"
                        },
                        "description": {
                            "type": "string",
                            "description": "New task description (optional, max 1000 characters)"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "New task priority (optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New task tags (optional, replaces existing tags)"
                        }
                    },
                    "required": ["user_id", "task_id"]
                }
            }
        })

    return schemas


# Register tools
from app.mcp_server.tools.add_task import add_task
from app.mcp_server.tools.list_tasks import list_tasks
from app.mcp_server.tools.complete_task import complete_task
from app.mcp_server.tools.delete_task import delete_task
from app.mcp_server.tools.update_task import update_task

register_tool(
    name="add_task",
    handler=add_task,
    rate_limit="100/hour",
    description="Create a new task for the authenticated user"
)

register_tool(
    name="list_tasks",
    handler=list_tasks,
    rate_limit="1000/hour",
    description="Get all tasks for the authenticated user with optional filtering"
)

register_tool(
    name="complete_task",
    handler=complete_task,
    rate_limit="200/hour",
    description="Toggle task completion status"
)

register_tool(
    name="delete_task",
    handler=delete_task,
    rate_limit="100/hour",
    description="Permanently remove a task"
)

register_tool(
    name="update_task",
    handler=update_task,
    rate_limit="200/hour",
    description="Modify task title and/or description"
)
