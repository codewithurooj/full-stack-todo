"""Test fixtures for mock Kubernetes cluster and AI providers.

Provides reusable fixtures for testing all three tools with mocked
Kubernetes API and AI provider responses.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Any, Dict, List


# Kubernetes Mock Fixtures

@pytest.fixture
def mock_k8s_pod():
    """Mock Kubernetes pod object."""
    pod = Mock()
    pod.metadata = Mock()
    pod.metadata.name = "test-pod"
    pod.metadata.namespace = "default"
    pod.metadata.labels = {"app": "test"}
    pod.metadata.creation_timestamp = datetime.now()

    pod.spec = Mock()
    pod.spec.containers = [Mock(name="nginx", image="nginx:1.21")]

    pod.status = Mock()
    pod.status.phase = "Running"
    pod.status.conditions = [
        Mock(type="Ready", status="True")
    ]
    pod.status.pod_ip = "10.244.0.5"

    return pod


@pytest.fixture
def mock_k8s_deployment():
    """Mock Kubernetes deployment object."""
    deployment = Mock()
    deployment.metadata = Mock()
    deployment.metadata.name = "nginx-deployment"
    deployment.metadata.namespace = "default"
    deployment.metadata.labels = {"app": "nginx"}

    deployment.spec = Mock()
    deployment.spec.replicas = 3
    deployment.spec.selector = Mock(match_labels={"app": "nginx"})

    deployment.status = Mock()
    deployment.status.replicas = 3
    deployment.status.ready_replicas = 3
    deployment.status.available_replicas = 3

    return deployment


@pytest.fixture
def mock_k8s_service():
    """Mock Kubernetes service object."""
    service = Mock()
    service.metadata = Mock()
    service.metadata.name = "nginx-service"
    service.metadata.namespace = "default"

    service.spec = Mock()
    service.spec.type = "ClusterIP"
    service.spec.cluster_ip = "10.96.0.1"
    service.spec.ports = [
        Mock(port=80, target_port=80, protocol="TCP")
    ]
    service.spec.selector = {"app": "nginx"}

    return service


@pytest.fixture
def mock_k8s_node():
    """Mock Kubernetes node object."""
    node = Mock()
    node.metadata = Mock()
    node.metadata.name = "node-1"
    node.metadata.labels = {"kubernetes.io/hostname": "node-1"}

    node.status = Mock()
    node.status.conditions = [
        Mock(type="Ready", status="True")
    ]
    node.status.capacity = {
        "cpu": "4",
        "memory": "8Gi",
        "pods": "110"
    }
    node.status.allocatable = {
        "cpu": "3800m",
        "memory": "7.5Gi",
        "pods": "110"
    }

    return node


@pytest.fixture
def mock_k8s_client(mock_k8s_pod, mock_k8s_deployment, mock_k8s_service, mock_k8s_node):
    """Mock Kubernetes client with common methods."""
    client = Mock()

    # Core V1 API
    client.core_v1 = Mock()
    client.core_v1.list_pod_for_all_namespaces.return_value = Mock(
        items=[mock_k8s_pod]
    )
    client.core_v1.list_namespaced_pod.return_value = Mock(
        items=[mock_k8s_pod]
    )
    client.core_v1.list_namespaced_service.return_value = Mock(
        items=[mock_k8s_service]
    )
    client.core_v1.list_node.return_value = Mock(
        items=[mock_k8s_node]
    )
    client.core_v1.list_namespace.return_value = Mock(
        items=[
            Mock(metadata=Mock(name="default")),
            Mock(metadata=Mock(name="kube-system"))
        ]
    )

    # Apps V1 API
    client.apps_v1 = Mock()
    client.apps_v1.list_namespaced_deployment.return_value = Mock(
        items=[mock_k8s_deployment]
    )

    return client


# AI Provider Mock Fixtures

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    response = Mock()
    response.choices = [
        Mock(message=Mock(content="This is a test response from OpenAI"))
    ]
    return response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    response = Mock()
    response.content = [
        Mock(text="This is a test response from Claude")
    ]
    return response


@pytest.fixture
def mock_openai_provider(mock_openai_response):
    """Mock OpenAI provider."""
    with patch('scripts.shared.ai_provider.OpenAI') as mock_client_class:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_client_class.return_value = mock_client

        from scripts.shared.ai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key="test-key")
        return provider


@pytest.fixture
def mock_anthropic_provider(mock_anthropic_response):
    """Mock Anthropic provider."""
    with patch('scripts.shared.ai_provider.Anthropic') as mock_client_class:
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_client_class.return_value = mock_client

        from scripts.shared.ai_provider import AnthropicProvider
        provider = AnthropicProvider(api_key="test-key")
        return provider


# Configuration Fixtures

@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = Mock()
    config.tool_name = "test-tool"
    config.ai_provider = "openai"
    config.openai_api_key = "test-openai-key"
    config.anthropic_api_key = "test-anthropic-key"
    config.get.return_value = "INFO"
    config.validate.return_value = True
    return config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary configuration directory."""
    config_dir = tmp_path / ".test-tool"
    config_dir.mkdir()
    return config_dir


