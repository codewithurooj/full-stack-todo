"""Security scanner for kagent.

Scans for security vulnerabilities including privileged containers,
RBAC issues, exposed secrets, and security best practices.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.k8s_client import K8sClient
import logging

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Scans cluster for security issues."""

    def __init__(self, config: Any):
        """Initialize security scanner.

        Args:
            config: Configuration object
        """
        self.config = config
        try:
            self.k8s = K8sClient()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self.k8s = None

    def scan(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan for security issues.

        Args:
            namespace: Optional namespace to scan

        Returns:
            List of findings
        """
        if not self.k8s:
            return []

        findings = []

        # Check for privileged containers
        findings.extend(self._check_privileged_containers(namespace))

        # Check for containers running as root
        findings.extend(self._check_root_containers(namespace))

        # Check for host network/PID/IPC usage
        findings.extend(self._check_host_access(namespace))

        # Check for exposed secrets
        findings.extend(self._check_secrets(namespace))

        # Check security contexts
        findings.extend(self._check_security_contexts(namespace))

        return findings

    def _check_privileged_containers(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for privileged containers."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    if container.security_context and container.security_context.privileged:
                        findings.append({
                            'severity': 'critical',
                            'type': 'privileged_container',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'Container running in privileged mode',
                            'recommendation': 'Disable privileged mode unless absolutely necessary for security'
                        })

        except Exception as e:
            logger.error(f"Error checking privileged containers: {e}")

        return findings

    def _check_root_containers(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for containers running as root."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    # Check if running as non-root is not enforced
                    if not container.security_context or \
                       not hasattr(container.security_context, 'run_as_non_root') or \
                       not container.security_context.run_as_non_root:

                        # Also check if runAsUser is 0 (root)
                        if container.security_context and \
                           hasattr(container.security_context, 'run_as_user') and \
                           container.security_context.run_as_user == 0:
                            findings.append({
                                'severity': 'high',
                                'type': 'running_as_root',
                                'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                'namespace': pod.metadata.namespace,
                                'description': 'Container explicitly running as root (UID 0)',
                                'recommendation': 'Run container as non-root user for better security'
                            })
                        else:
                            findings.append({
                                'severity': 'medium',
                                'type': 'root_not_prevented',
                                'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                'namespace': pod.metadata.namespace,
                                'description': 'runAsNonRoot not enforced',
                                'recommendation': 'Set runAsNonRoot: true in security context'
                            })

        except Exception as e:
            logger.error(f"Error checking root containers: {e}")

        return findings

    def _check_host_access(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for host network/PID/IPC usage."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                # Check hostNetwork
                if pod.spec.host_network:
                    findings.append({
                        'severity': 'high',
                        'type': 'host_network',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'Pod using host network',
                        'recommendation': 'Avoid hostNetwork unless required for specific networking needs'
                    })

                # Check hostPID
                if pod.spec.host_pid:
                    findings.append({
                        'severity': 'high',
                        'type': 'host_pid',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'Pod using host PID namespace',
                        'recommendation': 'Avoid hostPID for better isolation'
                    })

                # Check hostIPC
                if pod.spec.host_ipc:
                    findings.append({
                        'severity': 'high',
                        'type': 'host_ipc',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'Pod using host IPC namespace',
                        'recommendation': 'Avoid hostIPC for better isolation'
                    })

        except Exception as e:
            logger.error(f"Error checking host access: {e}")

        return findings

    def _check_secrets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for potential secret exposure."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                # Check environment variables for potential secrets
                for container in pod.spec.containers:
                    if container.env:
                        for env_var in container.env:
                            # Look for common secret patterns in env var names
                            sensitive_keywords = ['password', 'secret', 'token', 'api_key', 'apikey']
                            if any(keyword in env_var.name.lower() for keyword in sensitive_keywords):
                                # Check if it's using valueFrom (good) or direct value (bad)
                                if not env_var.value_from and env_var.value:
                                    findings.append({
                                        'severity': 'high',
                                        'type': 'hardcoded_secret',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Potential hardcoded secret in env var: {env_var.name}',
                                        'recommendation': 'Use Kubernetes Secrets with valueFrom instead of hardcoded values'
                                    })

        except Exception as e:
            logger.error(f"Error checking secrets: {e}")

        return findings

    def _check_security_contexts(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check security context configurations."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    if not container.security_context:
                        findings.append({
                            'severity': 'medium',
                            'type': 'no_security_context',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'No security context defined',
                            'recommendation': 'Define security context with appropriate settings'
                        })
                    else:
                        # Check for read-only root filesystem
                        if not hasattr(container.security_context, 'read_only_root_filesystem') or \
                           not container.security_context.read_only_root_filesystem:
                            findings.append({
                                'severity': 'low',
                                'type': 'writable_root_fs',
                                'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                'namespace': pod.metadata.namespace,
                                'description': 'Root filesystem is writable',
                                'recommendation': 'Set readOnlyRootFilesystem: true for better security'
                            })

                        # Check for capability drops
                        if not hasattr(container.security_context, 'capabilities') or \
                           not container.security_context.capabilities or \
                           not container.security_context.capabilities.drop:
                            findings.append({
                                'severity': 'low',
                                'type': 'no_capability_drop',
                                'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                'namespace': pod.metadata.namespace,
                                'description': 'No capabilities dropped',
                                'recommendation': 'Drop unnecessary capabilities (e.g., drop: [ALL])'
                            })

        except Exception as e:
            logger.error(f"Error checking security contexts: {e}")

        return findings
