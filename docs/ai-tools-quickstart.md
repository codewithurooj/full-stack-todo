# AI-Powered Tools Quickstart Guide

Get started with kubectl-ai, kagent, and docker-ai in 5 minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.13+** installed
- **kubectl** configured (for kubectl-ai and kagent)
- **Docker** installed (for docker-ai)
- **AI API Key** (OpenAI or Anthropic)

### Check Prerequisites

```bash
# Check Python version
python --version  # Should be 3.13 or higher

# Check kubectl (for kubectl-ai and kagent)
kubectl version --client

# Check Docker (for docker-ai)
docker --version

# Verify kubectl cluster access (optional for kubectl-ai/kagent)
kubectl cluster-info
```

## Installation

### 1. Navigate to Scripts Directory

```bash
cd full-stack-todo/scripts
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Installation Script

```bash
# On Linux/Mac:
bash install.sh

# On Windows:
# Run commands manually from install.sh
```

### 4. Configure AI Provider

Set up your AI API key:

```bash
# For OpenAI
export OPENAI_API_KEY='sk-your-key-here'
export OPENAI_MODEL='gpt-4o-mini'

# OR for Anthropic
export ANTHROPIC_API_KEY='your-key-here'
export ANTHROPIC_MODEL='claude-3-5-sonnet-20241022'
```

**Make it permanent:**

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`):

```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 5. Verify Installation

```bash
kubectl-ai --help
kagent --help
docker-ai --help
```

If you see help output, you're ready to go!

## Quick Start: kubectl-ai

Natural language interface for Kubernetes.

### Your First Command

```bash
# List all pods
kubectl-ai execute "list all pods"
```

### More Examples

```bash
# Get pods in a specific namespace
kubectl-ai execute "show pods in production namespace"

# Scale a deployment
kubectl-ai execute "scale nginx deployment to 5 replicas"

# Delete a pod (with confirmation)
kubectl-ai execute "delete pod broken-pod"

# View logs
kubectl-ai execute "show logs for nginx pod"

# Troubleshoot issues
kubectl-ai troubleshoot "my pods keep crashing"
kubectl-ai troubleshoot "service not accessible"
```

### Useful Options

```bash
# Dry run (see command without executing)
kubectl-ai execute "delete all pods" --dry-run

# Skip confirmation
kubectl-ai execute "scale nginx to 3" --no-confirm

# View audit log
kubectl-ai audit --limit 20

# Check configuration
kubectl-ai config
```

## Quick Start: kagent

Cluster health analysis and recommendations.

### Your First Analysis

```bash
# Run comprehensive cluster analysis
kagent analyze
```

This will scan your cluster and show:
- Health issues
- Security vulnerabilities
- Resource optimization opportunities
- Configuration problems
- Performance issues

### More Examples

```bash
# Analyze specific namespace
kagent analyze --namespace production

# Save analysis report
kagent analyze --save --output json

# Run specific scanner
kagent scan --scanner security
kagent scan --scanner resources
kagent scan --scanner performance

# Generate detailed report
kagent report --format markdown
kagent report --format json --output report.json

# View analysis history
kagent history --limit 10

# Continuous monitoring (every 5 minutes)
kagent monitor --interval 300
```

### Understanding Results

kagent prioritizes findings by severity:

- **Critical** (red): Immediate action required
- **High** (orange): Should fix soon
- **Medium** (yellow): Best practice improvements
- **Low** (blue): Nice to have optimizations

Each finding includes:
- Clear description
- Impact explanation
- Actionable recommendation
- kubectl command to fix (when applicable)

## Quick Start: docker-ai

AI-powered Dockerfile generation.

### Your First Dockerfile

```bash
# Generate from natural language
docker-ai generate "Python Flask application with PostgreSQL on port 5000"
```

This creates an optimized `Dockerfile` with:
- Multi-stage builds
- Security hardening (non-root user)
- Layer caching optimization
- Best practices applied

### More Examples

```bash
# Generate from existing code
cd your-project/
docker-ai analyze .

# Generate for different languages
docker-ai generate "Node.js Express API with MongoDB"
docker-ai generate "Go web server with PostgreSQL"
docker-ai generate "Ruby on Rails app with Redis"

# Optimize existing Dockerfile
docker-ai optimize ./Dockerfile
docker-ai optimize ./Dockerfile --output Dockerfile.optimized

# Generate docker-compose.yml
docker-ai compose "Flask API with PostgreSQL and Redis"
docker-ai compose "Node.js app with MySQL" --output docker-compose.dev.yml
```

### Build and Test

```bash
# After generating Dockerfile
docker build -t myapp .
docker run -p 5000:5000 myapp

# After generating docker-compose.yml
docker-compose up
```

## Common Workflows

### Workflow 1: Deploy New Kubernetes App

```bash
# 1. Generate Dockerfile
docker-ai generate "Node.js Express API on port 3000"

# 2. Build and test locally
docker build -t myapp .
docker run -p 3000:3000 myapp

# 3. Deploy to Kubernetes
kubectl-ai execute "create deployment myapp with image myapp"
kubectl-ai execute "expose deployment myapp on port 3000"

# 4. Verify deployment
kubectl-ai execute "list pods for myapp"

# 5. Run cluster analysis
kagent analyze --namespace default
```

### Workflow 2: Troubleshoot Cluster Issues

```bash
# 1. Run cluster analysis
kagent analyze

# 2. Check specific issues
kagent scan --scanner security
kagent scan --scanner health

