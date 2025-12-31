"""Security hardener for docker-ai.

Applies security best practices to Dockerfiles.
"""

import re
from typing import List
import logging

logger = logging.getLogger(__name__)


class SecurityHardener:
    """Applies security hardening to Dockerfiles."""

    def __init__(self, config: Any):
        """Initialize security hardener.

        Args:
            config: Configuration object
        """
        self.config = config

    def harden(self, dockerfile_content: str) -> str:
        """Apply security hardening to Dockerfile.

        Args:
            dockerfile_content: Original Dockerfile content

        Returns:
            Hardened Dockerfile content
        """
        lines = dockerfile_content.split('\n')
        hardened_lines = []

        has_user = any('USER' in line and not line.strip().startswith('#') for line in lines)
        has_healthcheck = any('HEALTHCHECK' in line for line in lines)
        base_image = None

        for line in lines:
            # Track base image
            if line.strip().startswith('FROM'):
                base_image = line

            hardened_lines.append(line)

        # Add non-root user if missing
        if not has_user:
            # Find position to insert (before EXPOSE or CMD)
            insert_pos = len(hardened_lines)
            for i, line in enumerate(hardened_lines):
                if 'EXPOSE' in line or 'CMD' in line or 'ENTRYPOINT' in line:
                    insert_pos = i
                    break

            # Determine if alpine or debian-based
            is_alpine = base_image and 'alpine' in base_image.lower()

            user_lines = [
                "",
                "# Security: Create non-root user"
            ]

            if is_alpine:
                user_lines.extend([
                    "RUN addgroup -S appgroup && adduser -S appuser -G appgroup",
                    "RUN chown -R appuser:appgroup /app",
                    "USER appuser"
                ])
            else:
                user_lines.extend([
                    "RUN groupadd -r appgroup && useradd -r -g appgroup appuser",
                    "RUN chown -R appuser:appgroup /app",
                    "USER appuser"
                ])

            hardened_lines[insert_pos:insert_pos] = user_lines

        # Apply additional hardening
        return '\n'.join(hardened_lines)

    def check_security(self, dockerfile_content: str) -> List[str]:
        """Check Dockerfile for security issues.

        Args:
            dockerfile_content: Dockerfile content

        Returns:
            List of security issues found
        """
        issues = []
        lines = dockerfile_content.split('\n')

        has_user = False
        uses_latest = False
        has_secrets = False

        for line in lines:
            line_stripped = line.strip()

            # Check for USER directive
            if line_stripped.startswith('USER') and 'USER root' not in line_stripped:
                has_user = True

            # Check for :latest tag
            if line_stripped.startswith('FROM') and ':latest' in line_stripped:
                uses_latest = True

            # Check for potential secrets
            if 'PASSWORD' in line_stripped or 'SECRET' in line_stripped or 'API_KEY' in line_stripped:
                if '=' in line_stripped:
                    has_secrets = True

        if not has_user:
            issues.append("No non-root USER directive found")

        if uses_latest:
            issues.append("Using :latest tag is not recommended for reproducibility")

        if has_secrets:
            issues.append("Potential hardcoded secrets detected")

        return issues
