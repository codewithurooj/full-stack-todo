# Configuration Guide

Comprehensive guide to configuring kubectl-ai, kagent, and docker-ai.

## Overview

All three tools share a common configuration structure:

```
~/.{tool-name}/
├── config.yaml      # Tool-specific settings
├── .env            # API keys and environment variables
├── logs/           # Application logs
└── audit/          # Audit logs
```

## Quick Setup

### 1. Set API Keys (Required)

All tools require an AI provider API key:

**Option A: Environment Variables (Recommended)**

```bash
# For OpenAI
export OPENAI_API_KEY='sk-your-key-here'
export OPENAI_MODEL='gpt-4o-mini'

# OR for Anthropic
export ANTHROPIC_API_KEY='your-key-here'
export ANTHROPIC_MODEL='claude-3-5-sonnet-20241022'
```

**Option B: Tool-Specific .env Files**

```bash
# kubectl-ai
echo "OPENAI_API_KEY=sk-your-key" >> ~/.kubectl-ai/.env

# kagent
echo "OPENAI_API_KEY=sk-your-key" >> ~/.kagent/.env

# docker-ai
echo "OPENAI_API_KEY=sk-your-key" >> ~/.docker-ai/.env
```

### 2. Generate Config Files (Optional)

```bash
# Generate config templates
kubectl-ai config --init
kagent config --init
docker-ai config --init
```

## Configuration Files

### kubectl-ai Configuration

**File**: `~/.kubectl-ai/config.yaml`

```yaml
# AI Provider Settings
ai_provider: openai              # 'openai' or 'anthropic'
openai_model: gpt-4o-mini       # OpenAI model to use
anthropic_model: claude-3-5-sonnet-20241022  # Anthropic model

# kubectl Settings
kubectl_path: kubectl            # Path to kubectl binary
default_namespace: default       # Default namespace
default_context: null           # Default kubectl context (null = current)

# Safety Settings
confirmation_required: true      # Require confirmation for destructive ops
dry_run_by_default: false       # Default to dry-run mode

# Logging Settings
log_level: INFO                 # DEBUG, INFO, WARNING, ERROR
audit_enabled: true             # Enable audit logging
audit_retention_days: 30        # Days to keep audit logs

# Session Settings
context_persistence: true       # Remember conversation context
max_context_messages: 10        # Max messages to remember

# Execution Settings
max_retries: 3                  # Retry attempts for failed operations
timeout_seconds: 300            # Command timeout (5 minutes)

# Parser Settings
use_rule_based_first: true      # Try rule-based parsing before AI
min_confidence: 0.7             # Minimum confidence for rule-based
```

**Example Configurations:**

**Production (Safe):**
```yaml
ai_provider: openai
confirmation_required: true
dry_run_by_default: false
log_level: INFO
audit_enabled: true
max_retries: 3
```

**Development (Fast):**
```yaml
ai_provider: openai
confirmation_required: false
dry_run_by_default: false
log_level: DEBUG
use_rule_based_first: true
min_confidence: 0.6
```

**Strict (Maximum Safety):**
```yaml
ai_provider: anthropic
confirmation_required: true
dry_run_by_default: true
log_level: DEBUG
audit_enabled: true
audit_retention_days: 90
max_retries: 1
```

### kagent Configuration

**File**: `~/.kagent/config.yaml`

```yaml
# AI Provider Settings
ai_provider: openai
openai_model: gpt-4o-mini
anthropic_model: claude-3-5-sonnet-20241022

# Scanning Settings
default_namespace: null          # null = all namespaces
excluded_namespaces:            # Namespaces to skip
  - kube-system
  - kube-public
scanners_enabled:               # Which scanners to run
  - health
  - security
  - resources
  - config
  - performance

# Severity Settings
severity_threshold: low         # Minimum severity to show (low/medium/high/critical)
max_findings_per_category: 100  # Limit findings per category

# Report Settings
default_output_format: text     # 'text', 'json', or 'markdown'
save_reports: true              # Auto-save reports
report_directory: ~/.kagent/reports
report_retention_days: 30

# Monitoring Settings
monitor_interval: 3600          # Continuous monitoring interval (seconds)
enable_notifications: false     # Future: Send notifications
notification_threshold: high    # Severity to trigger notification

# Logging Settings
log_level: INFO
audit_enabled: true
audit_retention_days: 30

# Performance Settings
max_parallel_scans: 5           # Parallel namespace scans
timeout_per_resource: 30        # Timeout per resource check (seconds)
```

**Example Configurations:**

**Production Monitoring:**
```yaml
ai_provider: openai
excluded_namespaces:
  - kube-system
  - kube-public
severity_threshold: medium
save_reports: true
monitor_interval: 3600
```

**Security Focused:**
```yaml
ai_provider: anthropic
scanners_enabled:
  - security
  - config
severity_threshold: low
save_reports: true
report_directory: /var/log/security-reports
```

**Quick Development Scans:**
```yaml
ai_provider: openai
default_namespace: development
severity_threshold: high
save_reports: false
max_findings_per_category: 20
```

