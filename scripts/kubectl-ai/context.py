"""Command context manager for kubectl-ai session state.

Maintains conversation history and Kubernetes context across commands
to provide better AI responses.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime


class CommandContext:
    """Manages session state and conversation history."""

    def __init__(self, config: Any):
        """Initialize command context.

        Args:
            config: Configuration object
        """
        self.config = config
        self.context_dir = Path.home() / ".kubectl-ai" / "context"
        self.context_dir.mkdir(parents=True, exist_ok=True)

        # Session state
        self.current_namespace = "default"
        self.current_cluster = None
        self.conversation_history: List[Dict[str, str]] = []

        # Load persisted context if enabled
        if config.get('context_persistence', True):
            self._load_context()

    def _load_context(self) -> None:
        """Load persisted context from disk."""
        context_file = self.context_dir / "session.json"

        if context_file.exists():
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                    self.current_namespace = data.get('namespace', 'default')
                    self.current_cluster = data.get('cluster')
                    # Don't load old conversation history, start fresh each session
            except (json.JSONDecodeError, IOError):
                # If loading fails, just use defaults
                pass

    def _save_context(self) -> None:
        """Save context to disk for persistence."""
        context_file = self.context_dir / "session.json"

        data = {
            'namespace': self.current_namespace,
            'cluster': self.current_cluster,
            'last_updated': datetime.utcnow().isoformat()
        }

        with open(context_file, 'w') as f:
            json.dump(data, f, indent=2)

    def set_namespace(self, namespace: str) -> None:
        """Set current working namespace.

        Args:
            namespace: Kubernetes namespace
        """
        self.current_namespace = namespace
        self._save_context()

    def set_cluster(self, cluster: str) -> None:
        """Set current cluster context.

        Args:
            cluster: Cluster name
        """
        self.current_cluster = cluster
        self._save_context()

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
        """
        self.conversation_history.append({
            'role': role,
            'content': content
        })

        # Keep only last 10 messages to avoid context overflow
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history.

        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()

    def get_context_info(self) -> Dict[str, Any]:
        """Get current context information.

        Returns:
            Dictionary with context details
        """
        return {
            'namespace': self.current_namespace,
            'cluster': self.current_cluster,
            'history_length': len(self.conversation_history)
        }

    def get_system_prompt(self) -> str:
        """Get system prompt with current context.

        Returns:
            System prompt string with context
        """
        prompt = """You are kubectl-ai, an intelligent assistant for Kubernetes operations.
Your job is to help users interact with their Kubernetes cluster using natural language.

Current Context:
- Namespace: {namespace}
- Cluster: {cluster}

Guidelines:
1. Translate natural language queries into kubectl commands
2. Identify the operation type (get, create, update, delete, scale, etc.)
3. Extract resource type and name when mentioned
4. Use the current namespace unless user specifies otherwise
5. For destructive operations (delete, drain, etc.), mark them as requiring confirmation
6. Provide clear explanations for complex operations
7. Suggest diagnostic commands for troubleshooting

Output Format (JSON):
{{
  "operation": "get|create|delete|scale|update|describe|logs|etc",
  "resource_type": "pod|deployment|service|etc",
  "resource_name": "specific-name or null",
  "namespace": "namespace or null for current",
  "kubectl_command": "the actual kubectl command",
  "explanation": "brief explanation of what this does",
  "destructive": true/false
}}
""".format(
            namespace=self.current_namespace,
            cluster=self.current_cluster or "current context"
        )

        return prompt

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()

    def reset(self) -> None:
        """Reset context to defaults."""
        self.current_namespace = "default"
        self.current_cluster = None
        self.conversation_history.clear()
        self._save_context()
