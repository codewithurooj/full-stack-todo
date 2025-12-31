"""Recommendation generator for kagent.

Generates actionable recommendations from findings.
"""

from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ai_provider import get_ai_provider
import logging

logger = logging.getLogger(__name__)


class RecommendationGenerator:
    """Generates actionable recommendations."""

    def __init__(self, config: Any):
        """Initialize recommendation generator.

        Args:
            config: Configuration object
        """
        self.config = config
        try:
            self.ai_provider = get_ai_provider(config)
        except Exception as e:
            logger.warning(f"AI provider not available: {e}")
            self.ai_provider = None

    def generate(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations from findings.

        Args:
            findings: List of prioritized findings

        Returns:
            List of recommendations
        """
        recommendations = []

        # Group findings by type
        by_type = {}
        for finding in findings:
            finding_type = finding.get('type', 'unknown')
            if finding_type not in by_type:
                by_type[finding_type] = []
            by_type[finding_type].append(finding)

        # Generate recommendations for each type
        for finding_type, type_findings in by_type.items():
            if len(type_findings) >= 3:  # Only create group recommendations for 3+ findings
                recommendations.append(self._create_group_recommendation(finding_type, type_findings))
            else:
                # Individual recommendations
                for finding in type_findings:
                    recommendations.append(self._create_individual_recommendation(finding))

        return recommendations

    def _create_group_recommendation(
        self,
        finding_type: str,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a group recommendation for multiple findings of same type."""
        severity = max((f.get('severity', 'low') for f in findings),
                      key=lambda s: FindingPrioritizer.SEVERITY_SCORES.get(s, 0))

        return {
            'type': 'group',
            'finding_type': finding_type,
            'severity': severity,
            'count': len(findings),
            'title': f'Fix {len(findings)} {finding_type.replace("_", " ")} issues',
            'description': findings[0].get('recommendation', ''),
            'affected_resources': [f.get('resource') for f in findings],
            'action': self._generate_bulk_action(finding_type, findings)
        }

    def _create_individual_recommendation(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Create recommendation for a single finding."""
        return {
            'type': 'individual',
            'finding_type': finding.get('type'),
            'severity': finding.get('severity'),
            'title': finding.get('description'),
            'description': finding.get('recommendation'),
            'affected_resource': finding.get('resource'),
            'namespace': finding.get('namespace'),
            'action': self._generate_action(finding)
        }

    def _generate_action(self, finding: Dict[str, Any]) -> str:
        """Generate actionable command for a finding."""
        finding_type = finding.get('type', '')
        resource = finding.get('resource', '')
        namespace = finding.get('namespace', 'default')

        # Generate kubectl command based on finding type
        if 'missing_liveness_probe' in finding_type:
            return f"kubectl edit {resource} -n {namespace}  # Add livenessProbe section"
        elif 'missing_readiness_probe' in finding_type:
            return f"kubectl edit {resource} -n {namespace}  # Add readinessProbe section"
        elif 'privileged' in finding_type:
            return f"kubectl edit {resource} -n {namespace}  # Set privileged: false"
        elif 'running_as_root' in finding_type:
            return f"kubectl edit {resource} -n {namespace}  # Add runAsNonRoot: true"
        elif 'missing_requests' in finding_type or 'missing_limits' in finding_type:
            return f"kubectl edit {resource} -n {namespace}  # Add resource requests and limits"
        else:
            return f"kubectl describe {resource} -n {namespace}"

    def _generate_bulk_action(self, finding_type: str, findings: List[Dict[str, Any]]) -> str:
        """Generate bulk action for multiple findings."""
        namespaces = set(f.get('namespace') for f in findings if f.get('namespace'))

        if len(namespaces) == 1:
            namespace = list(namespaces)[0]
            return f"# Review all resources in namespace {namespace} for {finding_type.replace('_', ' ')}"
        else:
            return f"# Review resources across {len(namespaces)} namespaces for {finding_type.replace('_', ' ')}"


class FindingPrioritizer:
    """Prioritizer class for severity scores."""
    SEVERITY_SCORES = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }
