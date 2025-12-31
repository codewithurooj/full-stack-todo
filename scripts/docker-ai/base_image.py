"""Base image selector for docker-ai.

Selects optimal base images for different languages and use cases.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaseImageSelector:
    """Selects optimal Docker base images."""

    # Base images for different languages
    BASE_IMAGES = {
        'python': {
            'alpine': 'python:3.13-alpine',
            'slim': 'python:3.13-slim',
            'full': 'python:3.13',
            'distroless': 'gcr.io/distroless/python3',
        },
        'javascript': {
            'alpine': 'node:20-alpine',
            'slim': 'node:20-slim',
            'full': 'node:20',
        },
        'typescript': {
            'alpine': 'node:20-alpine',
            'slim': 'node:20-slim',
            'full': 'node:20',
        },
        'go': {
            'alpine': 'golang:1.21-alpine',
            'full': 'golang:1.21',
            'scratch': 'scratch',  # For final stage
        },
        'java': {
            'alpine': 'openjdk:21-alpine',
            'slim': 'openjdk:21-slim',
            'full': 'openjdk:21',
        },
        'ruby': {
            'alpine': 'ruby:3.3-alpine',
            'slim': 'ruby:3.3-slim',
            'full': 'ruby:3.3',
        },
        'php': {
            'alpine': 'php:8.3-alpine',
            'fpm': 'php:8.3-fpm',
            'apache': 'php:8.3-apache',
        },
        'rust': {
            'alpine': 'rust:1.75-alpine',
            'slim': 'rust:1.75-slim',
            'full': 'rust:1.75',
        },
    }

    def __init__(self, config: Any):
        """Initialize base image selector.

        Args:
            config: Configuration object
        """
        self.config = config
        self.prefer_alpine = config.get('default_base_image', 'alpine') == 'alpine'

    def select(
        self,
        language: str,
        framework: str = None,
        optimize_size: bool = True
    ) -> Dict[str, str]:
        """Select base images for build and runtime.

        Args:
            language: Programming language
            framework: Framework (optional)
            optimize_size: Whether to optimize for size

        Returns:
            Dictionary with 'build' and 'runtime' images
        """
        if language not in self.BASE_IMAGES:
            logger.warning(f"Unknown language: {language}, using Python")
            language = 'python'

        images = self.BASE_IMAGES[language]

        # Select build image
        build_image = images.get('full', images.get('alpine'))

        # Select runtime image
        if optimize_size and 'alpine' in images:
            runtime_image = images['alpine']
        elif optimize_size and 'slim' in images:
            runtime_image = images['slim']
        elif 'distroless' in images:
            runtime_image = images['distroless']
        else:
            runtime_image = images.get('alpine', images.get('slim', build_image))

        # Special cases for compiled languages
        if language == 'go':
            if optimize_size:
                runtime_image = 'alpine:latest'  # or scratch for static binaries
            build_image = images.get('alpine', images.get('full'))

        elif language == 'rust':
            if optimize_size:
                runtime_image = 'debian:bookworm-slim'
            build_image = images.get('full')

        return {
            'build': build_image,
            'runtime': runtime_image
        }

    def get_package_manager(self, language: str, image: str) -> str:
        """Get package manager for given language and image.

        Args:
            language: Programming language
            image: Docker image

        Returns:
            Package manager command
        """
        if 'alpine' in image:
            return 'apk add --no-cache'
        elif 'debian' in image or 'ubuntu' in image:
            return 'apt-get update && apt-get install -y'
        elif language == 'python':
            return 'pip install --no-cache-dir'
        elif language in ['javascript', 'typescript']:
            return 'npm install'
        elif language == 'go':
            return 'go get'
        elif language == 'ruby':
            return 'bundle install'
        elif language == 'php':
            return 'composer install'
        else:
            return 'apk add --no-cache'

    def get_recommended_packages(self, language: str, framework: str = None) -> List[str]:
        """Get recommended system packages.

        Args:
            language: Programming language
            framework: Framework (optional)

        Returns:
            List of package names
        """
        packages = []

        if language == 'python':
            packages = ['gcc', 'musl-dev', 'libffi-dev', 'openssl-dev']
            if framework == 'django':
                packages.extend(['postgresql-dev'])

        elif language in ['javascript', 'typescript']:
            packages = ['python3', 'make', 'g++']  # For native modules

        elif language == 'ruby':
            packages = ['build-base', 'postgresql-dev']

        elif language == 'php':
            packages = ['libpng-dev', 'libjpeg-dev', 'libzip-dev']

        return packages
