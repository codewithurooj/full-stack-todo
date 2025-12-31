"""Unit tests for kubectl-ai CLI.

Tests command parsing, translation, and execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path / 'kubectl-ai'))
sys.path.insert(0, str(scripts_path / 'shared'))

from nl_parser import NaturalLanguageParser
from translator import KubectlTranslator
from context import CommandContext


class TestNaturalLanguageParser:
    """Test natural language parsing."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.ai_provider = "openai"
        config.openai_api_key = "test-key"
        config.get = Mock(return_value="INFO")
        return config

    @pytest.fixture
    def parser(self, mock_config):
        """Create parser instance."""
        with patch('nl_parser.get_ai_provider'):
            return NaturalLanguageParser(mock_config)

    def test_parse_list_pods(self, parser):
        """Test parsing 'list all pods' query."""
        result = parser._rule_based_parse("list all pods")

        assert result['operation'] == 'get' or result['operation'] == 'list'
        assert result['resource_type'] in ['pod', 'pods']
        assert result['all_namespaces'] or not result.get('namespace')

    def test_parse_scale_deployment(self, parser):
        """Test parsing scale operation."""
        result = parser._rule_based_parse("scale nginx deployment to 5 replicas")

        assert result['operation'] == 'scale'
        assert 'deployment' in result['resource_type']
        assert result['resource_name'] == 'nginx'
        assert result['replicas'] == 5

    def test_parse_delete_pod(self, parser):
        """Test parsing destructive operation."""
        result = parser._rule_based_parse("delete pod test-pod")

        assert result['operation'] == 'delete'
        assert result['resource_type'] in ['pod', 'pods']
        assert result['resource_name'] == 'test-pod'
        assert result['destructive'] is True

    def test_parse_with_namespace(self, parser):
        """Test parsing with namespace specification."""
        result = parser._rule_based_parse("list pods in namespace production")

        assert result['namespace'] == 'production'
        assert not result['all_namespaces']

    def test_parse_all_namespaces(self, parser):
        """Test parsing all namespaces flag."""
        result = parser._rule_based_parse("list all pods across all namespaces")

        assert result['all_namespaces'] is True

    def test_parse_describe_operation(self, parser):
        """Test parsing describe operation."""
        result = parser._rule_based_parse("describe deployment nginx")

        assert result['operation'] == 'describe'
        assert 'deployment' in result['resource_type']
        assert result['resource_name'] == 'nginx'

    def test_extract_kubectl_context(self, parser):
        """Test context extraction."""
        context = parser.extract_kubectl_context("get pods in namespace test with label app=nginx")

        assert context['namespace'] == 'test'
        assert 'app=nginx' in context['labels']


class TestKubectlTranslator:
    """Test kubectl command translation."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value='kubectl')
        return config

    @pytest.fixture
    def translator(self, mock_config):
        """Create translator instance."""
        return KubectlTranslator(mock_config)

    def test_translate_get_pods(self, translator):
        """Test translating get pods operation."""
        intent = {
            'operation': 'get',
            'resource_type': 'pods',
            'namespace': None,
            'all_namespaces': True
        }

        command = translator.translate(intent)

        assert 'kubectl get pods' in command
        assert '--all-namespaces' in command

    def test_translate_scale(self, translator):
        """Test translating scale operation."""
        intent = {
            'operation': 'scale',
            'resource_type': 'deployment',
            'resource_name': 'nginx',
            'replicas': 5,
            'namespace': 'default'
        }

        command = translator.translate(intent)

        assert 'kubectl scale' in command
        assert 'deployment/nginx' in command
        assert '--replicas=5' in command
        assert '-n default' in command

    def test_translate_delete(self, translator):
        """Test translating delete operation."""
        intent = {
            'operation': 'delete',
            'resource_type': 'pod',
            'resource_name': 'test-pod',
            'namespace': 'test'
        }

        command = translator.translate(intent)

        assert 'kubectl delete pod test-pod' in command
        assert '-n test' in command

    def test_translate_describe(self, translator):
        """Test translating describe operation."""
        intent = {
            'operation': 'describe',
            'resource_type': 'deployment',
            'resource_name': 'api-server',
            'namespace': 'production'
        }

        command = translator.translate(intent)

        assert 'kubectl describe deployment api-server' in command
        assert '-n production' in command

    def test_translate_logs(self, translator):
        """Test translating logs operation."""
        intent = {
            'operation': 'logs',
            'resource_name': 'app-pod',
            'namespace': 'default'
        }

        command = translator.translate(intent)

        assert 'kubectl logs app-pod' in command
        assert '--tail=100' in command

    def test_validate_command(self, translator):
        """Test command validation."""
        assert translator.validate_command('kubectl get pods') is True
        assert translator.validate_command('kubectl delete pod test') is True
        assert translator.validate_command('rm -rf /') is False
        assert translator.validate_command('kubectl get pods && echo hack') is False


class TestCommandContext:
    """Test command context manager."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value=True)
        return config

    @pytest.fixture
    def context(self, mock_config, tmp_path):
        """Create context instance with temp directory."""
        with patch('context.Path.home', return_value=tmp_path):
            return CommandContext(mock_config)

    def test_initial_namespace(self, context):
        """Test default namespace is set."""
        assert context.current_namespace == 'default'

    def test_set_namespace(self, context):
        """Test changing namespace."""
        context.set_namespace('production')
        assert context.current_namespace == 'production'

    def test_conversation_history(self, context):
        """Test conversation history management."""
        context.add_to_history('user', 'list pods')
        context.add_to_history('assistant', 'kubectl get pods')

        history = context.get_history()
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'

    def test_history_limit(self, context):
        """Test history is limited to 10 messages."""
        for i in range(15):
            context.add_to_history('user', f'message {i}')

        history = context.get_history()
        assert len(history) == 10

    def test_get_context_info(self, context):
        """Test getting context information."""
        context.set_namespace('test')
        context.add_to_history('user', 'test')

        info = context.get_context_info()
        assert info['namespace'] == 'test'
        assert info['history_length'] == 1

    def test_reset_context(self, context):
        """Test resetting context."""
        context.set_namespace('production')
        context.add_to_history('user', 'test')

        context.reset()

        assert context.current_namespace == 'default'
        assert len(context.conversation_history) == 0


# Integration-style tests

class TestKubectlAIIntegration:
    """Integration tests for kubectl-ai components."""

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
            'context_persistence': False
        }.get(key, default))
        return config

    def test_end_to_end_get_pods(self, mock_config):
        """Test end-to-end: parse -> translate -> validate."""
        with patch('nl_parser.get_ai_provider'):
            parser = NaturalLanguageParser(mock_config)
            translator = KubectlTranslator(mock_config)

            # Parse
            intent = parser._rule_based_parse("list all pods in production")

            # Translate
            command = translator.translate(intent)

            # Validate
            assert translator.validate_command(command)
            assert 'kubectl' in command
            assert 'pods' in command

    def test_end_to_end_scale(self, mock_config):
        """Test end-to-end scale operation."""
        with patch('nl_parser.get_ai_provider'):
            parser = NaturalLanguageParser(mock_config)
            translator = KubectlTranslator(mock_config)

            intent = parser._rule_based_parse("scale nginx deployment to 3 replicas")
            command = translator.translate(intent)

            assert 'scale' in command
            assert 'nginx' in command
            assert 'replicas=3' in command


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
