"""Finding prioritizer for kagent.

Prioritizes findings by severity, impact, and urgency.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FindingPrioritizer:
    """Prioritizes findings for actionable recommendations."""

    SEVERITY_SCORES = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }

    def __init__(self, config: Any):
        """Initialize prioritizer.

        Args:
            config: Configuration object
        """
        self.config = config

    def prioritize(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize findings by severity and impact.

        Args:
            findings: List of findings

        Returns:
            Sorted list of findings (highest priority first)
        """
        # Add priority score to each finding
        for finding in findings:
            finding['priority_score'] = self._calculate_priority(finding)

        # Sort by priority score (descending)
        sorted_findings = sorted(
            findings,
            key=lambda x: x.get('priority_score', 0),
            reverse=True
        )

        return sorted_findings

    def _calculate_priority(self, finding: Dict[str, Any]) -> int:
        """Calculate priority score for a finding.

        Args:
            finding: Finding dictionary

        Returns:
            Priority score (0-100)
        """
        base_score = self.SEVERITY_SCORES.get(
            finding.get('severity', 'low'),
            25
        )

        # Boost priority for certain types
        finding_type = finding.get('type', '')

        # Security issues get boost
        if 'security' in finding_type or 'privileged' in finding_type or 'secret' in finding_type:
            base_score += 10

        # Production namespace gets boost
        if finding.get('namespace') == 'production':
            base_score += 5

        # System components get boost
        if finding.get('namespace') == 'kube-system':
            base_score += 5

        return min(base_score, 100)
