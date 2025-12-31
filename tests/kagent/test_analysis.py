"""Unit tests for kagent analysis components.

Tests health scanner, resource analyzer, and other core components.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path / 'kagent'))
sys.path.insert(0, str(scripts_path / 'shared'))


class TestHealthScanner:
    """Test cluster health scanner."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value="INFO")
        return config

    @pytest.fixture
    def scanner(self, mock_config):
        """Create health scanner with mocked K8s client."""
        with patch('kagent.health_scanner.K8sClient'):
            fromhealth_scanner import ClusterHealthScanner
            return ClusterHealthScanner(mock_config)

    def test_scan_returns_findings(self, scanner):
        """Test that scan returns list of findings."""
        # Mock K8s client methods
        scanner.k8s = Mock()
        scanner.k8s.get_nodes = Mock(return_value=[])
        scanner.k8s.get_all_pods = Mock(return_value=[])
        scanner.k8s.get_pods = Mock(return_value=[])
        scanner.k8s.get_cluster_info = Mock(return_value={'nodes': 1, 'pods': 10})

        findings = scanner.scan()

        assert isinstance(findings, list)

    def test_check_unhealthy_node(self, scanner, mock_k8s_node):
        """Test detection of unhealthy nodes."""
        # Create unhealthy node
        node = mock_k8s_node
        node.status.conditions = [Mock(type='Ready', status='False')]

        scanner.k8s = Mock()
        scanner.k8s.get_nodes = Mock(return_value=[node])
        scanner.k8s._get_node_status = Mock(return_value='NotReady')
        scanner.k8s.get_all_pods = Mock(return_value=[])
        scanner.k8s.get_pods = Mock(return_value=[])
        scanner.k8s.get_cluster_info = Mock(return_value={'nodes': 1, 'pods': 0})

        findings = scanner._check_node_health()

        assert len(findings) > 0
        assert any(f['type'] == 'node_health' for f in findings)
        assert any(f['severity'] == 'critical' for f in findings)


class TestResourceAnalyzer:
    """Test resource analyzer."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value="INFO")
        return config

    @pytest.fixture
    def analyzer(self, mock_config):
        """Create resource analyzer."""
        with patch('kagent.resource_analyzer.K8sClient'):
            fromresource_analyzer import ResourceAnalyzer
            return ResourceAnalyzer(mock_config)

    def test_analyze_returns_findings(self, analyzer):
        """Test that analyze returns list of findings."""
        analyzer.k8s = Mock()
        analyzer.k8s.get_all_pods = Mock(return_value=[])
        analyzer.k8s.get_pods = Mock(return_value=[])
        analyzer.k8s.get_deployments = Mock(return_value=[])
        analyzer.k8s.get_namespaces = Mock(return_value=['default'])

        findings = analyzer.analyze()

        assert isinstance(findings, list)

    def test_detect_missing_limits(self, analyzer):
        """Test detection of missing resource limits."""
        # Create pod with no limits
        pod = Mock()
        pod.metadata.name = "test-pod"
        pod.metadata.namespace = "default"

        container = Mock()
        container.name = "app"
        container.resources = None  # No resources defined

        pod.spec.containers = [container]

        analyzer.k8s = Mock()
        analyzer.k8s.get_all_pods = Mock(return_value=[pod])
        analyzer.k8s.get_pods = Mock(return_value=[])
        analyzer.k8s.get_deployments = Mock(return_value=[])
        analyzer.k8s.get_namespaces = Mock(return_value=['default'])

        findings = analyzer._check_resource_limits()

        assert len(findings) > 0
        assert any('missing' in f['type'] for f in findings)


class TestSecurityScanner:
    """Test security scanner."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value="INFO")
        return config

    @pytest.fixture
    def scanner(self, mock_config):
        """Create security scanner."""
        with patch('kagent.security_scanner.K8sClient'):
            fromsecurity_scanner import SecurityScanner
            return SecurityScanner(mock_config)

    def test_scan_returns_findings(self, scanner):
        """Test that scan returns list of findings."""
        scanner.k8s = Mock()
        scanner.k8s.get_all_pods = Mock(return_value=[])
        scanner.k8s.get_pods = Mock(return_value=[])

        findings = scanner.scan()

        assert isinstance(findings, list)

    def test_detect_privileged_container(self, scanner):
        """Test detection of privileged containers."""
        # Create privileged pod
        pod = Mock()
        pod.metadata.name = "privileged-pod"
        pod.metadata.namespace = "default"

        container = Mock()
        container.name = "app"
        container.security_context = Mock(privileged=True)

        pod.spec.containers = [container]

        scanner.k8s = Mock()
        scanner.k8s.get_all_pods = Mock(return_value=[pod])

        findings = scanner._check_privileged_containers()

        assert len(findings) > 0
        assert findings[0]['severity'] == 'critical'
        assert findings[0]['type'] == 'privileged_container'


