"""Audit logging system for command tracking.

Records all operations for compliance, troubleshooting, and security auditing.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()


class AuditLog:
    """Audit logging system for tracking operations."""

    def __init__(self, tool_name: str, audit_dir: Optional[Path] = None):
        """Initialize audit log.

        Args:
            tool_name: Name of the tool
            audit_dir: Directory for audit logs (default: ~/.{tool_name}/audit)
        """
        self.tool_name = tool_name
        self.audit_dir = audit_dir or (Path.home() / f".{tool_name}" / "audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Separate log files by date for easier management
        today = datetime.now().strftime("%Y-%m-%d")
        self.current_log = self.audit_dir / f"audit-{today}.jsonl"

    def log(
        self,
        operation: str,
        operation_type: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        namespace: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an operation to the audit trail.

        Args:
            operation: Operation performed
            operation_type: Type of operation (create, read, update, delete, execute)
            resource_type: Type of resource affected
            resource_name: Name of resource affected
            namespace: Kubernetes namespace
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata
        """
        timestamp = datetime.utcnow()

        audit_entry = {
            'timestamp': timestamp.isoformat(),
            'tool': self.tool_name,
            'operation': operation,
            'operation_type': operation_type,
            'success': success,
        }

        if resource_type:
            audit_entry['resource_type'] = resource_type
        if resource_name:
            audit_entry['resource_name'] = resource_name
        if namespace:
            audit_entry['namespace'] = namespace
        if error:
            audit_entry['error'] = error
        if metadata:
            audit_entry['metadata'] = metadata

        # Write to log file
        with open(self.current_log, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

    def log_kubectl_command(
        self,
        command: str,
        success: bool = True,
        output: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Log a kubectl command execution.

        Args:
            command: kubectl command executed
            success: Whether command succeeded
            output: Command output
            error: Error message if failed
        """
        metadata = {'command': command}
        if output:
            metadata['output'] = output[:500]  # Truncate long output

        self.log(
            operation=f"kubectl: {command}",
            operation_type='execute',
            success=success,
            error=error,
            metadata=metadata
        )

    def log_analysis(
        self,
        analysis_type: str,
        findings_count: int,
        critical_count: int = 0,
        high_count: int = 0,
        medium_count: int = 0,
        low_count: int = 0
    ) -> None:
        """Log a cluster analysis operation.

        Args:
            analysis_type: Type of analysis performed
            findings_count: Total number of findings
            critical_count: Number of critical findings
            high_count: Number of high priority findings
            medium_count: Number of medium priority findings
            low_count: Number of low priority findings
        """
        metadata = {
            'findings_count': findings_count,
            'critical': critical_count,
            'high': high_count,
            'medium': medium_count,
            'low': low_count,
        }

        self.log(
            operation=f"Analysis: {analysis_type}",
            operation_type='read',
            success=True,
            metadata=metadata
        )

    def log_dockerfile_generation(
        self,
        project_path: str,
        language: str,
        framework: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Log a Dockerfile generation operation.

        Args:
            project_path: Path to project
            language: Detected language
            framework: Detected framework
            success: Whether generation succeeded
            error: Error message if failed
        """
        metadata = {
            'project_path': project_path,
            'language': language,
        }
        if framework:
            metadata['framework'] = framework

        self.log(
            operation="Generate Dockerfile",
            operation_type='create',
            success=success,
            error=error,
            metadata=metadata
        )

    def get_entries(
        self,
        days: int = 7,
        operation_type: Optional[str] = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get audit log entries.

        Args:
            days: Number of days to look back
            operation_type: Filter by operation type
            success_only: Only return successful operations

        Returns:
            List of audit entries
        """
        entries = []
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all log files within the time range
        for log_file in sorted(self.audit_dir.glob("audit-*.jsonl")):
            # Parse date from filename
            try:
                file_date_str = log_file.stem.replace("audit-", "")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    continue

                # Read entries from file
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)

                            # Apply filters
                            if operation_type and entry.get('operation_type') != operation_type:
                                continue
                            if success_only and not entry.get('success', True):
                                continue

                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue

            except ValueError:
                # Skip files with invalid date format
                continue

        return entries

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get audit statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        entries = self.get_entries(days=days)

        total = len(entries)
        successful = sum(1 for e in entries if e.get('success', True))
        failed = total - successful

        # Count by operation type
        by_type = {}
        for entry in entries:
            op_type = entry.get('operation_type', 'unknown')
            by_type[op_type] = by_type.get(op_type, 0) + 1

        return {
            'total_operations': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'by_type': by_type,
            'period_days': days,
        }

    def display_recent(self, limit: int = 20) -> None:
        """Display recent audit entries in a formatted table.

        Args:
            limit: Maximum number of entries to display
        """
        entries = self.get_entries(days=7)[-limit:]

        if not entries:
            console.print("[yellow]No audit entries found[/yellow]")
            return

        table = Table(title=f"Recent Audit Log ({self.tool_name})")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Operation", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")

        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            status = "[green]✓[/green]" if entry.get('success', True) else "[red]✗[/red]"

            table.add_row(
                time_str,
                entry.get('operation', 'Unknown'),
                entry.get('operation_type', 'unknown'),
                status
            )

        console.print(table)

    def display_statistics(self, days: int = 7) -> None:
        """Display audit statistics.

        Args:
            days: Number of days to analyze
        """
        stats = self.get_statistics(days)

        console.print(f"\n[bold]Audit Statistics (Last {days} days)[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Operations", str(stats['total_operations']))
        table.add_row("Successful", f"[green]{stats['successful']}[/green]")
        table.add_row("Failed", f"[red]{stats['failed']}[/red]")
        table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")

        console.print(table)

        if stats['by_type']:
            console.print("\n[bold]By Operation Type:[/bold]\n")
            type_table = Table(show_header=True)
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="white")

            for op_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                type_table.add_row(op_type, str(count))

            console.print(type_table)

        console.print()
