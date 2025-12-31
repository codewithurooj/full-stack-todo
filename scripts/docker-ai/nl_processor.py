"""Natural language processor for docker-ai.

Parses natural language descriptions to extract application requirements.
"""

from typing import Dict, Any
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ai_provider import get_ai_provider
import logging

logger = logging.getLogger(__name__)


class NaturalLanguageProcessor:
    """Processes natural language to extract Dockerfile specifications."""

    LANGUAGE_KEYWORDS = {
        'python': ['python', 'py', 'django', 'flask', 'fastapi'],
        'javascript': ['javascript', 'js', 'node', 'nodejs', 'express', 'react', 'vue', 'next'],
        'typescript': ['typescript', 'ts'],
        'go': ['go', 'golang', 'gin', 'echo'],
        'java': ['java', 'spring', 'springboot', 'maven', 'gradle'],
        'ruby': ['ruby', 'rails'],
        'php': ['php', 'laravel', 'symfony'],
        'rust': ['rust'],
        'csharp': ['c#', 'csharp', '.net', 'dotnet', 'asp.net'],
    }

    FRAMEWORK_KEYWORDS = {
        'flask': ['flask'],
        'django': ['django'],
        'fastapi': ['fastapi'],
        'express': ['express'],
        'react': ['react'],
        'vue': ['vue', 'vuejs'],
        'next': ['next', 'nextjs'],
        'nest': ['nest', 'nestjs'],
        'gin': ['gin'],
        'spring': ['spring', 'springboot'],
    }

    SERVICE_KEYWORDS = {
        'postgresql': ['postgresql', 'postgres', 'psql'],
        'mysql': ['mysql'],
        'mongodb': ['mongodb', 'mongo'],
        'redis': ['redis'],
        'rabbitmq': ['rabbitmq', 'rabbit'],
        'elasticsearch': ['elasticsearch', 'elastic'],
        'nginx': ['nginx'],
    }

    def __init__(self, config: Any):
        """Initialize NL processor.

        Args:
            config: Configuration object
        """
        self.config = config
        try:
            self.ai_provider = get_ai_provider(config)
        except Exception as e:
            logger.warning(f"AI provider not available: {e}")
            self.ai_provider = None

    def process(self, description: str) -> Dict[str, Any]:
        """Process natural language description.

        Args:
            description: Natural language description

        Returns:
            Specification dictionary
        """
        # Try rule-based parsing first
        spec = self._rule_based_parse(description)

        # If AI is available and confidence is low, use AI
        if self.ai_provider and spec.get('confidence', 0) < 0.7:
            try:
                ai_spec = self._ai_parse(description)
                # Merge AI results
                spec.update(ai_spec)
                spec['confidence'] = 1.0
            except Exception as e:
                logger.warning(f"AI parsing failed: {e}")

        return spec

    def _rule_based_parse(self, description: str) -> Dict[str, Any]:
        """Parse using rule-based pattern matching."""
        desc_lower = description.lower()

        # Detect language
        language = None
        for lang, keywords in self.LANGUAGE_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                language = lang
                break

        # Detect framework
        framework = None
        for fw, keywords in self.FRAMEWORK_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                framework = fw
                break

        # Detect services
        services = []
        for service, keywords in self.SERVICE_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                services.append(service)

        # Detect ports (if mentioned)
        ports = []
        port_pattern = r'port\s+(\d+)'
        port_matches = re.findall(port_pattern, desc_lower)
        ports = [int(p) for p in port_matches]

        # Default ports based on framework
        if not ports and framework:
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
            ports = default_ports.get(framework, [8000])

        # Determine confidence
        confidence = 0.5
        if language:
            confidence += 0.3
        if framework:
            confidence += 0.2

        return {
            'language': language or 'python',  # Default to Python
            'framework': framework,
            'services': services,
            'ports': ports or [8000],
            'description': description,
            'confidence': min(confidence, 1.0)
        }

    def _ai_parse(self, description: str) -> Dict[str, Any]:
        """Parse using AI for complex descriptions."""
        system_prompt = """You are a Docker expert. Parse application descriptions into structured specifications.

Extract:
- language: programming language (python, javascript, go, java, etc.)
- framework: web framework if mentioned (flask, django, express, spring, etc.)
- services: external services needed (postgresql, redis, mongodb, etc.)
- ports: port numbers to expose
- entry_point: likely entry point file

Return ONLY valid JSON."""

        user_prompt = f"""Parse this application description:

"{description}"

Return JSON with: language, framework (or null), services (array), ports (array), entry_point"""

        try:
            response = self.ai_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=300,
                temperature=0.3
            )

            # Extract JSON
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            raise ValueError("No JSON in AI response")

        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            raise
