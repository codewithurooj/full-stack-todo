"""Unit tests for docker-ai components.

Tests Dockerfile generation, code analysis, and optimization.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path / 'docker-ai'))
sys.path.insert(0, str(scripts_path / 'shared'))


class TestCodeAnalyzer:
    """Test code analyzer."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def analyzer(self, mock_config):
        """Create code analyzer."""
        fromcode_analyzer import CodeAnalyzer
        return CodeAnalyzer(mock_config)

    def test_detect_python(self, analyzer, tmp_path):
        """Test Python detection."""
        # Create Python project
        (tmp_path / "requirements.txt").write_text("flask==3.0.0")
        (tmp_path / "app.py").write_text("from flask import Flask")

        result = analyzer.analyze(tmp_path)

        assert result['language'] == 'python'

    def test_detect_flask_framework(self, analyzer, tmp_path):
        """Test Flask framework detection."""
        (tmp_path / "requirements.txt").write_text("flask==3.0.0\ngunicorn==21.0.0")
        (tmp_path / "app.py").write_text("# Flask app")

        result = analyzer.analyze(tmp_path)

        assert result['language'] == 'python'
        assert result['framework'] == 'flask'

    def test_detect_nodejs(self, analyzer, tmp_path):
        """Test Node.js detection."""
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.18.0"}}')
        (tmp_path / "index.js").write_text("const express = require('express');")

        result = analyzer.analyze(tmp_path)

        assert result['language'] in ['javascript', 'typescript']
        assert result['framework'] == 'express'

    def test_detect_go(self, analyzer, tmp_path):
        """Test Go detection."""
        (tmp_path / "go.mod").write_text("module myapp\n\ngo 1.21")
        (tmp_path / "main.go").write_text("package main")

        result = analyzer.analyze(tmp_path)

        assert result['language'] == 'go'


class TestNaturalLanguageProcessor:
    """Test NL processor."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.ai_provider = "openai"
        return config

    @pytest.fixture
    def processor(self, mock_config):
        """Create NL processor."""
        with patch('docker_ai.nl_processor.get_ai_provider'):
            fromnl_processor import NaturalLanguageProcessor
            return NaturalLanguageProcessor(mock_config)

    def test_parse_simple_description(self, processor):
        """Test parsing simple description."""
        result = processor._rule_based_parse("Python Flask application")

        assert result['language'] == 'python'
        assert result['framework'] == 'flask'

    def test_parse_with_services(self, processor):
        """Test parsing with services."""
        result = processor._rule_based_parse("Node.js Express API with PostgreSQL and Redis")

        assert result['language'] == 'javascript'
        assert result['framework'] == 'express'
        assert 'postgresql' in result['services']
        assert 'redis' in result['services']

    def test_parse_with_ports(self, processor):
        """Test parsing with port numbers."""
        result = processor._rule_based_parse("Flask app on port 8080")

        assert result['language'] == 'python'
        assert 8080 in result['ports']


class TestBaseImageSelector:
    """Test base image selector."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value='alpine')
        return config

    @pytest.fixture
    def selector(self, mock_config):
        """Create base image selector."""
        frombase_image import BaseImageSelector
        return BaseImageSelector(mock_config)

    def test_select_python_images(self, selector):
        """Test Python image selection."""
        images = selector.select('python')

        assert 'python' in images['build'].lower()
        assert 'python' in images['runtime'].lower()
        assert 'alpine' in images['runtime'].lower()

    def test_select_nodejs_images(self, selector):
        """Test Node.js image selection."""
        images = selector.select('javascript')

        assert 'node' in images['build'].lower()
        assert 'alpine' in images['runtime'].lower()

    def test_select_go_images(self, selector):
        """Test Go image selection."""
        images = selector.select('go')

        assert 'go' in images['build'].lower() or 'golang' in images['build'].lower()


