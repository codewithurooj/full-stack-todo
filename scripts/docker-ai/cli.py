"""docker-ai (Gordon): AI-powered Dockerfile generation and optimization.

Generates optimized, secure Dockerfiles from natural language descriptions
or by analyzing project code. Supports multi-stage builds, security hardening,
and layer optimization.
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
logger = setup_logger("docker-ai")


@click.group()
@click.version_option(version="0.1.0")
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """docker-ai: AI-powered Dockerfile generation.

    Generate optimized Dockerfiles from natural language or code analysis.

    Examples:
      docker-ai generate "Python Flask app with Redis"
      docker-ai analyze /path/to/project
      docker-ai optimize ./Dockerfile
      docker-ai compose "Flask API with PostgreSQL"
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Setup logging
    if debug:
        logger.setLevel("DEBUG")

    # Initialize configuration
    try:
        config = Config("docker-ai")
        env_config = EnvConfig("docker-ai")

        if not validate_tool_env("docker-ai"):
            console.print("[red]Configuration validation failed[/red]")
            console.print("Run 'docker-ai config' to check your setup")
            sys.exit(1)

        ctx.obj['config'] = config
        ctx.obj['env_config'] = env_config
        ctx.obj['audit_log'] = AuditLog("docker-ai")

    except Exception as e:
        ErrorHandler.handle_error(e, "Initializing docker-ai")
        sys.exit(1)


@cli.command()
@click.argument('description', nargs=-1, required=True)
@click.option('--output', '-o', default='Dockerfile', help='Output filename')
@click.option('--multistage/--no-multistage', default=True, help='Use multi-stage builds')
@click.option('--security/--no-security', default=True, help='Apply security hardening')
@click.option('--optimize/--no-optimize', default=True, help='Optimize layer caching')
@click.pass_context
def generate(ctx, description, output, multistage, security, optimize):
    """Generate Dockerfile from natural language description.

    Examples:
      docker-ai generate "Python Flask application"
      docker-ai generate "Node.js Express API with MongoDB"
      docker-ai generate "Go web server with PostgreSQL" -o Dockerfile.go
    """
    description_str = ' '.join(description)

    console.print(f"\n[bold]Generating Dockerfile...[/bold]")
    console.print(f"Description: {description_str}\n")

    try:
        from nl_processor import NaturalLanguageProcessor
        from generator import DockerfileGenerator

        # Process natural language
        nl_processor = NaturalLanguageProcessor(ctx.obj['config'])
        spec = nl_processor.process(description_str)

        console.print(f"[cyan]→[/cyan] Detected: {spec.get('language', 'Unknown')} application")
        if spec.get('framework'):
            console.print(f"[cyan]→[/cyan] Framework: {spec['framework']}")
        console.print()

        # Generate Dockerfile
        generator = DockerfileGenerator(
            ctx.obj['config'],
            multistage=multistage,
            security=security,
            optimize=optimize
        )

        dockerfile_content = generator.generate_from_spec(spec)

        # Save to file
        output_path = Path(output)
        with open(output_path, 'w') as f:
            f.write(dockerfile_content)

        console.print(f"[green]✓ Dockerfile generated: {output_path}[/green]\n")

        # Show preview
        console.print("[bold]Preview:[/bold]")
        console.print("-" * 60)
        console.print(dockerfile_content)
        console.print("-" * 60)

        # Log generation
        ctx.obj['audit_log'].log_dockerfile_generation(
            project_path=str(output_path.parent),
            language=spec.get('language', 'unknown'),
            framework=spec.get('framework'),
            success=True
        )

    except Exception as e:
        ErrorHandler.handle_error(e, f"Generating Dockerfile from: {description_str}")
        sys.exit(1)


