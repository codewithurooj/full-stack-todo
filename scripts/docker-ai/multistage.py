"""Multi-stage build generator for docker-ai.

Creates multi-stage Dockerfiles for optimized image sizes.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MultiStageBuilder:
    """Generates multi-stage Docker builds."""

    def __init__(self, config: Any):
        """Initialize multi-stage builder.

        Args:
            config: Configuration object
        """
        self.config = config

    def create_stages(
        self,
        language: str,
        base_images: Dict[str, str],
        dependencies: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Create build stages.

        Args:
            language: Programming language
            base_images: Dict with 'build' and 'runtime' images
            dependencies: List of dependencies

        Returns:
            List of stage definitions
        """
        if language in ['go', 'rust']:
            # Compiled languages: build + runtime
            return self._create_compiled_stages(language, base_images)
        else:
            # Interpreted languages: dependencies + runtime
            return self._create_interpreted_stages(language, base_images, dependencies)

    def _create_compiled_stages(
        self,
        language: str,
        base_images: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Create stages for compiled languages."""
        stages = []

        # Build stage
        if language == 'go':
            stages.append({
                'name': 'builder',
                'base': base_images['build'],
                'steps': [
                    'WORKDIR /build',
                    'COPY go.mod go.sum ./',
                    'RUN go mod download',
                    'COPY . .',
                    'RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .',
                ]
            })

            # Runtime stage
            stages.append({
                'name': 'runtime',
                'base': base_images['runtime'],
                'steps': [
                    'WORKDIR /app',
                    'COPY --from=builder /build/app .',
                    'EXPOSE 8080',
                    'CMD ["./app"]',
                ]
            })

        elif language == 'rust':
            stages.append({
                'name': 'builder',
                'base': base_images['build'],
                'steps': [
                    'WORKDIR /build',
                    'COPY Cargo.toml Cargo.lock ./',
                    'RUN mkdir src && echo "fn main() {}" > src/main.rs',
                    'RUN cargo build --release',
                    'COPY . .',
                    'RUN cargo build --release',
                ]
            })

            stages.append({
                'name': 'runtime',
                'base': base_images['runtime'],
                'steps': [
                    'WORKDIR /app',
                    'COPY --from=builder /build/target/release/app .',
                    'CMD ["./app"]',
                ]
            })

        return stages

    def _create_interpreted_stages(
        self,
        language: str,
        base_images: Dict[str, str],
        dependencies: List[str]
    ) -> List[Dict[str, Any]]:
        """Create stages for interpreted languages."""
        stages = []

        # Single stage for interpreted languages (can be optimized with deps stage)
        if language == 'python':
            stages.append({
                'name': 'runtime',
                'base': base_images['runtime'],
                'steps': []  # Will be filled by generator
            })

        elif language in ['javascript', 'typescript']:
            # Dependencies stage
            stages.append({
                'name': 'dependencies',
                'base': base_images['build'],
                'steps': [
                    'WORKDIR /app',
                    'COPY package*.json ./',
                    'RUN npm ci --only=production',
                ]
            })

            # Runtime stage
            stages.append({
                'name': 'runtime',
                'base': base_images['runtime'],
                'steps': [
                    'WORKDIR /app',
                    'COPY --from=dependencies /app/node_modules ./node_modules',
                    'COPY . .',
                ]
            })

        return stages

    def should_use_multistage(self, language: str) -> bool:
        """Determine if multi-stage is beneficial.

        Args:
            language: Programming language

        Returns:
            True if multi-stage build is recommended
        """
        # Compiled languages always benefit
        if language in ['go', 'rust', 'java', 'csharp']:
            return True

        # Node.js benefits from dependency caching
        if language in ['javascript', 'typescript']:
            return True

        # Python can benefit but less critical
        if language == 'python':
            return self.config.get('enable_multistage', True)

        return False