### docker-ai Configuration

**File**: `~/.docker-ai/config.yaml`

```yaml
# AI Provider Settings
ai_provider: openai
openai_model: gpt-4o-mini
anthropic_model: claude-3-5-sonnet-20241022

# Generation Settings
base_image_variant: alpine      # 'alpine', 'slim', 'distroless', or 'full'
enable_multistage: true         # Use multi-stage builds
enable_security: true           # Apply security hardening
enable_optimization: true       # Optimize layer caching

# Security Settings
create_nonroot_user: true       # Add non-root USER directive
pin_base_image_versions: true   # Use specific tags, not :latest
scan_for_secrets: true          # Warn about hardcoded secrets

# Optimization Settings
optimize_package_managers: true # Add --no-cache flags
combine_run_commands: true      # Reduce layers
add_healthcheck: true          # Add HEALTHCHECK instruction

# Code Analysis Settings
auto_detect_language: true      # Analyze code for language/framework
confidence_threshold: 0.7       # Min confidence for auto-detection
supported_languages:            # Languages to detect
  - python
  - javascript
  - typescript
  - go
  - java
  - ruby
  - php
  - rust
  - csharp

# Compose Settings
compose_version: '3.8'          # docker-compose version
include_volumes: true           # Add volume definitions
include_networks: false         # Add network definitions
restart_policy: unless-stopped  # Container restart policy

# Logging Settings
log_level: INFO
audit_enabled: true
audit_retention_days: 30
```

**Example Configurations:**

**Production (Optimized & Secure):**
```yaml
ai_provider: openai
base_image_variant: alpine
enable_multistage: true
enable_security: true
enable_optimization: true
pin_base_image_versions: true
```

**Development (Fast Builds):**
```yaml
ai_provider: openai
base_image_variant: full
enable_multistage: false
enable_security: true
enable_optimization: false
```

**Maximum Security:**
```yaml
ai_provider: anthropic
base_image_variant: distroless
enable_multistage: true
enable_security: true
create_nonroot_user: true
pin_base_image_versions: true
scan_for_secrets: true
```

## Environment Variables

### Shared Environment Variables

All tools support these environment variables:

```bash
# AI Provider Settings
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Logging Settings
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
ENABLE_AUDIT_LOG=true           # Enable audit logging

# Performance Settings
AI_REQUEST_TIMEOUT=30           # AI API request timeout (seconds)
MAX_RETRIES=3                   # Retry attempts
```

### Tool-Specific Environment Variables

**kubectl-ai:**
```bash
KUBECTL_AI_CONFIG_PATH=~/.kubectl-ai/config.yaml
KUBECTL_AI_CONTEXT_DIR=~/.kubectl-ai/context
KUBECTL_PATH=/usr/local/bin/kubectl
KUBECTL_DEFAULT_NAMESPACE=default
```

**kagent:**
```bash
KAGENT_CONFIG_PATH=~/.kagent/config.yaml
KAGENT_REPORT_DIR=~/.kagent/reports
KAGENT_EXCLUDED_NAMESPACES=kube-system,kube-public
```

**docker-ai:**
```bash
DOCKER_AI_CONFIG_PATH=~/.docker-ai/config.yaml
DOCKER_AI_BASE_IMAGE_VARIANT=alpine
DOCKER_AI_MULTISTAGE=true
```

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages only

### Configure Logging

**In config.yaml:**
```yaml
log_level: DEBUG
```

**Via environment:**
```bash
export LOG_LEVEL=DEBUG
```

**At runtime:**
```bash
kubectl-ai --debug execute "list pods"
kagent --debug analyze
docker-ai --debug generate "Flask app"
```

### Log Locations

```
~/.kubectl-ai/logs/kubectl-ai.log
~/.kagent/logs/kagent.log
~/.docker-ai/logs/docker-ai.log
```

### Log Rotation

Logs automatically rotate:
- **Daily rotation**
- **Keep last 7 days**
- **Max size: 10MB per file**

## Audit Logging

### Enable Audit Logs

**In config.yaml:**
```yaml
audit_enabled: true
audit_retention_days: 30
```

### Audit Log Format

All audit logs use **JSONL** (JSON Lines) format:

```json
{"timestamp": "2024-12-31T10:30:00Z", "tool": "kubectl-ai", "operation": "kubectl_command", "command": "get pods", "namespace": "default", "success": true}
{"timestamp": "2024-12-31T10:31:00Z", "tool": "kagent", "operation": "cluster_analysis", "findings": 15, "severity_breakdown": {"critical": 2, "high": 5}}
{"timestamp": "2024-12-31T10:32:00Z", "tool": "docker-ai", "operation": "dockerfile_generation", "language": "python", "framework": "flask", "success": true}
```

### View Audit Logs

```bash
# Via CLI
kubectl-ai audit --limit 50
kagent history --limit 20
docker-ai audit --limit 20

# Direct file access
cat ~/.kubectl-ai/audit/audit-2024-12-31.jsonl
cat ~/.kagent/audit/audit-2024-12-31.jsonl
cat ~/.docker-ai/audit/audit-2024-12-31.jsonl
```