# 3. Get troubleshooting help
kubectl-ai troubleshoot "pods in crashloop"

# 4. Apply fixes
kubectl-ai execute "delete pod failing-pod"
kubectl-ai execute "scale deployment to 3 replicas"

# 5. Re-analyze to verify
kagent analyze
```

### Workflow 3: Optimize Existing Dockerfiles

```bash
# 1. Analyze current Dockerfile
docker-ai optimize ./Dockerfile --output Dockerfile.new

# 2. Compare changes
diff Dockerfile Dockerfile.new

# 3. Build and test
docker build -f Dockerfile.new -t myapp:optimized .

# 4. Check image size reduction
docker images | grep myapp
```

## Configuration

### kubectl-ai Configuration

```bash
# Generate config template
kubectl-ai config

# Edit configuration
# File: ~/.kubectl-ai/config.yaml
```

**Common settings:**

```yaml
ai_provider: openai           # or 'anthropic'
log_level: INFO               # or DEBUG
confirmation_required: true   # Safety confirmations
audit_enabled: true          # Audit logging
kubectl_path: kubectl        # kubectl binary path
max_retries: 3               # Retry attempts
```

### kagent Configuration

```bash
# Generate config template
kagent config

# File: ~/.kagent/config.yaml
```

**Common settings:**

```yaml
ai_provider: openai
default_output_format: text  # or 'json', 'markdown'
severity_threshold: medium   # Filter findings
save_reports: true          # Auto-save reports
scan_interval: 3600         # For continuous monitoring
```

### docker-ai Configuration

```bash
# Generate config template
docker-ai config

# File: ~/.docker-ai/config.yaml
```

**Common settings:**

```yaml
ai_provider: openai
base_image_variant: alpine   # or 'slim', 'distroless'
enable_multistage: true     # Multi-stage builds
enable_security: true       # Security hardening
enable_optimization: true   # Layer optimization
```

## Troubleshooting

### "Command not found"

```bash
# Activate virtual environment
source venv/bin/activate

# Or reinstall
bash install.sh
```

### "Cannot connect to cluster"

```bash
# Check kubectl connection
kubectl cluster-info

# Switch context if needed
kubectl config get-contexts
kubectl config use-context <context-name>
```

### "AI Provider Error"

```bash
# Check API key is set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set it temporarily
export OPENAI_API_KEY='your-key'

# Or add to tool's .env
echo "OPENAI_API_KEY=your-key" >> ~/.kubectl-ai/.env
```

### Enable Debug Logging

```bash
# For any tool, add --debug flag
kubectl-ai --debug execute "list pods"
kagent --debug analyze
docker-ai --debug generate "Flask app"
```

### View Audit Logs

```bash
# Check what operations were performed
kubectl-ai audit --limit 50
kagent history --limit 20
docker-ai audit --limit 20
```

## Best Practices

### kubectl-ai

1. **Use dry-run first** for destructive operations
2. **Keep confirmations enabled** in production
3. **Review audit logs** regularly
4. **Use specific namespaces** to avoid mistakes
5. **Test troubleshooting** with `--dry-run`

### kagent

1. **Run weekly scans** of production clusters
2. **Set up continuous monitoring** for critical clusters
3. **Prioritize critical/high** severity findings
4. **Save reports** for trend analysis
5. **Act on security issues** immediately

### docker-ai

1. **Use multi-stage builds** for production
2. **Always enable security** hardening
3. **Test generated Dockerfiles** before deploying
4. **Pin specific versions** (already done by default)
5. **Optimize for your use case** (development vs production)

## Next Steps

### Learn More

- **Full Documentation**: `scripts/README.md`
- **kubectl-ai Skill**: `.claude/skills/kubectl-ai.md`
- **kagent Skill**: `.claude/skills/kagent.md`
- **docker-ai Skill**: `.claude/skills/dockerfile-generator.md`

### Run Tests

```bash
# Test all tools
cd full-stack-todo
pytest tests/ -v

# Test specific tool
pytest tests/kubectl-ai/ -v
pytest tests/kagent/ -v
pytest tests/docker-ai/ -v
```

### Explore Advanced Features

**kubectl-ai:**
- Session context management
- Custom kubectl path
- Multi-step troubleshooting

**kagent:**
- Historical trend analysis
- Custom severity thresholds
- Report scheduling

**docker-ai:**
- Custom base images
- Framework-specific optimizations
- Service orchestration

## Getting Help

### View Help

```bash
kubectl-ai --help
kubectl-ai execute --help
kubectl-ai troubleshoot --help

kagent --help
kagent analyze --help
kagent scan --help

docker-ai --help
docker-ai generate --help
docker-ai analyze --help
```

### Check Status

```bash
# View configuration
kubectl-ai config
kagent config
docker-ai config

# View recent operations
kubectl-ai audit
kagent history
docker-ai audit

# Check statistics
kubectl-ai stats --days 7
```

### Debug Issues

```bash
# Enable debug mode
export LOG_LEVEL=DEBUG

# Run with debug flag
kubectl-ai --debug execute "your command"
kagent --debug analyze
docker-ai --debug generate "your description"
```

## Summary

You now have three powerful AI tools:

1. **kubectl-ai**: Talk to Kubernetes in plain English
2. **kagent**: Autonomous cluster health monitoring
3. **docker-ai**: Instant Dockerfile generation

Start with simple commands and explore from there!

```bash
# Try these now:
kubectl-ai execute "list all pods"
kagent analyze
docker-ai generate "Python Flask app"
```

Happy coding! 🚀
