"""Kubernetes client wrapper for simplified cluster operations.

Provides a higher-level interface to the Kubernetes Python client
with error handling and common operations.
"""

from typing import Optional, List, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logger = logging.getLogger(__name__)


class K8sClient:
    """Wrapper for Kubernetes API client."""

    def __init__(self, context: Optional[str] = None):
        """Initialize Kubernetes client.

        Args:
            context: Kubernetes context to use (None for current context)
        """
        try:
            if context:
                config.load_kube_config(context=context)
            else:
                try:
                    config.load_kube_config()
                except config.ConfigException:
                    # Try in-cluster config if kubeconfig fails
                    config.load_incluster_config()

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.networking_v1 = client.NetworkingV1Api()

            logger.info("Kubernetes client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def get_pods(
        self,
        namespace: str = "default",
        label_selector: Optional[str] = None
    ) -> List[Any]:
        """Get pods in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering pods

        Returns:
            List of pod objects
        """
        try:
            response = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            return response.items
        except ApiException as e:
            logger.error(f"Error getting pods: {e}")
            raise

    def get_all_pods(self) -> List[Any]:
        """Get all pods across all namespaces.

        Returns:
            List of pod objects
        """
        try:
            response = self.core_v1.list_pod_for_all_namespaces()
            return response.items
        except ApiException as e:
            logger.error(f"Error getting all pods: {e}")
            raise

    def get_deployments(
        self,
        namespace: str = "default",
        label_selector: Optional[str] = None
    ) -> List[Any]:
        """Get deployments in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering deployments

        Returns:
            List of deployment objects
        """
        try:
            response = self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
            return response.items
        except ApiException as e:
            logger.error(f"Error getting deployments: {e}")
            raise

    def get_services(
        self,
        namespace: str = "default",
        label_selector: Optional[str] = None
    ) -> List[Any]:
        """Get services in a namespace.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector for filtering services

        Returns:
            List of service objects
        """
        try:
            response = self.core_v1.list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector
            )
            return response.items
        except ApiException as e:
            logger.error(f"Error getting services: {e}")
            raise

    def get_nodes(self) -> List[Any]:
        """Get all cluster nodes.

        Returns:
            List of node objects
        """
        try:
            response = self.core_v1.list_node()
            return response.items
        except ApiException as e:
            logger.error(f"Error getting nodes: {e}")
            raise

    def get_namespaces(self) -> List[str]:
        """Get all namespaces in the cluster.

        Returns:
            List of namespace names
        """
        try:
            response = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in response.items]
        except ApiException as e:
            logger.error(f"Error getting namespaces: {e}")
            raise

    def scale_deployment(
        self,
        name: str,
        namespace: str,
        replicas: int
    ) -> Any:
        """Scale a deployment.

        Args:
            name: Deployment name
            namespace: Namespace
            replicas: Desired replica count

        Returns:
            Updated deployment object
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            deployment.spec.replicas = replicas

            response = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Scaled deployment {name} to {replicas} replicas")
            return response
        except ApiException as e:
            logger.error(f"Error scaling deployment: {e}")
            raise

    def delete_pod(self, name: str, namespace: str) -> Any:
        """Delete a pod.

        Args:
            name: Pod name
            namespace: Namespace

        Returns:
            Delete response
        """
        try:
            response = self.core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted pod {name} in namespace {namespace}")
            return response
        except ApiException as e:
            logger.error(f"Error deleting pod: {e}")
            raise

    def get_pod_logs(
        self,
        name: str,
        namespace: str,
        tail_lines: Optional[int] = None
    ) -> str:
        """Get logs from a pod.

        Args:
            name: Pod name
            namespace: Namespace
            tail_lines: Number of lines to tail (None for all)

        Returns:
            Pod logs as string
        """
        try:
            return self.core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                tail_lines=tail_lines
            )
        except ApiException as e:
            logger.error(f"Error getting pod logs: {e}")
            raise

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information.

        Returns:
            Dictionary with cluster details
        """
        try:
            nodes = self.get_nodes()
            pods = self.get_all_pods()
            namespaces = self.get_namespaces()

            return {
                'nodes': len(nodes),
                'pods': len(pods),
                'namespaces': len(namespaces),
                'node_details': [
                    {
                        'name': node.metadata.name,
                        'status': self._get_node_status(node),
                        'cpu': node.status.capacity.get('cpu'),
                        'memory': node.status.capacity.get('memory'),
                    }
                    for node in nodes
                ]
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            raise

    def _get_node_status(self, node: Any) -> str:
        """Get node status.

        Args:
            node: Node object

        Returns:
            Node status string
        """
        for condition in node.status.conditions:
            if condition.type == 'Ready':
                return 'Ready' if condition.status == 'True' else 'NotReady'
        return 'Unknown'
