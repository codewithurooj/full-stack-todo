"""Performance analyzer for kagent.

Analyzes cluster performance including response times,
resource bottlenecks, and optimization opportunities.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.k8s_client import K8sClient
import logging

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes cluster performance."""

    def __init__(self, config: Any):
        """Initialize performance analyzer.

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
        """Analyze performance.

        Args:
            namespace: Optional namespace to analyze

        Returns:
            List of findings
        """
        if not self.k8s:
            return []

        findings = []

        # Check for performance anti-patterns
        findings.extend(self._check_antipatterns(namespace))

        # Check node performance
        findings.extend(self._check_node_performance())

        # Check for resource contention
        findings.extend(self._check_resource_contention(namespace))

        return findings

    def _check_antipatterns(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for performance anti-patterns."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            for pod in pods:
                # Check for very small resource requests (under-provisioning)
                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        requests = container.resources.requests

                        # Check for very small CPU requests
                        if 'cpu' in requests:
                            cpu_str = requests['cpu']
                            try:
                                if 'm' in cpu_str:
                                    cpu_millicores = int(cpu_str.replace('m', ''))
                                    if cpu_millicores < 50:  # Less than 50m
                                        findings.append({
                                            'severity': 'medium',
                                            'type': 'low_cpu_request',
                                            'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                            'namespace': pod.metadata.namespace,
                                            'description': f'Very low CPU request: {cpu_str}',
                                            'recommendation': 'Increase CPU request to avoid throttling'
                                        })
                            except ValueError:
                                pass

                        # Check for very small memory requests
                        if 'memory' in requests:
                            memory_str = requests['memory']
                            if 'Mi' in memory_str:
                                memory_mi = int(memory_str.replace('Mi', ''))
                                if memory_mi < 64:  # Less than 64Mi
                                    findings.append({
                                        'severity': 'medium',
                                        'type': 'low_memory_request',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Very low memory request: {memory_str}',
                                        'recommendation': 'Increase memory request to avoid OOM kills'
                                    })

        except Exception as e:
            logger.error(f"Error checking anti-patterns: {e}")

        return findings

    def _check_node_performance(self) -> List[Dict[str, Any]]:
        """Check node performance indicators."""
        findings = []

        try:
            nodes = self.k8s.get_nodes()

            for node in nodes:
                # Check for nodes with low resources
                capacity = node.status.capacity

                # Check CPU capacity
                if 'cpu' in capacity:
                    cpu_count = int(capacity['cpu'])
                    if cpu_count < 2:
                        findings.append({
                            'severity': 'medium',
                            'type': 'low_node_cpu',
                            'resource': f'node/{node.metadata.name}',
                            'description': f'Node has only {cpu_count} CPU core(s)',
                            'recommendation': 'Consider using nodes with more CPU cores for better performance'
                        })

        except Exception as e:
            logger.error(f"Error checking node performance: {e}")

        return findings

    def _check_resource_contention(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for resource contention indicators."""
        findings = []

        try:
            cluster_info = self.k8s.get_cluster_info()

            # High pod density can indicate contention
            pods_per_node = cluster_info['pods'] / max(cluster_info['nodes'], 1)

            if pods_per_node > 50:
                findings.append({
                    'severity': 'medium',
                    'type': 'high_pod_density',
                    'resource': 'cluster',
                    'description': f'High pod density: {pods_per_node:.0f} pods per node',
                    'recommendation': 'Monitor for resource contention - consider adding nodes'
                })

        except Exception as e:
            logger.error(f"Error checking resource contention: {e}")

        return findings
