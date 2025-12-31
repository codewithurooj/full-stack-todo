"""Resource analyzer for kagent.

Analyzes resource utilization and identifies inefficiencies,
over/under-provisioning, and optimization opportunities.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.k8s_client import K8sClient
import logging

logger = logging.getLogger(__name__)


class ResourceAnalyzer:
    """Analyzes cluster resource utilization."""

    def __init__(self, config: Any):
        """Initialize resource analyzer.

        Args:
            config: Configuration object
        """
        self.config = config
        try:
            self.k8s = K8sClient()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self.k8s = None

    def analyze(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Analyze resource utilization.

        Args:
            namespace: Optional namespace to analyze

        Returns:
            List of findings
        """
        if not self.k8s:
            return []

        findings = []

        # Check for missing resource limits
        findings.extend(self._check_resource_limits(namespace))

        # Check for over-provisioning
        findings.extend(self._check_over_provisioning(namespace))

        # Check for resource inefficiency
        findings.extend(self._check_resource_efficiency(namespace))

        # Check for storage issues
        findings.extend(self._check_storage(namespace))

        return findings

    def _check_resource_limits(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for missing resource requests and limits."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    # Check for missing requests
                    if not container.resources or not container.resources.requests:
                        findings.append({
                            'severity': 'medium',
                            'type': 'missing_requests',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'No resource requests defined',
                            'recommendation': 'Set CPU and memory requests for predictable scheduling'
                        })

                    # Check for missing limits
                    if not container.resources or not container.resources.limits:
                        findings.append({
                            'severity': 'medium',
                            'type': 'missing_limits',
                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                            'namespace': pod.metadata.namespace,
                            'description': 'No resource limits defined',
                            'recommendation': 'Set CPU and memory limits to prevent resource exhaustion'
                        })

        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")

        return findings

    def _check_over_provisioning(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for over-provisioned resources."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                for container in pod.spec.containers:
                    if container.resources and container.resources.limits:
                        limits = container.resources.limits

                        # Check for very high memory limits (> 8Gi)
                        if 'memory' in limits:
                            memory_str = limits['memory']
                            if 'Gi' in memory_str:
                                memory_gi = int(memory_str.replace('Gi', ''))
                                if memory_gi > 8:
                                    findings.append({
                                        'severity': 'low',
                                        'type': 'high_memory_limit',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Very high memory limit: {memory_str}',
                                        'recommendation': 'Review if such high memory limit is necessary'
                                    })

                        # Check for very high CPU limits (> 4 cores)
                        if 'cpu' in limits:
                            cpu_str = limits['cpu']
                            # Parse CPU value (could be "4", "4000m", etc.)
                            try:
                                if 'm' in cpu_str:
                                    cpu_cores = int(cpu_str.replace('m', '')) / 1000
                                else:
                                    cpu_cores = int(cpu_str)

                                if cpu_cores > 4:
                                    findings.append({
                                        'severity': 'low',
                                        'type': 'high_cpu_limit',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Very high CPU limit: {cpu_str}',
                                        'recommendation': 'Review if such high CPU limit is necessary'
                                    })
                            except ValueError:
                                pass

        except Exception as e:
            logger.error(f"Error checking over-provisioning: {e}")

        return findings

    def _check_resource_efficiency(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for resource efficiency issues."""
        findings = []

        try:
            if namespace:
                deployments = self.k8s.get_deployments(namespace=namespace)
            else:
                # Get deployments from all namespaces
                namespaces = self.k8s.get_namespaces()
                deployments = []
                for ns in namespaces:
                    try:
                        deployments.extend(self.k8s.get_deployments(namespace=ns))
                    except:
                        pass

            for deployment in deployments:
                # Check for single replica deployments
                if deployment.spec.replicas == 1:
                    findings.append({
                        'severity': 'low',
                        'type': 'single_replica',
                        'resource': f'deployment/{deployment.metadata.name}',
                        'namespace': deployment.metadata.namespace,
                        'description': 'Deployment has only 1 replica',
                        'recommendation': 'Consider increasing replicas for high availability'
                    })

                # Check for very high replica count without HPA
                if deployment.spec.replicas > 10:
                    # This is simplified - would need to check for HPA in real implementation
                    findings.append({
                        'severity': 'low',
                        'type': 'high_replicas_no_hpa',
                        'resource': f'deployment/{deployment.metadata.name}',
                        'namespace': deployment.metadata.namespace,
                        'description': f'High replica count ({deployment.spec.replicas}) without autoscaling',
                        'recommendation': 'Consider using HorizontalPodAutoscaler for dynamic scaling'
                    })

        except Exception as e:
            logger.error(f"Error checking resource efficiency: {e}")

        return findings

    def _check_storage(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for storage-related issues."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                # Check for emptyDir volumes (data loss on pod restart)
                if pod.spec.volumes:
                    for volume in pod.spec.volumes:
                        if hasattr(volume, 'empty_dir') and volume.empty_dir:
                            findings.append({
                                'severity': 'low',
                                'type': 'ephemeral_storage',
                                'resource': f'pod/{pod.metadata.name}/volume/{volume.name}',
                                'namespace': pod.metadata.namespace,
                                'description': 'Using emptyDir (ephemeral storage)',
                                'recommendation': 'Consider PersistentVolume for data that should survive pod restarts'
                            })

        except Exception as e:
            logger.error(f"Error checking storage: {e}")

        return findings
