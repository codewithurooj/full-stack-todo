# Phase 1: Data Models

## MCP Tool Request Models

### AddTaskRequest
```python
class AddTaskRequest(BaseModel):
    user_id: str
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
```

### ListTasksRequest
```python
class ListTasksRequest(BaseModel):
    user_id: str
    filter: Literal["all", "pending", "completed"] = "all"
    sort_by: Optional[Literal["created_at", "updated_at", "title"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = None
```

### CompleteTaskRequest
```python
class CompleteTaskRequest(BaseModel):
    user_id: str
    task_id: str = Field(regex=r"^[0-9a-f-]{36}$")  # UUID format
```

### DeleteTaskRequest
```python
class DeleteTaskRequest(BaseModel):
    user_id: str
    task_id: str = Field(regex=r"^[0-9a-f-]{36}$")
```

### UpdateTaskRequest
```python
class UpdateTaskRequest(BaseModel):
    user_id: str
    task_id: str = Field(regex=r"^[0-9a-f-]{36}$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('title', 'description')
    def at_least_one_field(cls, v, values):
        if not v and not values.get('title') and not values.get('description'):
            raise ValueError("At least one of title or description must be provided")
        return v
```

## Response Models

### TaskResponse
```python
class TaskResponse(BaseModel):
    task_id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime
```

### ListTasksResponse
```python
class ListTasksResponse(BaseModel):
    tasks: List[TaskResponse]
    count: int
    filter_applied: str
```

### DeleteTaskResponse
```python
class DeleteTaskResponse(BaseModel):
    task_id: str
    deleted: Literal[True]
    deleted_at: datetime
```

## Error Models

```python
class ErrorResponse(BaseModel):
    error: dict
    timestamp: datetime
```