@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='Dockerfile', help='Output filename')
@click.option('--multistage/--no-multistage', default=True, help='Use multi-stage builds')
@click.option('--security/--no-security', default=True, help='Apply security hardening')
@click.pass_context
def analyze(ctx, project_path, output, multistage, security):
    """Analyze project and generate Dockerfile.

    Scans project files to detect language, framework, and dependencies,
    then generates an optimized Dockerfile.

    Examples:
      docker-ai analyze .
      docker-ai analyze /path/to/project
      docker-ai analyze ./backend -o Dockerfile.backend
    """
    project_path = Path(project_path).resolve()

    console.print(f"\n[bold]Analyzing project...[/bold]")
    console.print(f"Path: {project_path}\n")

    try:
        from code_analyzer import CodeAnalyzer
        from generator import DockerfileGenerator

        # Analyze code
        analyzer = CodeAnalyzer(ctx.obj['config'])
        analysis = analyzer.analyze(project_path)

        console.print(f"[cyan]→[/cyan] Language: {analysis.get('language', 'Unknown')}")
        console.print(f"[cyan]→[/cyan] Framework: {analysis.get('framework', 'None detected')}")
        console.print(f"[cyan]→[/cyan] Dependencies: {len(analysis.get('dependencies', []))} found")
        console.print()

        # Generate Dockerfile
        generator = DockerfileGenerator(
            ctx.obj['config'],
            multistage=multistage,
            security=security
        )

        dockerfile_content = generator.generate_from_analysis(analysis, project_path)

        # Save to file
        output_path = project_path / output
        with open(output_path, 'w') as f:
            f.write(dockerfile_content)

        console.print(f"[green]✓ Dockerfile generated: {output_path}[/green]\n")

        # Show preview
        console.print("[bold]Preview:[/bold]")
        console.print("-" * 60)
        console.print(dockerfile_content)
        console.print("-" * 60)

        # Log analysis
        ctx.obj['audit_log'].log_dockerfile_generation(
            project_path=str(project_path),
            language=analysis.get('language', 'unknown'),
            framework=analysis.get('framework'),
            success=True
        )

    except Exception as e:
        ErrorHandler.handle_error(e, f"Analyzing project: {project_path}")
        sys.exit(1)


@cli.command()
@click.argument('dockerfile_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output filename (default: overwrite)')
@click.pass_context
def optimize(ctx, dockerfile_path, output):
    """Optimize existing Dockerfile.

    Analyzes Dockerfile and applies optimizations:
    - Layer caching improvements
    - Multi-stage builds
    - Security hardening
    - Size reduction

    Examples:
      docker-ai optimize ./Dockerfile
      docker-ai optimize ./Dockerfile -o Dockerfile.optimized
    """
    dockerfile_path = Path(dockerfile_path).resolve()

    console.print(f"\n[bold]Optimizing Dockerfile...[/bold]")
    console.print(f"Input: {dockerfile_path}\n")

    try:
        from analyzer import DockerfileAnalyzer
        from optimizer import LayerOptimizer
        from security import SecurityHardener

        # Analyze current Dockerfile
        analyzer = DockerfileAnalyzer(ctx.obj['config'])
        analysis = analyzer.analyze_file(dockerfile_path)

        console.print("[cyan]Analysis Results:[/cyan]")
        console.print(f"  Issues found: {len(analysis.get('issues', []))}")
        console.print(f"  Optimization opportunities: {len(analysis.get('optimizations', []))}")
        console.print()

        # Apply optimizations
        optimizer = LayerOptimizer(ctx.obj['config'])
        hardener = SecurityHardener(ctx.obj['config'])

        optimized_content = optimizer.optimize(dockerfile_path)
        optimized_content = hardener.harden(optimized_content)

        # Save to file
        output_path = Path(output) if output else dockerfile_path
        with open(output_path, 'w') as f:
            f.write(optimized_content)

        console.print(f"[green]✓ Dockerfile optimized: {output_path}[/green]\n")

        # Show improvements
        if analysis.get('suggestions'):
            console.print("[bold]Applied improvements:[/bold]")
            for suggestion in analysis['suggestions'][:5]:
                console.print(f"  • {suggestion}")
            console.print()

    except Exception as e:
        ErrorHandler.handle_error(e, f"Optimizing Dockerfile: {dockerfile_path}")
        sys.exit(1)


@cli.command()
@click.argument('description', nargs=-1, required=True)
@click.option('--output', '-o', default='docker-compose.yml', help='Output filename')
@click.pass_context
def compose(ctx, description, output):
    """Generate docker-compose.yml from description.

    Examples:
      docker-ai compose "Flask API with PostgreSQL and Redis"
      docker-ai compose "Node.js app with MongoDB" -o compose.yaml
    """
    description_str = ' '.join(description)

    console.print(f"\n[bold]Generating docker-compose.yml...[/bold]")
    console.print(f"Description: {description_str}\n")

    try:
        from nl_processor import NaturalLanguageProcessor
        from compose_generator import ComposeGenerator

        # Process description
        nl_processor = NaturalLanguageProcessor(ctx.obj['config'])
        spec = nl_processor.process(description_str)

        # Generate docker-compose.yml
        compose_gen = ComposeGenerator(ctx.obj['config'])
        compose_content = compose_gen.generate(spec)

        # Save to file
        output_path = Path(output)
        with open(output_path, 'w') as f:
            f.write(compose_content)

        console.print(f"[green]✓ docker-compose.yml generated: {output_path}[/green]\n")

        # Show preview
        console.print("[bold]Preview:[/bold]")
        console.print("-" * 60)
        console.print(compose_content)
        console.print("-" * 60)

    except Exception as e:
        ErrorHandler.handle_error(e, f"Generating docker-compose: {description_str}")
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


def main():
    """Entry point for docker-ai CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
