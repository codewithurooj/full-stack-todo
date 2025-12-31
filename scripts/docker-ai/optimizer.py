"""Layer optimizer for docker-ai.

Optimizes Dockerfile layer caching for faster builds.
"""

import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LayerOptimizer:
    """Optimizes Dockerfile layers for better caching."""

    def __init__(self, config: Any):
        """Initialize layer optimizer.

        Args:
            config: Configuration object
        """
        self.config = config

    def optimize(self, dockerfile_path_or_content: Any) -> str:
        """Optimize Dockerfile layers.

        Args:
            dockerfile_path_or_content: Path to Dockerfile or content string

        Returns:
            Optimized Dockerfile content
        """
        # Read content
        if isinstance(dockerfile_path_or_content, str):
            if '\n' in dockerfile_path_or_content:
                content = dockerfile_path_or_content
            else:
                # Assume it's a path
                from pathlib import Path
                content = Path(dockerfile_path_or_content).read_text()
        else:
            content = dockerfile_path_or_content.read_text()

        lines = content.split('\n')
        optimized_lines = []

        for line in lines:
            optimized_line = self._optimize_line(line)
            optimized_lines.append(optimized_line)

        return '\n'.join(optimized_lines)

    def _optimize_line(self, line: str) -> str:
        """Optimize a single Dockerfile instruction.

        Args:
            line: Dockerfile line

        Returns:
            Optimized line
        """
        stripped = line.strip()

        # Combine multiple RUN commands (if applicable)
        # This is handled at generation time mostly

        # Add --no-cache flags to package managers
        if 'pip install' in stripped and '--no-cache-dir' not in stripped:
            line = line.replace('pip install', 'pip install --no-cache-dir')

        if 'apk add' in stripped and '--no-cache' not in stripped:
            line = line.replace('apk add', 'apk add --no-cache')

        if 'npm install' in stripped and 'npm ci' not in stripped:
            # Suggest npm ci for better caching
            line = line.replace('npm install', 'npm ci')

        # Clean up apt cache
        if 'apt-get install' in stripped and 'rm -rf /var/lib/apt/lists/*' not in stripped:
            if line.endswith('\\'):
                # Multi-line, don't modify
                pass
            else:
                line = line + ' && rm -rf /var/lib/apt/lists/*'

        return line

    def analyze_caching(self, dockerfile_content: str) -> Dict[str, Any]:
        """Analyze Dockerfile for caching efficiency.

        Args:
            dockerfile_content: Dockerfile content

        Returns:
            Analysis results
        """
        lines = dockerfile_content.split('\n')

        analysis = {
            'total_layers': 0,
            'cacheable_layers': 0,
            'suggestions': []
        }

        copy_before_deps = False
        has_separate_deps_copy = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Count layers
            if stripped.startswith(('FROM', 'RUN', 'COPY', 'ADD')):
                analysis['total_layers'] += 1

            # Check for COPY . before dependency installation
            if 'COPY . .' in stripped:
                # Check if deps were installed before
                prev_lines = lines[:i]
                if not any('requirements.txt' in l or 'package.json' in l for l in prev_lines):
                    copy_before_deps = True

            # Check for separate dependency copy
            if 'COPY requirements.txt' in stripped or 'COPY package' in stripped:
                has_separate_deps_copy = True
                analysis['cacheable_layers'] += 1

        # Generate suggestions
        if copy_before_deps and not has_separate_deps_copy:
            analysis['suggestions'].append(
                "Copy dependency files separately before 'COPY . .' to improve caching"
            )

        if analysis['cacheable_layers'] < 2:
            analysis['suggestions'].append(
                "Add more cacheable layers by separating dependency installation"
            )

        return analysis