# Audit Log Fixtures

@pytest.fixture
def mock_audit_log(tmp_path):
    """Mock audit log with temporary directory."""
    from scripts.shared.audit import AuditLog

    audit_dir = tmp_path / "audit"
    audit_log = AuditLog("test-tool", audit_dir=audit_dir)
    return audit_log


# kubectl Command Fixtures

@pytest.fixture
def sample_kubectl_commands():
    """Sample kubectl commands for testing."""
    return [
        {
            'natural': "list all pods",
            'kubectl': "kubectl get pods --all-namespaces",
            'destructive': False
        },
        {
            'natural': "scale nginx deployment to 5 replicas",
            'kubectl': "kubectl scale deployment nginx --replicas=5",
            'destructive': False
        },
        {
            'natural': "delete pod test-pod",
            'kubectl': "kubectl delete pod test-pod",
            'destructive': True
        },
        {
            'natural': "get pod logs for app-pod",
            'kubectl': "kubectl logs app-pod",
            'destructive': False
        }
    ]


# Cluster Analysis Fixtures

@pytest.fixture
def sample_cluster_issues():
    """Sample cluster issues for kagent testing."""
    return [
        {
            'severity': 'critical',
            'type': 'security',
            'resource': 'pod/privileged-pod',
            'namespace': 'default',
            'description': 'Pod running with privileged mode enabled',
            'recommendation': 'Disable privileged mode unless absolutely necessary'
        },
        {
            'severity': 'high',
            'type': 'resource',
            'resource': 'deployment/memory-hog',
            'namespace': 'default',
            'description': 'Deployment has no memory limits',
            'recommendation': 'Set appropriate memory requests and limits'
        },
        {
            'severity': 'medium',
            'type': 'config',
            'resource': 'deployment/no-probes',
            'namespace': 'default',
            'description': 'Missing liveness and readiness probes',
            'recommendation': 'Add health check probes for better reliability'
        }
    ]


# Dockerfile Generation Fixtures

@pytest.fixture
def sample_project_structure():
    """Sample project structure for Dockerfile generation."""
    return {
        'python_flask': {
            'files': ['app.py', 'requirements.txt', 'wsgi.py'],
            'language': 'python',
            'framework': 'flask',
            'expected_base': 'python:3.13-slim'
        },
        'nodejs_express': {
            'files': ['index.js', 'package.json', 'package-lock.json'],
            'language': 'javascript',
            'framework': 'express',
            'expected_base': 'node:20-alpine'
        },
        'go_gin': {
            'files': ['main.go', 'go.mod', 'go.sum'],
            'language': 'go',
            'framework': 'gin',
            'expected_base': 'golang:1.21-alpine'
        }
    }


@pytest.fixture
def sample_dockerfile_template():
    """Sample Dockerfile template."""
    return """FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
"""


# Helper Functions

def create_mock_pod_list(count: int = 3, namespace: str = "default") -> List[Any]:
    """Create a list of mock pods.

    Args:
        count: Number of pods to create
        namespace: Namespace for pods

    Returns:
        List of mock pod objects
    """
    pods = []
    for i in range(count):
        pod = Mock()
        pod.metadata = Mock(
            name=f"pod-{i}",
            namespace=namespace,
            labels={"app": f"app-{i % 2}"}
        )
        pod.status = Mock(phase="Running")
        pods.append(pod)
    return pods


def create_mock_deployment_list(count: int = 2, namespace: str = "default") -> List[Any]:
    """Create a list of mock deployments.

    Args:
        count: Number of deployments to create
        namespace: Namespace for deployments

    Returns:
        List of mock deployment objects
    """
    deployments = []
    for i in range(count):
        deployment = Mock()
        deployment.metadata = Mock(
            name=f"deployment-{i}",
            namespace=namespace
        )
        deployment.spec = Mock(replicas=3)
        deployment.status = Mock(
            replicas=3,
            ready_replicas=3,
            available_replicas=3
        )
        deployments.append(deployment)
    return deployments
