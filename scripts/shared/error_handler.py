"""Error handler with plain language explanations.

Converts technical errors into user-friendly messages with
actionable suggestions for resolution.
"""

from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
import logging

logger = logging.getLogger(__name__)
console = Console()


class ErrorHandler:
    """User-friendly error handler with suggestions."""

    # Common Kubernetes error patterns
    K8S_ERROR_PATTERNS = {
        'connection refused': {
            'title': 'Cannot Connect to Kubernetes Cluster',
            'explanation': 'Unable to connect to the Kubernetes API server.',
            'suggestions': [
                'Check if your cluster is running (minikube status, kind get clusters)',
                'Verify your kubeconfig file (~/.kube/config)',
                'Ensure kubectl context is set correctly (kubectl config current-context)',
                'Check if the API server is accessible from your network'
            ]
        },
        'not found': {
            'title': 'Resource Not Found',
            'explanation': 'The requested Kubernetes resource does not exist.',
            'suggestions': [
                'Verify the resource name is correct',
                'Check if you\'re in the right namespace (kubectl config view --minify)',
                'List available resources to confirm (kubectl get <resource-type>)',
                'The resource may have been deleted recently'
            ]
        },
        'unauthorized': {
            'title': 'Authentication Failed',
            'explanation': 'Your credentials are not authorized for this operation.',
            'suggestions': [
                'Check your kubeconfig authentication settings',
                'Verify you have the necessary RBAC permissions',
                'Try re-authenticating with your cluster',
                'Contact your cluster administrator for access'
            ]
        },
        'forbidden': {
            'title': 'Permission Denied',
            'explanation': 'You don\'t have permission to perform this operation.',
            'suggestions': [
                'Check your RBAC role bindings (kubectl describe rolebinding)',
                'Verify service account permissions if using one',
                'Contact your cluster administrator for required permissions',
                'Review the required permissions for this operation'
            ]
        },
        'timeout': {
            'title': 'Operation Timed Out',
            'explanation': 'The operation took too long to complete.',
            'suggestions': [
                'Check your network connection',
                'The cluster may be under heavy load',
                'Increase the timeout value if possible',
                'Check cluster health (kubectl get nodes, pods)'
            ]
        },
        'invalid': {
            'title': 'Invalid Configuration',
            'explanation': 'The configuration or request is invalid.',
            'suggestions': [
                'Review the error details for specific validation failures',
                'Check the Kubernetes API documentation for correct format',
                'Validate your YAML/JSON configuration',
                'Compare with working examples in the documentation'
            ]
        }
    }

    # AI provider error patterns
    AI_ERROR_PATTERNS = {
        'api_key': {
            'title': 'AI Provider API Key Error',
            'explanation': 'Invalid or missing API key for the AI provider.',
            'suggestions': [
                'Set the appropriate environment variable (OPENAI_API_KEY or ANTHROPIC_API_KEY)',
                'Verify your API key is valid and not expired',
                'Check for typos in the API key',
                'Generate a new API key from your provider dashboard'
            ]
        },
        'rate_limit': {
            'title': 'AI API Rate Limit Exceeded',
            'explanation': 'You have exceeded the rate limit for the AI API.',
            'suggestions': [
                'Wait a few minutes before retrying',
                'Consider upgrading your API plan for higher limits',
                'Reduce the frequency of requests',
                'Implement request batching or caching'
            ]
        },
        'quota': {
            'title': 'AI API Quota Exceeded',
            'explanation': 'You have used up your API quota or credits.',
            'suggestions': [
                'Check your account usage and billing',
                'Add credits or upgrade your plan',
                'Wait until your quota resets (usually monthly)',
                'Consider switching to a different AI provider'
            ]
        }
    }

    # Docker error patterns
    DOCKER_ERROR_PATTERNS = {
        'daemon': {
            'title': 'Docker Daemon Not Running',
            'explanation': 'Cannot connect to the Docker daemon.',
            'suggestions': [
                'Start Docker Desktop or Docker daemon',
                'Check if Docker service is running (systemctl status docker)',
                'Verify Docker socket permissions',
                'Restart Docker service if needed'
            ]
        },
        'image not found': {
            'title': 'Docker Image Not Found',
            'explanation': 'The specified Docker image does not exist.',
            'suggestions': [
                'Check the image name and tag are correct',
                'Pull the image first (docker pull <image>)',
                'Verify you have access to the image registry',
                'Check if the image exists in your registry'
            ]
        }
    }

    @staticmethod
    def handle_error(
        error: Exception,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle an error with user-friendly output.

        Args:
            error: The exception that occurred
            context: Additional context about what was being done
            metadata: Additional metadata for logging
        """
        error_msg = str(error).lower()

        # Find matching error pattern
        pattern_match = None
        error_info = None

        for pattern, info in ErrorHandler.K8S_ERROR_PATTERNS.items():
            if pattern in error_msg:
                pattern_match = pattern
                error_info = info
                break

        if not error_info:
            for pattern, info in ErrorHandler.AI_ERROR_PATTERNS.items():
                if pattern in error_msg:
                    pattern_match = pattern
                    error_info = info
                    break

        if not error_info:
            for pattern, info in ErrorHandler.DOCKER_ERROR_PATTERNS.items():
                if pattern in error_msg:
                    pattern_match = pattern
                    error_info = info
                    break

        # Display error
        console.print()

        if error_info:
            # Display friendly error with suggestions
            console.print(Panel.fit(
                f"[bold red]{error_info['title']}[/bold red]",
                border_style="red"
            ))

            console.print(f"\n[bold]What happened:[/bold]")
            console.print(f"{error_info['explanation']}\n")

            if context:
                console.print(f"[bold]Context:[/bold] {context}\n")

            console.print(f"[bold]Technical error:[/bold] [dim]{error}[/dim]\n")

            console.print(f"[bold]What to try:[/bold]")
            for i, suggestion in enumerate(error_info['suggestions'], 1):
                console.print(f"  {i}. {suggestion}")

        else:
            # Display generic error
            console.print(Panel.fit(
                f"[bold red]Error Occurred[/bold red]",
                border_style="red"
            ))

            if context:
                console.print(f"\n[bold]Context:[/bold] {context}")

            console.print(f"\n[bold]Error:[/bold] {error}\n")

            console.print("[bold]What to try:[/bold]")
            console.print("  1. Check the error message above for details")
            console.print("  2. Review the documentation for this operation")
            console.print("  3. Enable debug logging for more information")
            console.print("  4. Check the audit log for related operations")

        console.print()

        # Log error
        logger.error(
            f"Error: {error}",
            extra={
                'context': context,
                'pattern': pattern_match,
                'metadata': metadata or {}
            }
        )

    @staticmethod
    def handle_kubectl_error(error: Exception, command: str) -> None:
        """Handle kubectl command errors.

        Args:
            error: The exception that occurred
            command: The kubectl command that failed
        """
        ErrorHandler.handle_error(
            error,
            context=f"Executing kubectl command: {command}",
            metadata={'command': command}
        )

    @staticmethod
    def handle_ai_error(error: Exception, operation: str) -> None:
        """Handle AI provider errors.

        Args:
            error: The exception that occurred
            operation: The AI operation that failed
        """
        ErrorHandler.handle_error(
            error,
            context=f"AI operation: {operation}",
            metadata={'operation': operation}
        )

    @staticmethod
    def handle_docker_error(error: Exception, operation: str) -> None:
        """Handle Docker errors.

        Args:
            error: The exception that occurred
            operation: The Docker operation that failed
        """
        ErrorHandler.handle_error(
            error,
            context=f"Docker operation: {operation}",
            metadata={'operation': operation}
        )

    @staticmethod
    def display_warning(message: str, suggestions: Optional[list] = None) -> None:
        """Display a warning message.

        Args:
            message: Warning message
            suggestions: Optional list of suggestions
        """
        console.print()
        console.print(Panel.fit(
            f"[bold yellow]⚠ Warning[/bold yellow]",
            border_style="yellow"
        ))

        console.print(f"\n{message}\n")

        if suggestions:
            console.print("[bold]Recommendations:[/bold]")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"  {i}. {suggestion}")
            console.print()

    @staticmethod
    def display_success(message: str) -> None:
        """Display a success message.

        Args:
            message: Success message
        """
        console.print(f"\n[green]✓ {message}[/green]\n")

    @staticmethod
    def display_info(message: str) -> None:
        """Display an informational message.

        Args:
            message: Info message
        """
        console.print(f"\n[blue]ℹ {message}[/blue]\n")
