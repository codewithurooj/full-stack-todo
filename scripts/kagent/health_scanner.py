"""Cluster health scanner for kagent.

Scans overall cluster health including node status, pod health,
and cluster-level issues.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.k8s_client import K8sClient
from shared.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class ClusterHealthScanner:
    """Scans cluster health and identifies issues."""

    def __init__(self, config: Any):
        """Initialize health scanner.

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
        """Scan cluster health.

        Args:
            namespace: Optional namespace to scan (None for all)

        Returns:
            List of findings
        """
        if not self.k8s:
            return [{
                'severity': 'critical',
                'type': 'connectivity',
                'resource': 'cluster',
                'description': 'Cannot connect to Kubernetes cluster',
                'recommendation': 'Check kubectl configuration and cluster access'
            }]

        findings = []

        # Check node health
        findings.extend(self._check_node_health())

        # Check pod health
        findings.extend(self._check_pod_health(namespace))

        # Check system pods
        findings.extend(self._check_system_pods())

        # Check resource pressure
        findings.extend(self._check_resource_pressure())

        return findings

    def _check_node_health(self) -> List[Dict[str, Any]]:
        """Check health of cluster nodes."""
        findings = []

        try:
            nodes = self.k8s.get_nodes()

            for node in nodes:
                # Check node readiness
                node_status = self.k8s._get_node_status(node)
                if node_status != 'Ready':
                    findings.append({
                        'severity': 'critical',
                        'type': 'node_health',
                        'resource': f'node/{node.metadata.name}',
                        'description': f'Node is {node_status}',
                        'recommendation': f'Investigate node {node.metadata.name} - check node logs and system resources'
                    })

                # Check node conditions
                for condition in node.status.conditions:
                    if condition.type in ['MemoryPressure', 'DiskPressure', 'PIDPressure']:
                        if condition.status == 'True':
                            findings.append({
                                'severity': 'high',
                                'type': 'node_pressure',
                                'resource': f'node/{node.metadata.name}',
                                'description': f'{condition.type} detected',
                                'recommendation': f'Free up {condition.type.replace("Pressure", "")} on node {node.metadata.name}'
                            })

        except Exception as e:
            logger.error(f"Error checking node health: {e}")
            findings.append({
                'severity': 'medium',
                'type': 'scan_error',
                'resource': 'nodes',
                'description': f'Failed to check node health: {str(e)}',
                'recommendation': 'Check kubectl permissions for node access'
            })

        return findings

    def _check_pod_health(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check health of pods."""
        findings = []

        try:
            if namespace:
                pods = self.k8s.get_pods(namespace=namespace)
            else:
                pods = self.k8s.get_all_pods()

            # Count pod states
            pod_states = {
                'Running': 0,
                'Pending': 0,
                'Failed': 0,
                'Unknown': 0,
                'CrashLoopBackOff': 0,
                'ImagePullBackOff': 0
            }

            for pod in pods:
                phase = pod.status.phase
                pod_states[phase] = pod_states.get(phase, 0) + 1

                # Check for unhealthy states
                if phase == 'Failed':
                    findings.append({
                        'severity': 'high',
                        'type': 'pod_failed',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': f'Pod in Failed state',
                        'recommendation': f'Check logs: kubectl logs {pod.metadata.name} -n {pod.metadata.namespace}'
                    })

                elif phase == 'Pending':
                    # Pending for too long might indicate scheduling issues
                    findings.append({
                        'severity': 'medium',
                        'type': 'pod_pending',
                        'resource': f'pod/{pod.metadata.name}',
                        'namespace': pod.metadata.namespace,
                        'description': 'Pod stuck in Pending state',
                        'recommendation': f'Check events: kubectl describe pod {pod.metadata.name} -n {pod.metadata.namespace}'
                    })

                # Check container statuses
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if not container.ready:
                            if container.state.waiting:
                                reason = container.state.waiting.reason

                                if reason == 'CrashLoopBackOff':
                                    findings.append({
                                        'severity': 'critical',
                                        'type': 'crashloop',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Container in CrashLoopBackOff',
                                        'recommendation': f'Check logs: kubectl logs {pod.metadata.name} -c {container.name} -n {pod.metadata.namespace} --previous'
                                    })
                                    pod_states['CrashLoopBackOff'] += 1

                                elif reason == 'ImagePullBackOff':
                                    findings.append({
                                        'severity': 'high',
                                        'type': 'image_pull',
                                        'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                        'namespace': pod.metadata.namespace,
                                        'description': f'Cannot pull container image',
                                        'recommendation': f'Verify image name and registry access'
                                    })
                                    pod_states['ImagePullBackOff'] += 1

                        # Check restart count
                        if container.restart_count > 5:
                            findings.append({
                                'severity': 'medium',
                                'type': 'high_restarts',
                                'resource': f'pod/{pod.metadata.name}/container/{container.name}',
                                'namespace': pod.metadata.namespace,
                                'description': f'High restart count: {container.restart_count}',
                                'recommendation': 'Investigate cause of frequent restarts - check logs and resource limits'
                            })

        except Exception as e:
            logger.error(f"Error checking pod health: {e}")
            findings.append({
                'severity': 'medium',
                'type': 'scan_error',
                'resource': 'pods',
                'description': f'Failed to check pod health: {str(e)}',
                'recommendation': 'Check kubectl permissions for pod access'
            })

        return findings

    def _check_system_pods(self) -> List[Dict[str, Any]]:
        """Check health of system pods in kube-system namespace."""
        findings = []

        try:
            system_pods = self.k8s.get_pods(namespace='kube-system')

            critical_components = [
                'kube-apiserver',
                'kube-controller-manager',
                'kube-scheduler',
                'kube-proxy',
                'coredns',
                'etcd'
            ]

            for component in critical_components:
                # Check if component pods exist and are healthy
                component_pods = [
                    p for p in system_pods
                    if component in p.metadata.name
                ]

                if not component_pods:
                    findings.append({
                        'severity': 'critical',
                        'type': 'missing_component',
                        'resource': f'component/{component}',
                        'namespace': 'kube-system',
                        'description': f'Critical component {component} not found',
                        'recommendation': f'Ensure {component} is deployed and running'
                    })
                else:
                    # Check if any are not running
                    unhealthy = [
                        p for p in component_pods
                        if p.status.phase != 'Running'
                    ]
                    if unhealthy:
                        findings.append({
                            'severity': 'critical',
                            'type': 'component_unhealthy',
                            'resource': f'component/{component}',
                            'namespace': 'kube-system',
                            'description': f'{len(unhealthy)} {component} pod(s) not running',
                            'recommendation': f'Check {component} logs and restart if necessary'
                        })

        except Exception as e:
            logger.warning(f"Error checking system pods: {e}")
            # Don't add finding - kube-system might not be accessible

        return findings

    def _check_resource_pressure(self) -> List[Dict[str, Any]]:
        """Check for resource pressure indicators."""
        findings = []

        try:
            cluster_info = self.k8s.get_cluster_info()

            # Check node count
            if cluster_info['nodes'] < 2:
                findings.append({
                    'severity': 'medium',
                    'type': 'cluster_size',
                    'resource': 'cluster',
                    'description': f'Only {cluster_info["nodes"]} node(s) in cluster',
                    'recommendation': 'Consider adding more nodes for high availability'
                })

            # Check pod count vs nodes
            pods_per_node = cluster_info['pods'] / max(cluster_info['nodes'], 1)
            if pods_per_node > 100:
                findings.append({
                    'severity': 'medium',
                    'type': 'high_pod_density',
                    'resource': 'cluster',
                    'description': f'High pod density: {pods_per_node:.0f} pods per node',
                    'recommendation': 'Consider scaling cluster horizontally'
                })

        except Exception as e:
            logger.warning(f"Error checking resource pressure: {e}")

        return findings
