"""kubectl-ai: Natural language interface for Kubernetes operations.

Translates natural language commands into kubectl operations and executes them
with user confirmation for destructive operations.
"""

import click
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config
from shared.logger import setup_logger
from shared.audit import AuditLog
from shared.env import EnvConfig, validate_tool_env
from shared.error_handler import ErrorHandler
from rich.console import Console

console = Console()
logger = setup_logger("kubectl-ai")


@click.group()
@click.version_option(version="0.1.0")
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """kubectl-ai: Natural language Kubernetes operations.

    Transform natural language into kubectl commands with AI assistance.

    Examples:
      kubectl-ai "list all pods"
      kubectl-ai "scale nginx deployment to 5 replicas"
      kubectl-ai troubleshoot "why is my pod crashing?"
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Setup logging
    if debug:
        logger.setLevel("DEBUG")

    # Initialize configuration
    try:
        config = Config("kubectl-ai")
        env_config = EnvConfig("kubectl-ai")

        if not validate_tool_env("kubectl-ai"):
            console.print("[red]Configuration validation failed[/red]")
            console.print("Run 'kubectl-ai config' to check your setup")
            sys.exit(1)

        ctx.obj['config'] = config
        ctx.obj['env_config'] = env_config
        ctx.obj['audit_log'] = AuditLog("kubectl-ai")

    except Exception as e:
        ErrorHandler.handle_error(e, "Initializing kubectl-ai")
        sys.exit(1)


@cli.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show command without executing')
@click.option('--no-confirm', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def execute(ctx, query, dry_run, no_confirm):
    """Execute a natural language Kubernetes command.

    Examples:
      kubectl-ai execute "list all pods in default namespace"
      kubectl-ai execute "scale deployment nginx to 3 replicas"
      kubectl-ai execute "delete pod failing-pod" --dry-run
    """
    query_str = ' '.join(query)

    console.print(f"\n[bold]Natural Language Query:[/bold] {query_str}\n")

    try:
        from nl_parser import NaturalLanguageParser
        from translator import KubectlTranslator
        from executor import CommandExecutor

        # Parse natural language to intent
        parser = NaturalLanguageParser(ctx.obj['config'])
        intent = parser.parse(query_str)

        console.print(f"[bold]Detected Intent:[/bold] {intent['operation']}")
        console.print(f"[bold]Target:[/bold] {intent.get('resource_type', 'N/A')}\n")

        # Translate to kubectl command
        translator = KubectlTranslator(ctx.obj['config'])
        kubectl_cmd = translator.translate(intent)

        console.print(f"[bold]kubectl Command:[/bold] [cyan]{kubectl_cmd}[/cyan]\n")

        # Execute command
        if not dry_run:
            executor = CommandExecutor(
                ctx.obj['config'],
                ctx.obj['audit_log'],
                require_confirmation=not no_confirm
            )
            result = executor.execute(kubectl_cmd, intent)

            if result['success']:
                console.print("[green]✓ Command executed successfully[/green]\n")
                if result.get('output'):
                    console.print(result['output'])
            else:
                console.print(f"[red]✗ Command failed: {result.get('error')}[/red]\n")
        else:
            console.print("[yellow]Dry run - command not executed[/yellow]\n")

    except Exception as e:
        ErrorHandler.handle_error(e, f"Executing query: {query_str}")
        sys.exit(1)


@cli.command()
@click.argument('problem', nargs=-1, required=True)
@click.pass_context
def troubleshoot(ctx, problem):
    """Troubleshoot Kubernetes issues using AI analysis.

    Examples:
      kubectl-ai troubleshoot "pod keeps restarting"
      kubectl-ai troubleshoot "service not accessible"
    """
    problem_str = ' '.join(problem)

    console.print(f"\n[bold]Troubleshooting:[/bold] {problem_str}\n")

    try:
        from troubleshooter import KubectlTroubleshooter

        troubleshooter = KubectlTroubleshooter(ctx.obj['config'])
        analysis = troubleshooter.analyze(problem_str)

        console.print("[bold]Analysis:[/bold]")
        console.print(analysis['explanation'])
        console.print()

        if analysis.get('suggestions'):
            console.print("[bold]Suggested Actions:[/bold]")
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                console.print(f"  {i}. {suggestion}")
            console.print()

        if analysis.get('commands'):
            console.print("[bold]Diagnostic Commands:[/bold]")
            for cmd in analysis['commands']:
                console.print(f"  • {cmd}")
            console.print()

    except Exception as e:
        ErrorHandler.handle_error(e, f"Troubleshooting: {problem_str}")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Display current configuration."""
    try:
        ctx.obj['env_config'].display_config()
    except Exception as e:
        ErrorHandler.handle_error(e, "Displaying configuration")
        sys.exit(1)


@cli.command()
@click.option('--limit', default=20, help='Number of recent entries to show')
@click.pass_context
def audit(ctx, limit):
    """Display audit log."""
    try:
        ctx.obj['audit_log'].display_recent(limit)
    except Exception as e:
        ErrorHandler.handle_error(e, "Displaying audit log")
        sys.exit(1)


@cli.command()
@click.option('--days', default=7, help='Number of days to analyze')
@click.pass_context
def stats(ctx, days):
    """Display usage statistics."""
    try:
        ctx.obj['audit_log'].display_statistics(days)
    except Exception as e:
        ErrorHandler.handle_error(e, "Displaying statistics")
        sys.exit(1)


def main():
    """Entry point for kubectl-ai CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