## Multi-Provider Configuration

### Using Multiple AI Providers

You can configure different providers for different tools:

**kubectl-ai (OpenAI):**
```yaml
# ~/.kubectl-ai/config.yaml
ai_provider: openai
```

**kagent (Anthropic):**
```yaml
# ~/.kagent/config.yaml
ai_provider: anthropic
```

**docker-ai (OpenAI):**
```yaml
# ~/.docker-ai/config.yaml
ai_provider: openai
```

### Switch Providers

**Via config file:**
Edit `~/.{tool-name}/config.yaml` and change `ai_provider`

**Via environment:**
```bash
export AI_PROVIDER=anthropic
kubectl-ai execute "list pods"
```

## Advanced Configuration

### Custom kubectl Path

```yaml
# ~/.kubectl-ai/config.yaml
kubectl_path: /custom/path/to/kubectl
```

### Custom Context Directory

```yaml
# ~/.kubectl-ai/config.yaml
context_directory: /custom/context/path
```

### Report Customization

```yaml
# ~/.kagent/config.yaml
report_directory: /var/log/cluster-reports
report_format_template: |
  # Cluster Analysis Report
  Date: {timestamp}
  Findings: {total_findings}

  {findings_detail}
```

### Dockerfile Templates

```yaml
# ~/.docker-ai/config.yaml
custom_templates:
  python_flask: |
    FROM python:3.13-alpine AS builder
    # Custom template here...
```

## Configuration Validation

### Validate Configuration

```bash
# Check configuration
kubectl-ai config
kagent config
docker-ai config
```

### Test Configuration

```bash
# Test with --dry-run
kubectl-ai execute "list pods" --dry-run
kagent analyze --dry-run
docker-ai generate "Flask app" --dry-run
```

## Troubleshooting Configuration

### "Configuration file not found"

```bash
# Generate default config
kubectl-ai config --init
kagent config --init
docker-ai config --init
```

### "Invalid API key"

```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check .env files
cat ~/.kubectl-ai/.env
cat ~/.kagent/.env
cat ~/.docker-ai/.env
```

### "Permission denied" for config directory

```bash
# Fix permissions
chmod 700 ~/.kubectl-ai
chmod 700 ~/.kagent
chmod 700 ~/.docker-ai

# Recreate directories
rm -rf ~/.kubectl-ai
kubectl-ai config --init
```

### Debug Configuration Loading

```bash
# Enable debug mode to see config loading
export LOG_LEVEL=DEBUG
kubectl-ai --debug config
```

## Configuration Best Practices

### 1. Security

- **Never commit API keys** to version control
- **Use environment variables** for sensitive data
- **Restrict config file permissions**: `chmod 600 ~/.*/config.yaml`
- **Rotate API keys** regularly
- **Enable audit logging** in production

### 2. Production

- **Enable confirmations** for kubectl-ai
- **Set appropriate severity thresholds** for kagent
- **Use multi-stage builds** for docker-ai
- **Keep audit logs** for compliance
- **Set reasonable retention periods**

### 3. Development

- **Lower confirmation requirements** for speed
- **Increase log verbosity** (DEBUG)
- **Reduce monitoring intervals** for kagent
- **Use faster base images** for docker-ai
- **Disable unnecessary features**

### 4. Performance

- **Use rule-based parsing first** (faster)
- **Set timeouts appropriately**
- **Limit parallel operations**
- **Configure log rotation**
- **Clean up old audit logs**

## Configuration Examples by Use Case

### Use Case 1: Local Development

```yaml
# All tools - fast iteration
ai_provider: openai
log_level: DEBUG
confirmation_required: false
audit_enabled: false
enable_optimization: false
```

### Use Case 2: Production Cluster Management

```yaml
# kubectl-ai & kagent - safety first
ai_provider: anthropic
log_level: INFO
confirmation_required: true
audit_enabled: true
audit_retention_days: 90
severity_threshold: medium
```

### Use Case 3: CI/CD Pipeline

```yaml
# docker-ai - optimized builds
ai_provider: openai
base_image_variant: alpine
enable_multistage: true
enable_security: true
enable_optimization: true
log_level: WARNING
```

### Use Case 4: Security Audit

```yaml
# kagent - security focus
ai_provider: anthropic
scanners_enabled:
  - security
  - config
severity_threshold: low
save_reports: true
report_retention_days: 365
```

## Summary

Key configuration files:
- `~/.kubectl-ai/config.yaml` - kubectl-ai settings
- `~/.kagent/config.yaml` - kagent settings
- `~/.docker-ai/config.yaml` - docker-ai settings
- `~/.{tool}/.env` - API keys and secrets

Essential settings:
- `ai_provider` - Choose OpenAI or Anthropic
- `log_level` - Control verbosity
- `audit_enabled` - Track operations
- Tool-specific safety and optimization settings

For more help:
```bash
kubectl-ai config --help
kagent config --help
docker-ai config --help
```
