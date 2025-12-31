"""Report generator for kagent.

Generates cluster health reports in JSON, Markdown, and text formats.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates cluster health reports."""

    def __init__(self, config: Any):
        """Initialize report generator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.report_dir = Path.home() / ".kagent" / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        format: str = 'markdown'
    ) -> str:
        """Generate report.

        Args:
            findings: List of findings
            recommendations: List of recommendations
            format: Output format (json, markdown, text)

        Returns:
            Formatted report string
        """
        if format == 'json':
            return self._generate_json(findings, recommendations)
        elif format == 'markdown':
            return self._generate_markdown(findings, recommendations)
        else:
            return self._generate_text(findings, recommendations)

    def _generate_json(
        self,
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate JSON report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': self._generate_summary(findings),
            'findings': findings,
            'recommendations': recommendations
        }
        return json.dumps(report, indent=2)

    def _generate_markdown(
        self,
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate Markdown report."""
        lines = []

        # Header
        lines.append("# Kubernetes Cluster Health Report")
        lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary
        summary = self._generate_summary(findings)
        lines.append("## Summary\n")
        lines.append(f"- **Total Issues**: {summary['total']}")
        lines.append(f"- **Critical**: {summary['critical']}")
        lines.append(f"- **High**: {summary['high']}")
        lines.append(f"- **Medium**: {summary['medium']}")
        lines.append(f"- **Low**: {summary['low']}\n")

        # Recommendations
        if recommendations:
            lines.append("## Priority Recommendations\n")
            for i, rec in enumerate(recommendations[:10], 1):
                severity = rec.get('severity', 'medium')
                emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '⚪'}.get(severity, '⚪')
                lines.append(f"### {i}. {emoji} {rec.get('title', 'Unknown')}\n")
                lines.append(f"**Severity**: {severity.upper()}\n")

                if rec.get('type') == 'group':
                    lines.append(f"**Affected Resources**: {rec.get('count', 0)} resources\n")
                else:
                    lines.append(f"**Resource**: `{rec.get('affected_resource', 'N/A')}`\n")
                    if rec.get('namespace'):
                        lines.append(f"**Namespace**: `{rec['namespace']}`\n")

                lines.append(f"**Description**: {rec.get('description', 'No description')}\n")

                if rec.get('action'):
                    lines.append(f"**Action**:\n```bash\n{rec['action']}\n```\n")

        # Findings by Category
        lines.append("## Detailed Findings\n")
        by_category = self._group_by_type(findings)

        for category, category_findings in sorted(by_category.items()):
            lines.append(f"### {category.replace('_', ' ').title()}\n")
            for finding in category_findings[:5]:  # Top 5 per category
                lines.append(f"- **{finding.get('severity', 'low').upper()}**: {finding.get('description', 'No description')}")
                if finding.get('resource'):
                    lines.append(f"  - Resource: `{finding['resource']}`")
                if finding.get('namespace'):
                    lines.append(f"  - Namespace: `{finding['namespace']}`")
                lines.append("")

        return '\n'.join(lines)

    def _generate_text(
        self,
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate plain text report."""
        lines = []

        lines.append("=" * 60)
        lines.append("KUBERNETES CLUSTER HEALTH REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        summary = self._generate_summary(findings)
        lines.append("SUMMARY")
        lines.append("-" * 60)
        lines.append(f"Total Issues:    {summary['total']}")
        lines.append(f"Critical:        {summary['critical']}")
        lines.append(f"High:            {summary['high']}")
        lines.append(f"Medium:          {summary['medium']}")
        lines.append(f"Low:             {summary['low']}")
        lines.append("")

        # Top Recommendations
        if recommendations:
            lines.append("PRIORITY RECOMMENDATIONS")
            lines.append("-" * 60)
            for i, rec in enumerate(recommendations[:10], 1):
                lines.append(f"{i}. [{rec.get('severity', 'medium').upper()}] {rec.get('title', 'Unknown')}")
                if rec.get('affected_resource'):
                    lines.append(f"   Resource: {rec['affected_resource']}")
                if rec.get('namespace'):
                    lines.append(f"   Namespace: {rec['namespace']}")
                lines.append("")

        return '\n'.join(lines)

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate summary statistics."""
        summary = {
            'total': len(findings),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for finding in findings:
            severity = finding.get('severity', 'low')
            summary[severity] = summary.get(severity, 0) + 1

        return summary

    def _group_by_type(self, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group findings by type."""
        by_type = {}
        for finding in findings:
            finding_type = finding.get('type', 'unknown')
            if finding_type not in by_type:
                by_type[finding_type] = []
            by_type[finding_type].append(finding)
        return by_type

    def save(self, report: str, filename: str) -> None:
        """Save report to file.

        Args:
            report: Report content
            filename: Output filename
        """
        filepath = self.report_dir / filename

        with open(filepath, 'w') as f:
            f.write(report)

        logger.info(f"Report saved to {filepath}")
