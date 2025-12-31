"""Dockerfile analyzer for docker-ai.

Analyzes existing Dockerfiles for improvements and best practices.
"""

from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DockerfileAnalyzer:
    """Analyzes Dockerfiles for improvements."""

    def __init__(self, config: Any):
        """Initialize Dockerfile analyzer.

        Args:
            config: Configuration object
        """
        self.config = config

    def analyze_file(self, dockerfile_path: Path) -> Dict[str, Any]:
        """Analyze a Dockerfile.

        Args:
            dockerfile_path: Path to Dockerfile

        Returns:
            Analysis results
        """
        content = Path(dockerfile_path).read_text()
        return self.analyze_content(content)

    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze Dockerfile content.

        Args:
            content: Dockerfile content

        Returns:
            Analysis results
        """
        lines = content.split('\n')

        analysis = {
            'issues': [],
            'optimizations': [],
            'suggestions': [],
            'security_issues': [],
            'best_practices': []
        }

        # Track state
        has_user = False
        has_healthcheck = False
        has_multistage = False
        uses_cache_flags = True
        layer_count = 0
        base_image_pinned = True

        for line in lines:
            stripped = line.strip()

            # Count layers
            if stripped.startswith(('FROM', 'RUN', 'COPY', 'ADD')):
                layer_count += 1

            # Check FROM
            if stripped.startswith('FROM'):
                if ' AS ' in stripped:
                    has_multistage = True

                if ':latest' in stripped:
                    base_image_pinned = False
                    analysis['issues'].append({
                        'type': 'base_image',
                        'severity': 'medium',
                        'message': 'Using :latest tag - pin to specific version for reproducibility'
                    })

            # Check USER
            if stripped.startswith('USER'):
                if 'root' not in stripped:
                    has_user = True

            # Check HEALTHCHECK
            if stripped.startswith('HEALTHCHECK'):
                has_healthcheck = True

            # Check cache flags
            if 'pip install' in stripped and '--no-cache-dir' not in stripped:
                uses_cache_flags = False
                analysis['optimizations'].append({
                    'type': 'caching',
                    'message': 'Add --no-cache-dir to pip install for smaller images'
                })

            if 'apk add' in stripped and '--no-cache' not in stripped:
                uses_cache_flags = False
                analysis['optimizations'].append({
                    'type': 'caching',
                    'message': 'Add --no-cache to apk add for smaller images'
                })

            # Check for apt-get without cleanup
            if 'apt-get install' in stripped and 'rm -rf /var/lib/apt/lists/*' not in content:
                analysis['optimizations'].append({
                    'type': 'size',
                    'message': 'Clean apt cache after install to reduce image size'
                })

            # Check for COPY . . before dependencies
            if 'COPY . .' in stripped:
                # This should come after dependency installation
                pass

        # Security checks
        if not has_user:
            analysis['security_issues'].append({
                'severity': 'high',
                'message': 'No non-root USER directive - container runs as root'
            })

        # Best practices
        if not has_healthcheck:
            analysis['best_practices'].append({
                'message': 'Add HEALTHCHECK instruction for better container monitoring'
            })

        if not has_multistage and layer_count > 10:
            analysis['best_practices'].append({
                'message': 'Consider multi-stage build to reduce final image size'
            })

        # Summary
        analysis['summary'] = {
            'total_issues': len(analysis['issues']) + len(analysis['security_issues']),
            'layer_count': layer_count,
            'has_user': has_user,
            'has_healthcheck': has_healthcheck,
            'has_multistage': has_multistage
        }

        # Generate suggestions
        analysis['suggestions'] = self._generate_suggestions(analysis)

        return analysis

    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable suggestions.

        Args:
            analysis: Analysis results

        Returns:
            List of suggestions
        """
        suggestions = []

        if analysis['security_issues']:
            suggestions.append("Add non-root USER directive for better security")

        if analysis['optimizations']:
            suggestions.append("Apply package manager cache optimizations")

        if not analysis['summary']['has_healthcheck']:
            suggestions.append("Add HEALTHCHECK for container health monitoring")

        if not analysis['summary']['has_multistage']:
            suggestions.append("Consider multi-stage build for smaller images")

        return suggestions