class TestPrioritizer:
    """Test finding prioritizer."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def prioritizer(self, mock_config):
        """Create prioritizer."""
        fromprioritizer import FindingPrioritizer
        return FindingPrioritizer(mock_config)

    def test_prioritize_by_severity(self, prioritizer):
        """Test prioritization by severity."""
        findings = [
            {'severity': 'low', 'type': 'test1'},
            {'severity': 'critical', 'type': 'test2'},
            {'severity': 'medium', 'type': 'test3'},
            {'severity': 'high', 'type': 'test4'}
        ]

        prioritized = prioritizer.prioritize(findings)

        # Critical should be first
        assert prioritized[0]['severity'] == 'critical'
        # Low should be last
        assert prioritized[-1]['severity'] == 'low'

    def test_priority_score_calculation(self, prioritizer):
        """Test priority score calculation."""
        critical = {'severity': 'critical', 'type': 'test'}
        high = {'severity': 'high', 'type': 'test'}
        medium = {'severity': 'medium', 'type': 'test'}
        low = {'severity': 'low', 'type': 'test'}

        assert prioritizer._calculate_priority(critical) > prioritizer._calculate_priority(high)
        assert prioritizer._calculate_priority(high) > prioritizer._calculate_priority(medium)
        assert prioritizer._calculate_priority(medium) > prioritizer._calculate_priority(low)


class TestRecommendationGenerator:
    """Test recommendation generator."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.ai_provider = "openai"
        return config

    @pytest.fixture
    def generator(self, mock_config):
        """Create recommendation generator."""
        with patch('kagent.recommendations.get_ai_provider'):
            fromrecommendations import RecommendationGenerator
            return RecommendationGenerator(mock_config)

    def test_generate_recommendations(self, generator):
        """Test recommendation generation."""
        findings = [
            {
                'severity': 'high',
                'type': 'missing_probes',
                'resource': 'pod/test',
                'namespace': 'default',
                'recommendation': 'Add liveness probe'
            }
        ]

        recommendations = generator.generate(findings)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_group_recommendations(self, generator):
        """Test grouped recommendations for multiple findings."""
        findings = [
            {'severity': 'high', 'type': 'missing_probes', 'resource': 'pod/test1'},
            {'severity': 'high', 'type': 'missing_probes', 'resource': 'pod/test2'},
            {'severity': 'high', 'type': 'missing_probes', 'resource': 'pod/test3'}
        ]

        recommendations = generator.generate(findings)

        # Should create group recommendation
        assert any(r.get('type') == 'group' for r in recommendations)


class TestReportGenerator:
    """Test report generator."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def generator(self, mock_config, tmp_path):
        """Create report generator."""
        fromreporter import ReportGenerator
        gen = ReportGenerator(mock_config)
        gen.report_dir = tmp_path  # Use temp directory
        return gen

    def test_generate_json_report(self, generator):
        """Test JSON report generation."""
        findings = [{'severity': 'high', 'type': 'test'}]
        recommendations = [{'title': 'Fix test issue'}]

        report = generator.generate(findings, recommendations, format='json')

        assert isinstance(report, str)
        assert 'findings' in report
        assert 'recommendations' in report

    def test_generate_markdown_report(self, generator):
        """Test Markdown report generation."""
        findings = [{'severity': 'high', 'type': 'test', 'description': 'Test issue'}]
        recommendations = [{'title': 'Fix test issue', 'severity': 'high'}]

        report = generator.generate(findings, recommendations, format='markdown')

        assert '# Kubernetes Cluster Health Report' in report
        assert 'Summary' in report

    def test_generate_text_report(self, generator):
        """Test text report generation."""
        findings = [{'severity': 'high', 'type': 'test'}]
        recommendations = []

        report = generator.generate(findings, recommendations, format='text')

        assert 'KUBERNETES CLUSTER HEALTH REPORT' in report
        assert 'SUMMARY' in report


# Fixtures
@pytest.fixture
def mock_k8s_node():
    """Mock Kubernetes node."""
    node = Mock()
    node.metadata = Mock(name="test-node")
    node.status = Mock()
    node.status.conditions = [Mock(type='Ready', status='True')]
    node.status.capacity = {'cpu': '4', 'memory': '8Gi'}
    return node


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
