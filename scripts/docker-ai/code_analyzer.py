"""Code analyzer for docker-ai.

Analyzes project code to detect language, framework, and dependencies.
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes project code to determine language and framework."""

    # File patterns for language detection
    LANGUAGE_PATTERNS = {
        'python': ['*.py', 'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
        'javascript': ['*.js', 'package.json', 'yarn.lock', 'package-lock.json'],
        'typescript': ['*.ts', 'tsconfig.json'],
        'go': ['*.go', 'go.mod', 'go.sum'],
        'java': ['*.java', 'pom.xml', 'build.gradle', 'build.gradle.kts'],
        'ruby': ['*.rb', 'Gemfile', 'Gemfile.lock'],
        'php': ['*.php', 'composer.json'],
        'rust': ['*.rs', 'Cargo.toml', 'Cargo.lock'],
        'csharp': ['*.cs', '*.csproj', '*.sln'],
        'cpp': ['*.cpp', '*.hpp', 'CMakeLists.txt'],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'python': {
            'flask': ['flask', 'Flask'],
            'django': ['django', 'Django', 'manage.py'],
            'fastapi': ['fastapi', 'FastAPI'],
            'streamlit': ['streamlit'],
        },
        'javascript': {
            'express': ['express'],
            'react': ['react', 'react-dom'],
            'vue': ['vue'],
            'next': ['next'],
            'nest': ['@nestjs'],
        },
        'typescript': {
            'express': ['express'],
            'nest': ['@nestjs'],
            'next': ['next'],
        },
        'go': {
            'gin': ['github.com/gin-gonic/gin'],
            'echo': ['github.com/labstack/echo'],
            'fiber': ['github.com/gofiber/fiber'],
        },
        'java': {
            'spring': ['spring-boot', 'springframework'],
            'quarkus': ['quarkus'],
        }
    }

    def __init__(self, config: Any):
        """Initialize code analyzer.

        Args:
            config: Configuration object
        """
        self.config = config

    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project to detect language and framework.

        Args:
            project_path: Path to project directory

        Returns:
            Analysis results
        """
        project_path = Path(project_path)

        if not project_path.is_dir():
            raise ValueError(f"Path is not a directory: {project_path}")

        # Detect language
        language = self._detect_language(project_path)

        # Detect framework
        framework = self._detect_framework(project_path, language)

        # Analyze dependencies
        dependencies = self._analyze_dependencies(project_path, language)

        # Detect entry point
        entry_point = self._detect_entry_point(project_path, language, framework)

        # Detect ports
        ports = self._detect_ports(project_path, language, framework)

        return {
            'language': language,
            'framework': framework,
            'dependencies': dependencies,
            'entry_point': entry_point,
            'ports': ports,
            'project_path': str(project_path)
        }

    def _detect_language(self, project_path: Path) -> str:
        """Detect programming language."""
        scores = {}

        for language, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if '*' in pattern:
                    # Glob pattern
                    matches = list(project_path.rglob(pattern))
                    score += len(matches)
                else:
                    # Exact file match
                    if (project_path / pattern).exists():
                        score += 5  # Higher weight for specific files

            scores[language] = score

        # Return language with highest score
        if scores:
            detected = max(scores.items(), key=lambda x: x[1])
            if detected[1] > 0:
                logger.info(f"Detected language: {detected[0]} (score: {detected[1]})")
                return detected[0]

        return 'unknown'

    def _detect_framework(self, project_path: Path, language: str) -> str:
        """Detect framework for given language."""
        if language not in self.FRAMEWORK_PATTERNS:
            return None

        frameworks = self.FRAMEWORK_PATTERNS[language]

        for framework, patterns in frameworks.items():
            # Check dependency files
            if language == 'python':
                req_file = project_path / 'requirements.txt'
                if req_file.exists():
                    content = req_file.read_text()
                    if any(pattern in content for pattern in patterns):
                        logger.info(f"Detected framework: {framework}")
                        return framework

            elif language in ['javascript', 'typescript']:
                pkg_file = project_path / 'package.json'
                if pkg_file.exists():
                    try:
                        pkg_data = json.loads(pkg_file.read_text())
                        deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                        if any(pattern in deps for pattern in patterns):
                            logger.info(f"Detected framework: {framework}")
                            return framework
                    except json.JSONDecodeError:
                        pass

            elif language == 'go':
                go_mod = project_path / 'go.mod'
                if go_mod.exists():
                    content = go_mod.read_text()
                    if any(pattern in content for pattern in patterns):
                        logger.info(f"Detected framework: {framework}")
                        return framework

        return None

    def _analyze_dependencies(self, project_path: Path, language: str) -> List[str]:
        """Extract dependencies."""
        dependencies = []

        if language == 'python':
            req_file = project_path / 'requirements.txt'
            if req_file.exists():
                dependencies = [
                    line.strip() for line in req_file.read_text().split('\n')
                    if line.strip() and not line.startswith('#')
                ]

        elif language in ['javascript', 'typescript']:
            pkg_file = project_path / 'package.json'
            if pkg_file.exists():
                try:
                    pkg_data = json.loads(pkg_file.read_text())
                    dependencies = list(pkg_data.get('dependencies', {}).keys())
                except json.JSONDecodeError:
                    pass

        elif language == 'go':
            # Go modules are in go.mod
            dependencies = ['go modules']

        return dependencies[:20]  # Limit to first 20

    def _detect_entry_point(self, project_path: Path, language: str, framework: str) -> str:
        """Detect application entry point."""
        if language == 'python':
            if framework == 'flask':
                # Common Flask patterns
                for name in ['app.py', 'application.py', 'main.py', 'wsgi.py']:
                    if (project_path / name).exists():
                        return name
            elif framework == 'django':
                return 'manage.py'
            elif framework == 'fastapi':
                for name in ['main.py', 'app.py']:
                    if (project_path / name).exists():
                        return name

        elif language in ['javascript', 'typescript']:
            pkg_file = project_path / 'package.json'
            if pkg_file.exists():
                try:
                    pkg_data = json.loads(pkg_file.read_text())
                    if 'main' in pkg_data:
                        return pkg_data['main']
                except json.JSONDecodeError:
                    pass

            # Default entry points
            for name in ['index.js', 'server.js', 'app.js', 'index.ts']:
                if (project_path / name).exists():
                    return name

        elif language == 'go':
            if (project_path / 'main.go').exists():
                return 'main.go'

        return 'main'  # Fallback

    def _detect_ports(self, project_path: Path, language: str, framework: str) -> List[int]:
        """Detect ports used by application."""
        default_ports = {
            'flask': [5000],
            'django': [8000],
            'fastapi': [8000],
            'express': [3000],
            'next': [3000],
            'nest': [3000],
            'gin': [8080],
            'spring': [8080],
        }

        if framework and framework in default_ports:
            return default_ports[framework]

        # Default fallback
        return [8000]
