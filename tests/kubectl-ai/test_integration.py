"""Integration tests for kubectl-ai.

Tests integration with mock Kubernetes cluster.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


@pytest.mark.integration
class TestKubectlAIWithMockCluster:
    """Integration tests with mocked Kubernetes cluster."""

    @pytest.fixture
    def mock_k8s_response(self):
        """Mock successful kubectl response."""
        return Mock(
            returncode=0,
            stdout="NAME      READY   STATUS    RESTARTS   AGE\npod-1     1/1     Running   0          5m",
            stderr=""
        )

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.ai_provider = "openai"
        config.openai_api_key = "test-key"
        config.get = Mock(side_effect=lambda key, default=None: {
            'kubectl_path': 'kubectl',
            'max_retries': 3,
            'timeout': 30,
            'confirmation_required': False  # Skip confirmation for tests
        }.get(key, default))
        return config

    @pytest.fixture
    def mock_audit_log(self, tmp_path):
        """Mock audit log."""
        from shared.audit import AuditLog
        return AuditLog("kubectl-ai-test", audit_dir=tmp_path / "audit")

    def test_execute_get_pods_command(self, mock_config, mock_audit_log, mock_k8s_response):
        """Test executing a get pods command."""
        from kubectl_ai.executor import CommandExecutor

        with patch('subprocess.run', return_value=mock_k8s_response):
            executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=False)

            intent = {
                'operation': 'get',
                'resource_type': 'pods',
                'destructive': False
            }

            result = executor.execute('kubectl get pods', intent)

            assert result['success'] is True
            assert 'pod-1' in result['output']

    def test_execute_destructive_operation_with_confirmation(self, mock_config, mock_audit_log):
        """Test destructive operation requires confirmation."""
        from kubectl_ai.executor import CommandExecutor

        executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=True)

        intent = {
            'operation': 'delete',
            'resource_type': 'pod',
            'resource_name': 'test-pod',
            'destructive': True,
            'explanation': 'Delete a pod'
        }

        # Mock user declining confirmation
        with patch('shared.confirmation.Confirm.ask', return_value=False):
            result = executor.execute('kubectl delete pod test-pod', intent)

            assert result['success'] is False
            assert 'cancelled' in result['error'].lower()

    def test_full_workflow_list_pods(self, mock_config, mock_audit_log, mock_k8s_response):
        """Test full workflow: parse -> translate -> execute."""
        with patch('kubectl_ai.nl_parser.get_ai_provider'), \
             patch('subprocess.run', return_value=mock_k8s_response):

            from kubectl_ai.nl_parser import NaturalLanguageParser
            from kubectl_ai.translator import KubectlTranslator
            from kubectl_ai.executor import CommandExecutor

            # Parse natural language
            parser = NaturalLanguageParser(mock_config)
            intent = parser._rule_based_parse("list all pods")

            # Translate to kubectl command
            translator = KubectlTranslator(mock_config)
            command = translator.translate(intent)

            # Execute command
            executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=False)
            result = executor.execute(command, intent)

            assert result['success'] is True
            assert 'pod-1' in result['output']

    def test_full_workflow_scale_deployment(self, mock_config, mock_audit_log):
        """Test full workflow for scale operation."""
        mock_response = Mock(
            returncode=0,
            stdout="deployment.apps/nginx scaled",
            stderr=""
        )

        with patch('kubectl_ai.nl_parser.get_ai_provider'), \
             patch('subprocess.run', return_value=mock_response):

            from kubectl_ai.nl_parser import NaturalLanguageParser
            from kubectl_ai.translator import KubectlTranslator
            from kubectl_ai.executor import CommandExecutor

            parser = NaturalLanguageParser(mock_config)
            intent = parser._rule_based_parse("scale nginx deployment to 5 replicas")

            translator = KubectlTranslator(mock_config)
            command = translator.translate(intent)

            executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=False)
            result = executor.execute(command, intent)

            assert result['success'] is True
            assert 'scaled' in result['output']

    def test_troubleshooter_analysis(self, mock_config):
        """Test troubleshooter provides analysis."""
        with patch('kubectl_ai.troubleshooter.get_ai_provider') as mock_ai, \
             patch('kubectl_ai.troubleshooter.K8sClient'):

            # Mock AI response
            mock_provider = Mock()
            mock_provider.generate.return_value = """
EXPLANATION:
The pod is likely crashing due to misconfiguration or missing dependencies.

COMMANDS:
- kubectl describe pod crashing-pod
- kubectl logs crashing-pod
- kubectl get events

SOLUTIONS:
1. Check pod logs for error messages
2. Verify container image is correct
3. Check resource limits
"""
            mock_ai.return_value = mock_provider

            from kubectl_ai.troubleshooter import KubectlTroubleshooter

            troubleshooter = KubectlTroubleshooter(mock_config)
            analysis = troubleshooter.analyze("pod keeps crashing")

            assert 'explanation' in analysis
            assert len(analysis['commands']) > 0
            assert len(analysis['suggestions']) > 0

    def test_audit_log_records_operations(self, mock_config, mock_audit_log, mock_k8s_response):
        """Test that operations are recorded in audit log."""
        from kubectl_ai.executor import CommandExecutor

        with patch('subprocess.run', return_value=mock_k8s_response):
            executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=False)

            intent = {'operation': 'get', 'destructive': False}
            executor.execute('kubectl get pods', intent)

            # Check audit log has entry
            entries = mock_audit_log.get_entries(days=1)
            assert len(entries) > 0
            assert 'kubectl get pods' in entries[-1]['metadata']['command']


@pytest.mark.integration
@pytest.mark.slow
class TestKubectlAIWithRealCluster:
    """Integration tests with real Kubernetes cluster (requires kubectl)."""

    @pytest.fixture
    def skip_if_no_kubectl(self):
        """Skip test if kubectl is not available."""
        import subprocess
        try:
            subprocess.run(['kubectl', 'version', '--client'],
                         capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("kubectl not available")

    def test_connection_check(self, skip_if_no_kubectl, mock_config, mock_audit_log):
        """Test kubectl connection (requires configured cluster)."""
        from kubectl_ai.executor import CommandExecutor

        executor = CommandExecutor(mock_config, mock_audit_log, require_confirmation=False)

        # This will fail if no cluster is configured, which is expected
        result = executor.test_connection()
        # Just checking it doesn't crash


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
