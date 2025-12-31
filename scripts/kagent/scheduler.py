"""Analysis scheduler for kagent.

Schedules periodic cluster health analysis.
"""

import time
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.audit import AuditLog
import logging

logger = logging.getLogger(__name__)


class AnalysisScheduler:
    """Schedules periodic cluster analysis."""

    def __init__(self, config: Any, audit_log: AuditLog):
        """Initialize scheduler.

        Args:
            config: Configuration object
            audit_log: Audit log instance
        """
        self.config = config
        self.audit_log = audit_log
        self.running = False

    def start(self, interval: int = 3600, namespace: Optional[str] = None) -> None:
        """Start scheduled analysis.

        Args:
            interval: Analysis interval in seconds (default: 1 hour)
            namespace: Optional namespace to monitor
        """
        self.running = True

        logger.info(f"Starting scheduled analysis (interval: {interval}s)")

        while self.running:
            try:
                self._run_analysis(namespace)
                logger.info(f"Analysis complete. Next run in {interval}s")

                # Wait for next interval
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def _run_analysis(self, namespace: Optional[str] = None) -> None:
        """Run a single analysis cycle."""
        from health_scanner import ClusterHealthScanner
        from resource_analyzer import ResourceAnalyzer
        from config_checker import ConfigurationChecker
        from security_scanner import SecurityScanner
        from performance_analyzer import PerformanceAnalyzer
        from history import AnalysisHistory

        logger.info(f"Running scheduled analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run scans
        health_scanner = ClusterHealthScanner(self.config)
        resource_analyzer = ResourceAnalyzer(self.config)
        config_checker = ConfigurationChecker(self.config)
        security_scanner = SecurityScanner(self.config)
        performance_analyzer = PerformanceAnalyzer(self.config)

        health_findings = health_scanner.scan(namespace=namespace)
        resource_findings = resource_analyzer.analyze(namespace=namespace)
        config_findings = config_checker.check(namespace=namespace)
        security_findings = security_scanner.scan(namespace=namespace)
        performance_findings = performance_analyzer.analyze(namespace=namespace)

        # Combine findings
        all_findings = (
            health_findings +
            resource_findings +
            config_findings +
            security_findings +
            performance_findings
        )

        # Save to history
        history = AnalysisHistory("kagent")
        history.save({
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'scheduled',
            'namespace': namespace or 'all',
            'findings_count': len(all_findings),
            'critical': len([f for f in all_findings if f.get('severity') == 'critical']),
            'high': len([f for f in all_findings if f.get('severity') == 'high']),
            'medium': len([f for f in all_findings if f.get('severity') == 'medium']),
            'low': len([f for f in all_findings if f.get('severity') == 'low']),
            'findings': all_findings
        })

        # Log to audit
        self.audit_log.log_analysis(
            analysis_type='scheduled_analysis',
            findings_count=len(all_findings),
            critical_count=len([f for f in all_findings if f.get('severity') == 'critical']),
            high_count=len([f for f in all_findings if f.get('severity') == 'high']),
            medium_count=len([f for f in all_findings if f.get('severity') == 'medium']),
            low_count=len([f for f in all_findings if f.get('severity') == 'low'])
        )

        logger.info(f"Found {len(all_findings)} issues")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
