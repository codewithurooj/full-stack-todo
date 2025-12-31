"""Configuration checker for kagent.

Checks Kubernetes configurations against best practices including
probes, labels, annotations, and deployment strategies.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.k8s_client import K8sClient
import logging

logger = logging.getLogger(__name__)


class ConfigurationChecker:
    """Checks configurations against best practices."""

    def __init__(self, config: Any):
        """Initialize configuration checker.

        Args:
            config: Configuration object
        """
        self.config = config
        try:
            self.k8s = K8sClient()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self.k8s = None

    def check(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check configurations.

        Args:
            namespace: Optional namespace to check

        Returns:
            List of findings
        """
        if not self.k8s:
            return []

        findings = []

        # Check health probes
        findings.extend(self._check_health_probes(namespace))

        # Check labels and selectors
        findings.extend(self._check_labels(namespace))

        # Check update strategies
        findings.extend(self._check_update_strategies(namespace))

        # Check service configurations
        findings.extend(self._check_services(namespace))

        return findings

    def _check_health_probes(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for missing or misconfigured health probes."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    # Check liveness probe
                    if not container.liveness_probe:
                        findings.append({
                            'severity': 'medium',
                            'type': 'missing_liveness_probe',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'No liveness probe configured',
                            'recommendation': 'Add liveness probe to detect and restart unhealthy containers'
                        })

                    # Check readiness probe
                    if not container.readiness_probe:
                        findings.append({
                            'severity': 'medium',
                            'type': 'missing_readiness_probe',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'No readiness probe configured',
                            'recommendation': 'Add readiness probe to ensure traffic only reaches ready pods'
                        })

        except Exception as e:
            logger.error(f"Error checking health probes: {e}")

        return findings

    def _check_labels(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for missing or inconsistent labels."""
        findings = []

        recommended_labels = ['app', 'version', 'component', 'environment']

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                labels = pod.metadata.labels or {}

                # Check for app label
                if 'app' not in labels and 'app.kubernetes.io/name' not in labels:
                    findings.append({
                        'severity': 'low',
                        'type': 'missing_app_label',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'No app label found',
                        'recommendation': 'Add app label for better organization and selection'
                    })

                # Check for version label
                if 'version' not in labels and 'app.kubernetes.io/version' not in labels:
                    findings.append({
                        'severity': 'low',
                        'type': 'missing_version_label',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'No version label found',
                        'recommendation': 'Add version label to track deployments'
                    })

        except Exception as e:
            logger.error(f"Error checking labels: {e}")

        return findings

    def _check_update_strategies(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check deployment update strategies."""
        findings = []

        try:
            if namespace:
                deployments = self.k8s.get_deployments(namespace=namespace)
            else:
                namespaces = self.k8s.get_namespaces()
                deployments = []
                for ns in namespaces:
                    try:
                        deployments.extend(self.k8s.get_deployments(namespace=ns))
                    except:
                        pass

            for deployment in deployments:
                # Check if using Recreate strategy (downtime during updates)
                if deployment.spec.strategy:
                    if deployment.spec.strategy.type == 'Recreate':
                        findings.append({
                            'severity': 'low',
                            'type': 'recreate_strategy',
                            'resource': f'deployment/{deployment.metadata.name}',
                            'namespace': deployment.metadata.namespace,
                            'description': 'Using Recreate update strategy (causes downtime)',
                            'recommendation': 'Consider RollingUpdate strategy for zero-downtime deployments'
                        })

        except Exception as e:
            logger.error(f"Error checking update strategies: {e}")

        return findings

    def _check_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check service configurations."""
        findings = []

        try:
            if namespace:
                services = self.k8s.get_services(namespace=namespace)
            else:
                namespaces = self.k8s.get_namespaces()
                services = []
                for ns in namespaces:
                    try:
                        services.extend(self.k8s.get_services(namespace=ns))
                    except:
                        pass

            for service in services:
                # Check for services without selectors
                if not service.spec.selector:
                    findings.append({
                        'severity': 'medium',
                        'type': 'service_no_selector',
                        'resource': f'service/{service.metadata.name}',
                        'namespace': service.metadata.namespace,
                        'description': 'Service has no selector',
                        'recommendation': 'Add selector to route traffic to specific pods'
                    })

                # Check for LoadBalancer services (can be expensive)
                if service.spec.type == 'LoadBalancer':
                    findings.append({
                        'severity': 'low',
                        'type': 'loadbalancer_service',
                        'resource': f'service/{service.metadata.name}',
                        'namespace': service.metadata.namespace,
                        'description': 'Using LoadBalancer service type',
                        'recommendation': 'Ensure LoadBalancer is necessary (can incur cloud costs)'
                    })

        except Exception as e:
            logger.error(f"Error checking services: {e}")

        return findings