class TestDockerfileGenerator:
    """Test Dockerfile generator."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get = Mock(return_value='alpine')
        return config

    @pytest.fixture
    def generator(self, mock_config):
        """Create Dockerfile generator."""
        fromgenerator import DockerfileGenerator
        return DockerfileGenerator(mock_config)

    def test_generate_python_dockerfile(self, generator):
        """Test Python Dockerfile generation."""
        spec = {
            'language': 'python',
            'framework': 'flask',
            'ports': [5000]
        }

        dockerfile = generator.generate_from_spec(spec)

        assert 'FROM python' in dockerfile
        assert 'WORKDIR /app' in dockerfile
        assert 'COPY requirements.txt' in dockerfile
        assert 'EXPOSE 5000' in dockerfile

    def test_generate_nodejs_dockerfile(self, generator):
        """Test Node.js Dockerfile generation."""
        spec = {
            'language': 'javascript',
            'framework': 'express',
            'ports': [3000]
        }

        dockerfile = generator.generate_from_spec(spec)

        assert 'FROM node' in dockerfile
        assert 'COPY package' in dockerfile
        assert 'EXPOSE 3000' in dockerfile

    def test_security_hardening_included(self, generator):
        """Test that security hardening is applied."""
        spec = {
            'language': 'python',
            'framework': 'flask',
            'ports': [5000]
        }

        dockerfile = generator.generate_from_spec(spec)

        assert 'USER' in dockerfile  # Non-root user
        assert 'appuser' in dockerfile

    def test_multistage_for_go(self, generator):
        """Test multi-stage build for Go."""
        spec = {
            'language': 'go',
            'ports': [8080]
        }

        dockerfile = generator.generate_from_spec(spec)

        assert 'AS builder' in dockerfile
        assert 'COPY --from=builder' in dockerfile


class TestSecurityHardener:
    """Test security hardener."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def hardener(self, mock_config):
        """Create security hardener."""
        fromsecurity import SecurityHardener
        return SecurityHardener(mock_config)

    def test_check_missing_user(self, hardener):
        """Test detection of missing USER directive."""
        dockerfile = """
FROM python:3.13-alpine
WORKDIR /app
COPY . .
CMD ["python", "app.py"]
"""

        issues = hardener.check_security(dockerfile)

        assert any('USER' in issue for issue in issues)

    def test_check_latest_tag(self, hardener):
        """Test detection of :latest tag."""
        dockerfile = """
FROM python:latest
WORKDIR /app
"""

        issues = hardener.check_security(dockerfile)

        assert any('latest' in issue.lower() for issue in issues)


class TestLayerOptimizer:
    """Test layer optimizer."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def optimizer(self, mock_config):
        """Create layer optimizer."""
        fromoptimizer import LayerOptimizer
        return LayerOptimizer(mock_config)

    def test_add_no_cache_to_pip(self, optimizer):
        """Test adding --no-cache-dir to pip install."""
        line = "RUN pip install -r requirements.txt"

        optimized = optimizer._optimize_line(line)

        assert '--no-cache-dir' in optimized

    def test_add_no_cache_to_apk(self, optimizer):
        """Test adding --no-cache to apk add."""
        line = "RUN apk add gcc musl-dev"

        optimized = optimizer._optimize_line(line)

        assert '--no-cache' in optimized


class TestDockerfileAnalyzer:
    """Test Dockerfile analyzer."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def analyzer(self, mock_config):
        """Create Dockerfile analyzer."""
        fromanalyzer import DockerfileAnalyzer
        return DockerfileAnalyzer(mock_config)

    def test_analyze_simple_dockerfile(self, analyzer):
        """Test analyzing a simple Dockerfile."""
        dockerfile = """
FROM python:3.13-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""

        analysis = analyzer.analyze_content(dockerfile)

        assert 'issues' in analysis
        assert 'security_issues' in analysis
        assert 'suggestions' in analysis

    def test_detect_missing_healthcheck(self, analyzer):
        """Test detection of missing HEALTHCHECK."""
        dockerfile = """
FROM python:3.13-alpine
WORKDIR /app
CMD ["python", "app.py"]
"""

        analysis = analyzer.analyze_content(dockerfile)

        assert any('health' in str(item).lower() for item in analysis['best_practices'])


class TestComposeGenerator:
    """Test docker-compose generator."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return Mock()

    @pytest.fixture
    def generator(self, mock_config):
        """Create compose generator."""
        fromcompose_generator import ComposeGenerator
        return ComposeGenerator(mock_config)

    def test_generate_simple_compose(self, generator):
        """Test simple compose generation."""
        spec = {
            'language': 'python',
            'framework': 'flask',
            'services': ['postgresql'],
            'ports': [5000]
        }

        compose = generator.generate(spec)

        assert 'version' in compose
        assert 'services' in compose
        assert 'app:' in compose
        assert 'postgresql:' in compose

    def test_generate_multi_service_compose(self, generator):
        """Test multi-service compose generation."""
        spec = {
            'language': 'javascript',
            'framework': 'express',
            'services': ['postgresql', 'redis', 'mongodb'],
            'ports': [3000]
        }

        compose = generator.generate(spec)

        assert 'postgresql:' in compose
        assert 'redis:' in compose
        assert 'mongodb:' in compose


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
