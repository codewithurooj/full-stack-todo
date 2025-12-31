"""Confirmation prompt system for destructive operations.

Provides interactive confirmation for potentially dangerous operations
to prevent accidental data loss or service disruption.
"""

from typing import Optional, List
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table
import logging

logger = logging.getLogger(__name__)
console = Console()


class ConfirmationPrompt:
    """Interactive confirmation system for operations."""

    DESTRUCTIVE_OPERATIONS = {
        'delete': 'Delete',
        'remove': 'Remove',
        'destroy': 'Destroy',
        'terminate': 'Terminate',
        'scale_down': 'Scale down',
        'drain': 'Drain',
        'evict': 'Evict',
    }

    def __init__(self, require_confirmation: bool = True):
        """Initialize confirmation prompt.

        Args:
            require_confirmation: Whether to require confirmation
        """
        self.require_confirmation = require_confirmation

    def is_destructive(self, operation: str) -> bool:
        """Check if an operation is destructive.

        Args:
            operation: Operation name

        Returns:
            True if operation is destructive
        """
        operation_lower = operation.lower()
        return any(
            keyword in operation_lower
            for keyword in self.DESTRUCTIVE_OPERATIONS.keys()
        )

    def confirm_operation(
        self,
        operation: str,
        resource_type: str,
        resource_name: str,
        namespace: Optional[str] = None,
        additional_info: Optional[dict] = None
    ) -> bool:
        """Prompt user to confirm an operation.

        Args:
            operation: Operation to perform
            resource_type: Type of resource (pod, deployment, etc.)
            resource_name: Name of the resource
            namespace: Kubernetes namespace (if applicable)
            additional_info: Additional details to display

        Returns:
            True if confirmed, False otherwise
        """
        # Skip confirmation if not required
        if not self.require_confirmation:
            return True

        # Always confirm destructive operations
        if not self.is_destructive(operation):
            return True

        # Display operation details
        console.print()
        console.print(Panel.fit(
            f"[bold yellow]⚠ Destructive Operation Detected[/bold yellow]",
            border_style="yellow"
        ))

        # Create details table
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Operation", f"[bold red]{operation}[/bold red]")
        table.add_row("Resource Type", resource_type)
        table.add_row("Resource Name", resource_name)

        if namespace:
            table.add_row("Namespace", namespace)

        if additional_info:
            for key, value in additional_info.items():
                table.add_row(key, str(value))

        console.print(table)
        console.print()

        # Get confirmation
        confirmed = Confirm.ask(
            "[bold]Do you want to proceed?[/bold]",
            default=False
        )

        if confirmed:
            logger.info(
                f"User confirmed {operation} for {resource_type}/{resource_name}"
            )
            console.print("[green]✓ Operation confirmed[/green]\n")
        else:
            logger.info(
                f"User cancelled {operation} for {resource_type}/{resource_name}"
            )
            console.print("[yellow]✗ Operation cancelled[/yellow]\n")

        return confirmed

    def confirm_kubectl_command(
        self,
        command: str,
        explanation: Optional[str] = None
    ) -> bool:
        """Confirm execution of a kubectl command.

        Args:
            command: kubectl command to execute
            explanation: Optional explanation of what the command does

        Returns:
            True if confirmed, False otherwise
        """
        # Check if command is destructive
        destructive_keywords = ['delete', 'remove', 'destroy', 'drain', 'cordon']
        is_destructive = any(
            keyword in command.lower()
            for keyword in destructive_keywords
        )

        # Skip confirmation for non-destructive operations
        if not is_destructive and not self.require_confirmation:
            return True

        # Display command details
        console.print()
        if is_destructive:
            console.print(Panel.fit(
                f"[bold yellow]⚠ Destructive kubectl Command[/bold yellow]",
                border_style="yellow"
            ))
        else:
            console.print(Panel.fit(
                f"[bold blue]kubectl Command[/bold blue]",
                border_style="blue"
            ))

        console.print(f"\n[bold]Command:[/bold] [cyan]{command}[/cyan]\n")

        if explanation:
            console.print(f"[bold]Explanation:[/bold] {explanation}\n")

        # Get confirmation
        if is_destructive:
            confirmed = Confirm.ask(
                "[bold]Do you want to execute this command?[/bold]",
                default=False
            )
        else:
            confirmed = Confirm.ask(
                "[bold]Execute this command?[/bold]",
                default=True
            )

        if confirmed:
            logger.info(f"User confirmed kubectl command: {command}")
            console.print("[green]✓ Command will be executed[/green]\n")
        else:
            logger.info(f"User cancelled kubectl command: {command}")
            console.print("[yellow]✗ Command cancelled[/yellow]\n")

        return confirmed

    def confirm_batch_operation(
        self,
        operation: str,
        resources: List[dict],
        dry_run: bool = False
    ) -> bool:
        """Confirm a batch operation affecting multiple resources.

        Args:
            operation: Operation to perform
            resources: List of resource dicts with 'type', 'name', 'namespace'
            dry_run: Whether this is a dry run

        Returns:
            True if confirmed, False otherwise
        """
        # Display batch operation details
        console.print()
        console.print(Panel.fit(
            f"[bold yellow]⚠ Batch Operation: {operation}[/bold yellow]",
            border_style="yellow"
        ))

        console.print(f"\n[bold]Affected Resources ({len(resources)}):[/bold]\n")

        # Create resources table
        table = Table()
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Namespace", style="yellow")

        for resource in resources[:10]:  # Show first 10
            table.add_row(
                resource.get('type', 'Unknown'),
                resource.get('name', 'Unknown'),
                resource.get('namespace', 'default')
            )

        console.print(table)

        if len(resources) > 10:
            console.print(f"\n[dim]... and {len(resources) - 10} more[/dim]\n")

        if dry_run:
            console.print("[yellow]This is a DRY RUN - no changes will be made[/yellow]\n")

        # Get confirmation
        confirmed = Confirm.ask(
            f"[bold]Proceed with {operation} on {len(resources)} resources?[/bold]",
            default=False
        )

        if confirmed:
            logger.info(f"User confirmed batch {operation} on {len(resources)} resources")
            console.print("[green]✓ Batch operation confirmed[/green]\n")
        else:
            logger.info(f"User cancelled batch {operation}")
            console.print("[yellow]✗ Batch operation cancelled[/yellow]\n")

        return confirmed
