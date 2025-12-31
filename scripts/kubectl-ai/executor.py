"""Command executor for kubectl-ai.

Executes kubectl commands with confirmation for destructive operations.
"""

import subprocess
from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.confirmation import ConfirmationPrompt
from shared.audit import AuditLog
from shared.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes kubectl commands with safety checks."""

    def __init__(
        self,
        config: Any,
        audit_log: AuditLog,
        require_confirmation: bool = True
    ):
        """Initialize command executor.

        Args:
            config: Configuration object
            audit_log: Audit log instance
            require_confirmation: Whether to require confirmation for destructive ops
        """
        self.config = config
        self.audit_log = audit_log
        self.confirmation = ConfirmationPrompt(require_confirmation=require_confirmation)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30)

    def execute(
        self,
        command: str,
        intent: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Execute a kubectl command.

        Args:
            command: kubectl command to execute
            intent: Parsed intent for context
            dry_run: If True, don't actually execute

        Returns:
            Dictionary with execution result
        """
        # Validate command
        if not self._validate_command(command):
            return {
                'success': False,
                'error': 'Invalid or potentially dangerous command',
                'command': command
            }

        # Check if destructive and require confirmation
        is_destructive = intent.get('destructive', False)

        if is_destructive:
            # Get confirmation
            explanation = intent.get('explanation', 'This is a destructive operation')

            confirmed = self.confirmation.confirm_kubectl_command(
                command=command,
                explanation=explanation
            )

            if not confirmed:
                self.audit_log.log_kubectl_command(
                    command=command,
                    success=False,
                    error="User cancelled operation"
                )
                return {
                    'success': False,
                    'error': 'Operation cancelled by user',
                    'command': command
                }

        # Execute command
        if dry_run:
            return {
                'success': True,
                'output': f"[DRY RUN] Would execute: {command}",
                'command': command,
                'dry_run': True
            }

        try:
            result = self._run_command(command)

            # Log to audit
            self.audit_log.log_kubectl_command(
                command=command,
                success=result['success'],
                output=result.get('output'),
                error=result.get('error')
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Command execution failed: {error_msg}")

            # Log failure
            self.audit_log.log_kubectl_command(
                command=command,
                success=False,
                error=error_msg
            )

            ErrorHandler.handle_kubectl_error(e, command)

            return {
                'success': False,
                'error': error_msg,
                'command': command
            }

    def _run_command(self, command: str) -> Dict[str, Any]:
        """Run a shell command and capture output.

        Args:
            command: Command to run

        Returns:
            Dictionary with result
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'command': command
                }
            else:
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': result.stderr,
                    'command': command,
                    'return_code': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {self.timeout} seconds',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }

    def _validate_command(self, command: str) -> bool:
        """Validate command safety.

        Args:
            command: Command to validate

        Returns:
            True if command is safe
        """
        # Must start with kubectl
        if not command.strip().startswith('kubectl'):
            logger.warning(f"Command doesn't start with kubectl: {command}")
            return False

        # Check for command injection patterns
        dangerous_patterns = [
            '&&', '||', ';', '|', '>', '<',  # Command chaining/redirection
            '`', '$(',  # Command substitution
            'rm -rf', 'dd if=', 'mkfs',  # Dangerous system commands
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                logger.warning(f"Dangerous pattern detected in command: {pattern}")
                # Allow some patterns in safe contexts
                if pattern in ['|', '>'] and 'kubectl' in command:
                    # Allow piping kubectl output
                    continue
                return False

        return True

    def execute_interactive(self, command: str) -> Dict[str, Any]:
        """Execute an interactive command (like kubectl exec).

        Args:
            command: Interactive command to execute

        Returns:
            Dictionary with result
        """
        logger.info(f"Executing interactive command: {command}")

        try:
            # For interactive commands, don't capture output
            result = subprocess.run(
                command,
                shell=True,
                timeout=None  # No timeout for interactive sessions
            )

            success = result.returncode == 0

            self.audit_log.log_kubectl_command(
                command=command,
                success=success,
                output="Interactive session",
                error=None if success else f"Exit code: {result.returncode}"
            )

            return {
                'success': success,
                'command': command,
                'interactive': True
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Interactive command failed: {error_msg}")

            self.audit_log.log_kubectl_command(
                command=command,
                success=False,
                error=error_msg
            )

            return {
                'success': False,
                'error': error_msg,
                'command': command
            }

    def test_connection(self) -> bool:
        """Test kubectl connection to cluster.

        Returns:
            True if connection successful
        """
        try:
            result = self._run_command('kubectl cluster-info')
            return result['success']
        except Exception as e:
            logger.error(f"Cluster connection test failed: {e}")
            return False
