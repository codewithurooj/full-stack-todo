"""Natural language parser for kubectl-ai.

Parses natural language queries into structured intents using AI.
"""

import json
import re
from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ai_provider import get_ai_provider
from shared.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class NaturalLanguageParser:
    """Parses natural language into kubectl intents."""

    # Common kubectl operations
    OPERATIONS = {
        'list': ['list', 'show', 'get', 'display', 'view'],
        'create': ['create', 'make', 'add', 'new'],
        'delete': ['delete', 'remove', 'destroy', 'kill'],
        'update': ['update', 'modify', 'change', 'edit'],
        'scale': ['scale', 'resize'],
        'describe': ['describe', 'details', 'info', 'information'],
        'logs': ['logs', 'log', 'tail'],
        'exec': ['exec', 'execute', 'run', 'shell'],
        'apply': ['apply', 'deploy'],
        'rollout': ['rollout', 'restart', 'roll'],
    }

    # Kubernetes resource types
    RESOURCES = [
        'pod', 'pods', 'po',
        'deployment', 'deployments', 'deploy',
        'service', 'services', 'svc',
        'namespace', 'namespaces', 'ns',
        'node', 'nodes',
        'configmap', 'configmaps', 'cm',
        'secret', 'secrets',
        'ingress', 'ingresses', 'ing',
        'persistentvolume', 'pv',
        'persistentvolumeclaim', 'pvc',
        'statefulset', 'statefulsets', 'sts',
        'daemonset', 'daemonsets', 'ds',
        'job', 'jobs',
        'cronjob', 'cronjobs',
    ]

    def __init__(self, config: Any):
        """Initialize natural language parser.

        Args:
            config: Configuration object
        """
        self.config = config
        self.ai_provider = get_ai_provider(config)

    def parse(self, query: str) -> Dict[str, Any]:
        """Parse natural language query into structured intent.

        Args:
            query: Natural language query

        Returns:
            Dictionary with parsed intent
        """
        # Try rule-based parsing first (faster)
        intent = self._rule_based_parse(query)

        # If rule-based parsing is uncertain, use AI
        if intent.get('confidence', 0) < 0.7:
            try:
                intent = self._ai_parse(query)
            except Exception as e:
                logger.warning(f"AI parsing failed, using rule-based: {e}")
                # Fall back to rule-based result

        return intent

    def _rule_based_parse(self, query: str) -> Dict[str, Any]:
        """Parse using rule-based pattern matching.

        Args:
            query: Natural language query

        Returns:
            Parsed intent dictionary
        """
        query_lower = query.lower()

        # Detect operation
        operation = 'get'  # default
        confidence = 0.5

        for op, keywords in self.OPERATIONS.items():
            if any(kw in query_lower for kw in keywords):
                operation = op
                confidence = 0.8
                break

        # Detect resource type
        resource_type = None
        for resource in self.RESOURCES:
            if resource in query_lower:
                resource_type = resource
                confidence = min(confidence + 0.1, 0.9)
                break

        # Extract resource name (simple pattern matching)
        resource_name = None

        # Pattern: "deployment nginx" or "pod my-pod"
        if resource_type:
            pattern = rf"{resource_type}\s+([a-z0-9-]+)"
            match = re.search(pattern, query_lower)
            if match:
                resource_name = match.group(1)
                confidence = 0.9

        # Detect namespace
        namespace = None
        ns_patterns = [
            r"in\s+namespace\s+([a-z0-9-]+)",
            r"namespace\s+([a-z0-9-]+)",
            r"ns\s+([a-z0-9-]+)",
            r"-n\s+([a-z0-9-]+)",
        ]
        for pattern in ns_patterns:
            match = re.search(pattern, query_lower)
            if match:
                namespace = match.group(1)
                break

        # Detect all namespaces flag
        all_namespaces = any(
            phrase in query_lower
            for phrase in ['all namespaces', 'all-namespaces', '--all-namespaces', 'across all']
        )

        # Detect scale replicas
        replicas = None
        if operation == 'scale':
            replica_patterns = [
                r"to\s+(\d+)\s+replica",
                r"(\d+)\s+replica",
                r"replicas?\s*=?\s*(\d+)",
            ]
            for pattern in replica_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    replicas = int(match.group(1))
                    confidence = 0.9
                    break

        # Determine if operation is destructive
        destructive = operation in ['delete', 'destroy', 'remove', 'kill']

        return {
            'operation': operation,
            'resource_type': resource_type,
            'resource_name': resource_name,
            'namespace': namespace,
            'all_namespaces': all_namespaces,
            'replicas': replicas,
            'destructive': destructive,
            'confidence': confidence,
            'original_query': query,
        }

    def _ai_parse(self, query: str) -> Dict[str, Any]:
        """Parse using AI for complex queries.

        Args:
            query: Natural language query

        Returns:
            Parsed intent dictionary
        """
        system_prompt = """You are a kubectl command interpreter. Parse natural language queries into structured JSON.

Extract:
- operation: get, create, delete, update, scale, describe, logs, exec, apply, rollout
- resource_type: pod, deployment, service, namespace, node, etc.
- resource_name: specific name if mentioned, null otherwise
- namespace: namespace if specified, null otherwise
- all_namespaces: true if query mentions "all namespaces"
- replicas: number if scaling operation
- destructive: true if operation deletes/removes resources
- kubectl_command: the actual kubectl command to execute
- explanation: brief explanation of what this command does

Return ONLY valid JSON, no other text."""

        user_prompt = f"""Parse this query:

"{query}"

Return JSON with the structure above."""

        try:
            response = self.ai_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.3  # Low temperature for consistent parsing
            )

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                intent = json.loads(json_match.group(0))
                intent['confidence'] = 1.0
                intent['original_query'] = query
                return intent
            else:
                raise ValueError("No JSON found in AI response")

        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            raise

    def extract_kubectl_context(self, query: str) -> Dict[str, Optional[str]]:
        """Extract kubectl context information from query.

        Args:
            query: Natural language query

        Returns:
            Dictionary with context (namespace, labels, etc.)
        """
        context = {
            'namespace': None,
            'labels': None,
            'field_selector': None,
        }

        query_lower = query.lower()

        # Extract namespace
        ns_patterns = [
            r"in\s+namespace\s+([a-z0-9-]+)",
            r"namespace\s+([a-z0-9-]+)",
            r"-n\s+([a-z0-9-]+)",
        ]
        for pattern in ns_patterns:
            match = re.search(pattern, query_lower)
            if match:
                context['namespace'] = match.group(1)
                break

        # Extract label selectors
        label_patterns = [
            r"with\s+label\s+([a-z0-9-=,]+)",
            r"labeled\s+([a-z0-9-=,]+)",
            r"-l\s+([a-z0-9-=,]+)",
        ]
        for pattern in label_patterns:
            match = re.search(pattern, query_lower)
            if match:
                context['labels'] = match.group(1)
                break

        return context
