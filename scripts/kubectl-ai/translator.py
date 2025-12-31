"""kubectl command translator.

Translates parsed intents into actual kubectl commands.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class KubectlTranslator:
    """Translates intents to kubectl commands."""

    def __init__(self, config: Any):
        """Initialize kubectl translator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.kubectl_path = config.get('kubectl_path', 'kubectl')

    def translate(self, intent: Dict[str, Any]) -> str:
        """Translate intent to kubectl command.

        Args:
            intent: Parsed intent dictionary

        Returns:
            kubectl command string
        """
        operation = intent.get('operation', 'get')

        # Dispatch to operation-specific translator
        if operation == 'get' or operation == 'list':
            return self._translate_get(intent)
        elif operation == 'describe':
            return self._translate_describe(intent)
        elif operation == 'delete':
            return self._translate_delete(intent)
        elif operation == 'scale':
            return self._translate_scale(intent)
        elif operation == 'logs':
            return self._translate_logs(intent)
        elif operation == 'create':
            return self._translate_create(intent)
        elif operation == 'apply':
            return self._translate_apply(intent)
        elif operation == 'exec':
            return self._translate_exec(intent)
        elif operation == 'rollout':
            return self._translate_rollout(intent)
        elif operation == 'update':
            return self._translate_update(intent)
        else:
            # Fallback to AI-generated command if available
            if 'kubectl_command' in intent:
                return intent['kubectl_command']
            else:
                return self._translate_generic(intent)

    def _translate_get(self, intent: Dict[str, Any]) -> str:
        """Translate get/list operation."""
        parts = [self.kubectl_path, 'get']

        resource_type = intent.get('resource_type', 'pods')
        parts.append(resource_type)

        # Add resource name if specified
        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        # Add namespace flag
        if intent.get('all_namespaces'):
            parts.append('--all-namespaces')
        elif intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        # Add output format
        parts.append('-o wide')

        return ' '.join(parts)

    def _translate_describe(self, intent: Dict[str, Any]) -> str:
        """Translate describe operation."""
        parts = [self.kubectl_path, 'describe']

        resource_type = intent.get('resource_type', 'pod')
        parts.append(resource_type)

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        if intent.get('namespace') and not intent.get('all_namespaces'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_delete(self, intent: Dict[str, Any]) -> str:
        """Translate delete operation."""
        parts = [self.kubectl_path, 'delete']

        resource_type = intent.get('resource_type', 'pod')
        parts.append(resource_type)

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])
        else:
            # If no specific name, might need label selector or --all
            logger.warning("Delete operation without specific resource name")

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_scale(self, intent: Dict[str, Any]) -> str:
        """Translate scale operation."""
        parts = [self.kubectl_path, 'scale']

        resource_type = intent.get('resource_type', 'deployment')
        resource_name = intent.get('resource_name', '')

        parts.append(f"{resource_type}/{resource_name}")

        replicas = intent.get('replicas', 1)
        parts.append(f"--replicas={replicas}")

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_logs(self, intent: Dict[str, Any]) -> str:
        """Translate logs operation."""
        parts = [self.kubectl_path, 'logs']

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])
        elif intent.get('resource_type'):
            parts.append(intent['resource_type'])

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        # Add common log flags
        parts.append('--tail=100')

        return ' '.join(parts)

    def _translate_create(self, intent: Dict[str, Any]) -> str:
        """Translate create operation."""
        parts = [self.kubectl_path, 'create']

        resource_type = intent.get('resource_type', 'deployment')
        parts.append(resource_type)

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_apply(self, intent: Dict[str, Any]) -> str:
        """Translate apply operation."""
        parts = [self.kubectl_path, 'apply', '-f']

        # Assume filename is in resource_name
        if intent.get('resource_name'):
            parts.append(intent['resource_name'])
        else:
            parts.append('-')  # stdin

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_exec(self, intent: Dict[str, Any]) -> str:
        """Translate exec operation."""
        parts = [self.kubectl_path, 'exec', '-it']

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        parts.append('--')
        parts.append('/bin/sh')  # default shell

        return ' '.join(parts)

    def _translate_rollout(self, intent: Dict[str, Any]) -> str:
        """Translate rollout operation."""
        parts = [self.kubectl_path, 'rollout', 'restart']

        resource_type = intent.get('resource_type', 'deployment')
        resource_name = intent.get('resource_name', '')

        parts.append(f"{resource_type}/{resource_name}")

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_update(self, intent: Dict[str, Any]) -> str:
        """Translate update operation."""
        # Update typically uses patch or edit
        parts = [self.kubectl_path, 'edit']

        resource_type = intent.get('resource_type', 'deployment')
        parts.append(resource_type)

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])

        return ' '.join(parts)

    def _translate_generic(self, intent: Dict[str, Any]) -> str:
        """Generic translation fallback."""
        parts = [self.kubectl_path]

        parts.append(intent.get('operation', 'get'))

        if intent.get('resource_type'):
            parts.append(intent['resource_type'])

        if intent.get('resource_name'):
            parts.append(intent['resource_name'])

        if intent.get('namespace'):
            parts.extend(['-n', intent['namespace']])
        elif intent.get('all_namespaces'):
            parts.append('--all-namespaces')

        return ' '.join(parts)

    def add_common_flags(self, command: str, flags: Dict[str, Any]) -> str:
        """Add common kubectl flags to a command.

        Args:
            command: Base kubectl command
            flags: Dictionary of flags to add

        Returns:
            Command with added flags
        """
        parts = command.split()

        if flags.get('output'):
            parts.extend(['-o', flags['output']])

        if flags.get('labels'):
            parts.extend(['-l', flags['labels']])

        if flags.get('field_selector'):
            parts.extend(['--field-selector', flags['field_selector']])

        if flags.get('watch'):
            parts.append('-w')

        if flags.get('follow'):
            parts.append('-f')

        return ' '.join(parts)

    def validate_command(self, command: str) -> bool:
        """Validate kubectl command syntax.

        Args:
            command: kubectl command to validate

        Returns:
            True if command appears valid
        """
        if not command.startswith('kubectl'):
            return False

        # Check for dangerous patterns
        dangerous = ['rm -rf', '| bash', '&&', ';']
        for pattern in dangerous:
            if pattern in command:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                return False

        return True
