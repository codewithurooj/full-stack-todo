"""kagent: AI-powered Kubernetes cluster health analysis and recommendations.

Continuously monitors cluster health, detects issues, and provides
actionable recommendations for optimization, security, and reliability.
"""

import click
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config
from shared.logger import setup_logger
from shared.audit import AuditLog
from shared.env import EnvConfig, validate_tool_env
from shared.error_handler import ErrorHandler
from rich.console import Console
from rich.table import Table

console = Console()
logger = setup_logger("kagent")


@click.group()
@click.version_option(version="0.1.0")
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """kagent: AI-powered Kubernetes cluster health analysis.

    Analyze cluster health, detect issues, and get actionable recommendations.

    Examples:
      kagent analyze                    # Run full cluster analysis
      kagent scan security              # Security-focused scan
      kagent report --format markdown   # Generate health report
      kagent history                    # View analysis history
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Setup logging
    if debug:
        logger.setLevel("DEBUG")

    # Initialize configuration
    try:
        config = Config("kagent")
        env_config = EnvConfig("kagent")

        if not validate_tool_env("kagent"):
            console.print("[red]Configuration validation failed[/red]")
            console.print("Run 'kagent config' to check your setup")
            sys.exit(1)

        ctx.obj['config'] = config
        ctx.obj['env_config'] = env_config
        ctx.obj['audit_log'] = AuditLog("kagent")

    except Exception as e:
        ErrorHandler.handle_error(e, "Initializing kagent")
        sys.exit(1)


@cli.command()
@click.option('--namespace', '-n', help='Analyze specific namespace only')
@click.option('--output', '-o', type=click.Choice(['json', 'markdown', 'text']), default='text',
              help='Output format')
@click.option('--save', is_flag=True, help='Save report to file')
@click.pass_context
def analyze(ctx, namespace, output, save):
    """Run comprehensive cluster health analysis.

    Performs a full analysis including:
    - Resource utilization
    - Security vulnerabilities
    - Configuration best practices
    - Performance issues
    - Cost optimization opportunities

    Examples:
      kagent analyze
      kagent analyze --namespace production
      kagent analyze --output markdown --save
    """
    console.print("\n[bold]Starting Cluster Health Analysis...[/bold]\n")

    try:
        from health_scanner import ClusterHealthScanner
        from resource_analyzer import ResourceAnalyzer
        from config_checker import ConfigurationChecker
        from security_scanner import SecurityScanner
        from performance_analyzer import PerformanceAnalyzer
        from prioritizer import FindingPrioritizer
        from recommendations import RecommendationGenerator
        from reporter import ReportGenerator

        # Initialize components
        health_scanner = ClusterHealthScanner(ctx.obj['config'])
        resource_analyzer = ResourceAnalyzer(ctx.obj['config'])
        config_checker = ConfigurationChecker(ctx.obj['config'])
        security_scanner = SecurityScanner(ctx.obj['config'])
        performance_analyzer = PerformanceAnalyzer(ctx.obj['config'])

        # Run scans
        console.print("[cyan]→[/cyan] Scanning cluster health...")
        health_findings = health_scanner.scan(namespace=namespace)

        console.print("[cyan]→[/cyan] Analyzing resource utilization...")
        resource_findings = resource_analyzer.analyze(namespace=namespace)

        console.print("[cyan]→[/cyan] Checking configuration...")
        config_findings = config_checker.check(namespace=namespace)

        console.print("[cyan]→[/cyan] Scanning for security issues...")
        security_findings = security_scanner.scan(namespace=namespace)

        console.print("[cyan]→[/cyan] Analyzing performance...")
        performance_findings = performance_analyzer.analyze(namespace=namespace)

        # Combine all findings
        all_findings = (
            health_findings +
            resource_findings +
            config_findings +
            security_findings +
            performance_findings
        )

        console.print(f"\n[bold]Found {len(all_findings)} issues[/bold]\n")

        # Prioritize findings
        prioritizer = FindingPrioritizer(ctx.obj['config'])
        prioritized = prioritizer.prioritize(all_findings)

        # Generate recommendations
        rec_generator = RecommendationGenerator(ctx.obj['config'])
        recommendations = rec_generator.generate(prioritized)

        # Generate report
        report_gen = ReportGenerator(ctx.obj['config'])
        report = report_gen.generate(
            findings=prioritized,
            recommendations=recommendations,
            format=output
        )

        # Display or save report
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kagent_report_{timestamp}.{output}"
            report_gen.save(report, filename)
            console.print(f"\n[green]✓ Report saved to {filename}[/green]")
        else:
            console.print(report)

        # Log analysis
        ctx.obj['audit_log'].log_analysis(
            analysis_type='full_cluster',
            findings_count=len(all_findings),
            critical_count=len([f for f in all_findings if f.get('severity') == 'critical']),
            high_count=len([f for f in all_findings if f.get('severity') == 'high']),
            medium_count=len([f for f in all_findings if f.get('severity') == 'medium']),
            low_count=len([f for f in all_findings if f.get('severity') == 'low'])
        )

    except Exception as e:
        ErrorHandler.handle_error(e, "Running cluster analysis")
        sys.exit(1)


@cli.command()
@click.argument('scan_type', type=click.Choice(['security', 'resources', 'config', 'performance', 'health']))
@click.option('--namespace', '-n', help='Scan specific namespace only')
@click.pass_context
def scan(ctx, scan_type, namespace):
    """Run a focused scan on specific aspect.

    Scan types:
      security     - Security vulnerabilities and RBAC issues
      resources    - Resource utilization and efficiency
      config       - Configuration best practices
      performance  - Performance bottlenecks
      health       - Overall cluster health

    Examples:
      kagent scan security
      kagent scan resources --namespace production
    """
    console.print(f"\n[bold]Running {scan_type} scan...[/bold]\n")

    try:
        findings = []

        if scan_type == 'security':
            from security_scanner import SecurityScanner
            scanner = SecurityScanner(ctx.obj['config'])
            findings = scanner.scan(namespace=namespace)

        elif scan_type == 'resources':
            from resource_analyzer import ResourceAnalyzer
            analyzer = ResourceAnalyzer(ctx.obj['config'])
            findings = analyzer.analyze(namespace=namespace)

        elif scan_type == 'config':
            from config_checker import ConfigurationChecker
            checker = ConfigurationChecker(ctx.obj['config'])
            findings = checker.check(namespace=namespace)

        elif scan_type == 'performance':
            from performance_analyzer import PerformanceAnalyzer
            analyzer = PerformanceAnalyzer(ctx.obj['config'])
            findings = analyzer.analyze(namespace=namespace)

        elif scan_type == 'health':
            from health_scanner import ClusterHealthScanner
            scanner = ClusterHealthScanner(ctx.obj['config'])
            findings = scanner.scan(namespace=namespace)

        # Display findings
        _display_findings(findings)

        # Log scan
        ctx.obj['audit_log'].log_analysis(
            analysis_type=f'{scan_type}_scan',
            findings_count=len(findings),
            critical_count=len([f for f in findings if f.get('severity') == 'critical']),
            high_count=len([f for f in findings if f.get('severity') == 'high'])
        )

    except Exception as e:
        ErrorHandler.handle_error(e, f"Running {scan_type} scan")
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'text']), default='markdown',
              help='Report format')
@click.option('--save', is_flag=True, help='Save report to file')
@click.pass_context
def report(ctx, format, save):
    """Generate cluster health report from latest analysis.

    Examples:
      kagent report
      kagent report --format json
      kagent report --format markdown --save
    """
    try:
        from history import AnalysisHistory

        history = AnalysisHistory("kagent")
        latest = history.get_latest()

        if not latest:
            console.print("[yellow]No analysis data found. Run 'kagent analyze' first.[/yellow]")
            return

        from reporter import ReportGenerator
        report_gen = ReportGenerator(ctx.obj['config'])

        report = report_gen.generate(
            findings=latest['findings'],
            recommendations=latest.get('recommendations', []),
            format=format
        )

        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kagent_report_{timestamp}.{format}"
            report_gen.save(report, filename)
            console.print(f"\n[green]✓ Report saved to {filename}[/green]")
        else:
            console.print(report)

    except Exception as e:
        ErrorHandler.handle_error(e, "Generating report")
        sys.exit(1)


@cli.command()
@click.option('--limit', default=10, help='Number of entries to show')
@click.pass_context
def history(ctx, limit):
    """View analysis history.

    Examples:
      kagent history
      kagent history --limit 20
    """
    try:
        from history import AnalysisHistory

        history = AnalysisHistory("kagent")
        entries = history.get_all(limit=limit)

        if not entries:
            console.print("[yellow]No analysis history found.[/yellow]")
            return

        table = Table(title="Analysis History")
        table.add_column("Date", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Findings", style="white")
        table.add_column("Critical", style="red")
        table.add_column("High", style="yellow")

        for entry in entries:
            table.add_row(
                entry['timestamp'],
                entry.get('type', 'full'),
                str(entry.get('findings_count', 0)),
                str(entry.get('critical', 0)),
                str(entry.get('high', 0))
            )

        console.print(table)

    except Exception as e:
        ErrorHandler.handle_error(e, "Viewing history")
        sys.exit(1)


@cli.command()
@click.option('--interval', default=3600, help='Scan interval in seconds')
@click.option('--namespace', '-n', help='Namespace to monitor')
@click.pass_context
def monitor(ctx, interval, namespace):
    """Start continuous monitoring (scheduled analysis).

    Examples:
      kagent monitor                      # Every hour
      kagent monitor --interval 1800      # Every 30 minutes
      kagent monitor --namespace prod     # Monitor specific namespace
    """
    console.print(f"\n[bold]Starting continuous monitoring (interval: {interval}s)...[/bold]\n")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

    try:
        from scheduler import AnalysisScheduler

        scheduler = AnalysisScheduler(ctx.obj['config'], ctx.obj['audit_log'])
        scheduler.start(interval=interval, namespace=namespace)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
    except Exception as e:
        ErrorHandler.handle_error(e, "Running continuous monitoring")
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


def _display_findings(findings):
    """Display findings in a formatted table."""
    if not findings:
        console.print("[green]✓ No issues found![/green]")
        return

    # Group by severity
    by_severity = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }

    for finding in findings:
        severity = finding.get('severity', 'low')
        by_severity[severity].append(finding)

    # Display summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Critical: [red]{len(by_severity['critical'])}[/red]")
    console.print(f"  High:     [yellow]{len(by_severity['high'])}[/yellow]")
    console.print(f"  Medium:   {len(by_severity['medium'])}")
    console.print(f"  Low:      {len(by_severity['low'])}\n")

    # Display findings table
    table = Table(title="Findings")
    table.add_column("Severity", style="bold")
    table.add_column("Type", style="cyan")
    table.add_column("Resource", style="white")
    table.add_column("Description", style="white")

    # Show critical and high first
    for severity in ['critical', 'high', 'medium', 'low']:
        for finding in by_severity[severity][:5]:  # Show top 5 per severity
            severity_style = {
                'critical': '[red]CRITICAL[/red]',
                'high': '[yellow]HIGH[/yellow]',
                'medium': '[blue]MEDIUM[/blue]',
                'low': '[dim]LOW[/dim]'
            }

            table.add_row(
                severity_style.get(severity, severity),
                finding.get('type', 'Unknown'),
                finding.get('resource', 'N/A'),
                finding.get('description', '')[:60] + '...'
            )

    console.print(table)
    console.print()


def main():
    """Entry point for kagent CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
