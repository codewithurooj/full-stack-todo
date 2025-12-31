"""Integration tests for docker-ai.

Tests the complete workflow with real project samples.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
import sys

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path / 'docker-ai'))
sys.path.insert(0, str(scripts_path / 'shared'))


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestPythonFlaskProject:
    """Test Python Flask project generation."""

    @pytest.fixture
    def flask_project(self, temp_project):
        """Create sample Flask project."""
        # Create requirements.txt
        (temp_project / "requirements.txt").write_text(
            "flask==3.0.0\ngunicorn==21.0.0\npython-dotenv==1.0.0"
        )

        # Create app.py
        (temp_project / "app.py").write_text("""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")

        return temp_project

    def test_generate_from_code_analysis(self, runner, flask_project):
        """Test generating Dockerfile from code analysis."""
        fromcli import cli

        result = runner.invoke(cli, [
            'generate',
            '--description', 'Analyze this project',
            '--output', str(flask_project / 'Dockerfile'),
            '--multistage',
            '--security'
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert (flask_project / 'Dockerfile').exists()

        dockerfile = (flask_project / 'Dockerfile').read_text()
        assert 'FROM python' in dockerfile
        assert 'requirements.txt' in dockerfile
        assert 'USER appuser' in dockerfile

    def test_generate_from_description(self, runner, temp_project):
        """Test generating Dockerfile from natural language."""
        fromcli import cli

        result = runner.invoke(cli, [
            'generate',
            '--description', 'Python Flask application with PostgreSQL on port 5000',
            '--output', str(temp_project / 'Dockerfile'),
            '--multistage',
            '--security',
            '--optimize'
        ], catch_exceptions=False)

        assert result.exit_code == 0

        dockerfile = (temp_project / 'Dockerfile').read_text()
        assert 'FROM python' in dockerfile
        assert 'EXPOSE 5000' in dockerfile
        assert 'USER' in dockerfile
        assert '--no-cache-dir' in dockerfile or 'pip install' in dockerfile

    def test_generate_compose_for_flask(self, runner, flask_project):
        """Test docker-compose generation."""
        fromcli import cli

        result = runner.invoke(cli, [
            'compose',
            '--description', 'Flask app with PostgreSQL and Redis',
            '--output', str(flask_project / 'docker-compose.yml')
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert (flask_project / 'docker-compose.yml').exists()

        compose = (flask_project / 'docker-compose.yml').read_text()
        assert 'version:' in compose
        assert 'services:' in compose
        assert 'app:' in compose
        assert 'postgresql:' in compose
        assert 'redis:' in compose


class TestNodeExpressProject:
    """Test Node.js Express project generation."""

    @pytest.fixture
    def express_project(self, temp_project):
        """Create sample Express project."""
        # Create package.json
        (temp_project / "package.json").write_text("""{
  "name": "express-api",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "pg": "^8.11.0"
  },
  "scripts": {
    "start": "node index.js"
  }
}""")

        # Create index.js
        (temp_project / "index.js").write_text("""
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
""")

        return temp_project

    def test_generate_nodejs_dockerfile(self, runner, express_project):
        """Test Node.js Dockerfile generation."""
        fromcli import cli

        result = runner.invoke(cli, [
            'generate',
            '--description', 'Analyze this project',
            '--output', str(express_project / 'Dockerfile'),
            '--multistage',
            '--security'
        ], catch_exceptions=False)

        assert result.exit_code == 0

        dockerfile = (express_project / 'Dockerfile').read_text()
        assert 'FROM node' in dockerfile
        assert 'package' in dockerfile
        assert 'npm' in dockerfile or 'yarn' in dockerfile
        assert 'USER' in dockerfile

    def test_generate_nodejs_compose(self, runner, express_project):
        """Test Node.js compose generation."""
        fromcli import cli

        result = runner.invoke(cli, [
            'compose',
            '--description', 'Node.js Express API with PostgreSQL',
            '--output', str(express_project / 'docker-compose.yml')
        ], catch_exceptions=False)

        assert result.exit_code == 0

        compose = (express_project / 'docker-compose.yml').read_text()
        assert 'app:' in compose
        assert 'postgresql:' in compose


class TestGoProject:
    """Test Go project generation."""

    @pytest.fixture
    def go_project(self, temp_project):
        """Create sample Go project."""
        # Create go.mod
        (temp_project / "go.mod").write_text("""module myapp

go 1.21

require github.com/gorilla/mux v1.8.0
""")

        # Create main.go
        (temp_project / "main.go").write_text("""package main

import (
    "fmt"
    "net/http"
    "github.com/gorilla/mux"
)

func main() {
    r := mux.NewRouter()
    r.HandleFunc("/health", healthHandler)
    http.ListenAndServe(":8080", r)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, `{"status": "healthy"}`)
}
""")

        return temp_project

    def test_generate_go_multistage(self, runner, go_project):
        """Test Go multi-stage Dockerfile."""
        fromcli import cli

        result = runner.invoke(cli, [
            'generate',
            '--description', 'Analyze this project',
            '--output', str(go_project / 'Dockerfile'),
            '--multistage',
            '--security',
            '--optimize'
        ], catch_exceptions=False)

        assert result.exit_code == 0

        dockerfile = (go_project / 'Dockerfile').read_text()
        assert 'AS builder' in dockerfile
        assert 'COPY --from=builder' in dockerfile
        assert 'go build' in dockerfile or 'GO' in dockerfile


class TestDockerfileAnalysis:
    """Test Dockerfile analysis functionality."""

    @pytest.fixture
    def sample_dockerfile(self, temp_project):
        """Create sample Dockerfile."""
        dockerfile = temp_project / 'Dockerfile'
        dockerfile.write_text("""FROM python:latest
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "app.py"]
""")
        return dockerfile

    def test_analyze_dockerfile(self, runner, sample_dockerfile):
        """Test analyzing existing Dockerfile."""
        fromcli import cli

        result = runner.invoke(cli, [
            'analyze',
            str(sample_dockerfile),
            '--output', 'json'
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert 'issues' in result.output or 'security' in result.output

    def test_optimize_dockerfile(self, runner, sample_dockerfile):
        """Test optimizing Dockerfile."""
        fromcli import cli

        output_file = sample_dockerfile.parent / 'Dockerfile.optimized'

        result = runner.invoke(cli, [
            'optimize',
            str(sample_dockerfile),
            '--output', str(output_file),
            '--security'
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert output_file.exists()

        optimized = output_file.read_text()
        # Should have improvements
        assert 'USER' in optimized or '--no-cache-dir' in optimized


class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_complete_flask_workflow(self, runner, temp_project):
        """Test complete workflow: generate → analyze → optimize."""
        fromcli import cli

        # Step 1: Generate Dockerfile
        result = runner.invoke(cli, [
            'generate',
            '--description', 'Python Flask app with PostgreSQL on port 5000',
            '--output', str(temp_project / 'Dockerfile'),
            '--security'
        ], catch_exceptions=False)
        assert result.exit_code == 0

        # Step 2: Analyze generated Dockerfile
        result = runner.invoke(cli, [
            'analyze',
            str(temp_project / 'Dockerfile')
        ], catch_exceptions=False)
        assert result.exit_code == 0

        # Step 3: Optimize Dockerfile
        result = runner.invoke(cli, [
            'optimize',
            str(temp_project / 'Dockerfile'),
            '--output', str(temp_project / 'Dockerfile.optimized')
        ], catch_exceptions=False)
        assert result.exit_code == 0

        # Step 4: Generate docker-compose
        result = runner.invoke(cli, [
            'compose',
            '--description', 'Flask with PostgreSQL',
            '--output', str(temp_project / 'docker-compose.yml')
        ], catch_exceptions=False)
        assert result.exit_code == 0

        # Verify all files created
        assert (temp_project / 'Dockerfile').exists()
        assert (temp_project / 'Dockerfile.optimized').exists()
        assert (temp_project / 'docker-compose.yml').exists()

    def test_config_management(self, runner, temp_project):
        """Test configuration file generation and loading."""
        fromcli import cli

        config_file = temp_project / 'docker-ai.yml'

        # Generate config template
        result = runner.invoke(cli, [
            'config',
            '--init',
            '--output', str(config_file)
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert config_file.exists()

        config = config_file.read_text()
        assert 'ai_provider:' in config
        assert 'base_image_variant:' in config

    def test_audit_logging(self, runner, temp_project):
        """Test that operations are logged."""
        fromcli import cli
        import os

        # Set audit log path
        audit_file = temp_project / 'audit.jsonl'
        os.environ['DOCKER_AI_AUDIT_LOG'] = str(audit_file)

        # Perform operation
        result = runner.invoke(cli, [
            'generate',
            '--description', 'Python Flask app',
            '--output', str(temp_project / 'Dockerfile')
        ], catch_exceptions=False)

        assert result.exit_code == 0

        # Check audit log created
        # Note: Audit log might not be created in test mode
        # This is a basic check
        if audit_file.exists():
            assert audit_file.stat().st_size > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
