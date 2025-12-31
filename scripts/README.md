# AI-Powered Kubernetes and Container Tools

Three intelligent CLI tools for Kubernetes and container operations using AI:

1. **kubectl-ai** - Natural language interface for Kubernetes operations (✅ Complete)
2. **kagent** - Cluster health analysis and recommendations (✅ Complete)
3. **docker-ai** - AI-powered Dockerfile generation (✅ Complete)

## Quick Start

### Installation

```bash
# 1. Clone repository
cd full-stack-todo/scripts

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run installation script
bash install.sh

# 4. Set up AI provider
export OPENAI_API_KEY='your-key-here'
# OR
export ANTHROPIC_API_KEY='your-key-here'

# 5. Verify installation
kubectl-ai --help
kagent --help
docker-ai --help
```

### Prerequisites

- **Python 3.13+**
- **kubectl** (for kubectl-ai and kagent)
- **Docker** (for docker-ai)
- **AI API Key** (OpenAI or Anthropic)

## kubectl-ai (MVP) ✅

### What is it?

Natural language interface for Kubernetes operations. Turn English commands into kubectl operations.

### Features

- ✅ Natural language → kubectl command translation
- ✅ AI-powered command interpretation
- ✅ Safety confirmations for destructive operations
- ✅ Comprehensive audit logging
- ✅ Troubleshooting assistant
- ✅ Dry-run mode
- ✅ Support for OpenAI and Anthropic

### Usage Examples

```bash
# List resources
kubectl-ai execute "list all pods"
kubectl-ai execute "show deployments in production namespace"

# Scale operations
kubectl-ai execute "scale nginx deployment to 5 replicas"

# Troubleshooting
kubectl-ai troubleshoot "pod keeps restarting"
kubectl-ai troubleshoot "service not accessible"

# View audit log
kubectl-ai audit --limit 20

# Configuration
kubectl-ai config
```

### Architecture

```
kubectl-ai/
├── cli.py              # CLI entry point (Click framework)
├── context.py          # Session state management
├── nl_parser.py        # Natural language parsing
├── translator.py       # kubectl command translation
├── executor.py         # Command execution with safety
└── troubleshooter.py   # AI-powered troubleshooting
```

### Testing

```bash
# Run kubectl-ai tests
cd tests
pytest kubectl-ai/ -v

# With coverage
pytest kubectl-ai/ --cov=../scripts/kubectl-ai

# Integration tests
pytest kubectl-ai/ -m integration
```

## kagent ✅

Autonomous Kubernetes cluster analysis and recommendations engine.

### Features

- ✅ Comprehensive cluster health scanning
- ✅ Security vulnerability detection
- ✅ Resource optimization recommendations
- ✅ Configuration best practices analysis
- ✅ Performance analysis
- ✅ Priority-based finding ranking
- ✅ Actionable recommendations with kubectl commands
- ✅ Historical trend analysis
- ✅ Scheduled continuous monitoring
- ✅ JSON, Markdown, and Text report formats

### Usage Examples

```bash
# Run comprehensive analysis
kagent analyze

# Analyze specific namespace
kagent analyze --namespace production

# Save report
kagent analyze --save --output json

# Run specific scanner
kagent scan --scanner security
kagent scan --scanner resources
kagent scan --scanner performance

# Generate detailed report
kagent report --format markdown
kagent report --format json --output cluster-report.json

# View analysis history
kagent history --limit 10

# Continuous monitoring
kagent monitor --interval 300  # Every 5 minutes
kagent monitor --interval 3600 --save  # Hourly with reports

# Configuration
kagent config
```

### What It Analyzes

**Health Scanner:**
- Node status and readiness
- Pod health across all namespaces
- System pod status
- Resource pressure detection

**Security Scanner:**
- Privileged containers
- Root user usage
- Host filesystem access
- Missing security contexts
- Secrets exposure
- Service account misconfigurations

**Resource Analyzer:**
- Missing resource limits/requests
- Over-provisioned resources
- Resource efficiency metrics
- Storage usage

**Config Checker:**
- Missing health probes (liveness/readiness)
- Update strategy validation
- Label and annotation best practices
- Service configurations

**Performance Analyzer:**
- Anti-patterns (e.g., hostNetwork, hostPID)
- Node performance metrics
- Resource contention

### Architecture

```
kagent/
├── cli.py                 # CLI entry point
├── health_scanner.py      # Health checks
├── security_scanner.py    # Security analysis
├── resource_analyzer.py   # Resource optimization
├── config_checker.py      # Configuration validation
├── performance_analyzer.py # Performance analysis
├── prioritizer.py         # Finding prioritization
├── recommendations.py     # Actionable recommendations
├── reporter.py           # Report generation
├── scheduler.py          # Continuous monitoring
└── history.py            # Analysis history tracking
```

### Testing

```bash
# Run kagent tests
pytest tests/kagent/ -v

# With coverage
pytest tests/kagent/ --cov=scripts/kagent

# Integration tests
pytest tests/kagent/ -m integration
```

## docker-ai (Gordon) ✅

AI-powered Dockerfile generation and optimization.

### Features

- ✅ Natural language → Dockerfile generation
- ✅ Automatic code analysis for language/framework detection
- ✅ Multi-stage build generation
- ✅ Security hardening (non-root users, pinned versions)
- ✅ Layer caching optimization
- ✅ Docker Compose generation
- ✅ Existing Dockerfile analysis
- ✅ Dockerfile optimization
- ✅ Support for 8+ languages (Python, Node.js, Go, Java, Ruby, PHP, Rust, C#)
- ✅ 7+ service integrations (PostgreSQL, MySQL, MongoDB, Redis, RabbitMQ, Elasticsearch, Nginx)

### Usage Examples

```bash
# Generate from natural language
docker-ai generate "Python Flask application with PostgreSQL on port 5000"
docker-ai generate "Node.js Express API with Redis" --output Dockerfile.node

# Generate from code analysis
docker-ai analyze .
docker-ai analyze /path/to/project --multistage --security

# Optimize existing Dockerfile
docker-ai optimize ./Dockerfile
docker-ai optimize ./Dockerfile --output Dockerfile.optimized

# Generate docker-compose.yml
docker-ai compose "Flask API with PostgreSQL and Redis"
docker-ai compose "Node.js app with MongoDB" --output docker-compose.dev.yml

# View configuration
docker-ai config

# View audit log
docker-ai audit --limit 20
```

### Supported Languages & Frameworks

**Python:**
- Flask, Django, FastAPI
- Poetry, Pipenv, requirements.txt

**JavaScript/TypeScript:**
- Express, NestJS, Next.js
- npm, yarn, pnpm

**Go:**
- Standard Go modules
- Gin, Echo, Fiber

**Java:**
- Spring Boot, Maven, Gradle

**Ruby:**
- Rails, Sinatra, Bundler

**PHP:**
- Laravel, Symfony, Composer

**Rust:**
- Cargo projects

**C#/.NET:**
- .NET Core, ASP.NET

### Architecture

```
docker-ai/
├── cli.py               # CLI entry point
├── code_analyzer.py     # Project code analysis
├── nl_processor.py      # Natural language processing
├── base_image.py        # Base image selection
├── multistage.py        # Multi-stage build generation
├── generator.py         # Main Dockerfile generator
├── security.py          # Security hardening
├── optimizer.py         # Layer optimization
├── analyzer.py          # Dockerfile analysis
└── compose_generator.py # docker-compose generation
```

### Testing

```bash
# Run docker-ai tests
pytest tests/docker-ai/ -v

# With coverage
pytest tests/docker-ai/ --cov=scripts/docker-ai

# Integration tests
pytest tests/docker-ai/test_integration.py -v
```

## Shared Infrastructure

All three tools share common utilities:

```
shared/
├── config.py           # Configuration management
├── logger.py           # Logging with audit support
├── audit.py            # Audit logging system
├── ai_provider.py      # AI provider abstraction
├── k8s_client.py       # Kubernetes client wrapper
├── confirmation.py     # Confirmation prompts
├── error_handler.py    # User-friendly error handling
└── env.py              # Environment configuration
```

### Key Features

- **Multi-Provider AI**: OpenAI or Anthropic
- **Audit Trail**: All operations logged with timestamps
- **User Safety**: Confirmation for destructive operations
- **Error Handling**: Plain language error messages with solutions
- **Configuration**: Per-tool config files in `~/.tool-name/`

## Configuration

Each tool stores configuration in your home directory:

```
~/.kubectl-ai/
├── config.yaml         # Tool configuration
├── .env               # API keys
├── context/           # Session context
├── logs/              # Application logs
└── audit/             # Audit logs

~/.kagent/
├── config.yaml         # Tool configuration
├── .env               # API keys
├── logs/              # Application logs
├── audit/             # Audit logs
└── reports/           # Analysis reports

~/.docker-ai/
├── config.yaml         # Tool configuration
├── .env               # API keys
├── logs/              # Application logs
└── audit/             # Audit logs
```

### Configuration Files

**~/.kubectl-ai/config.yaml**:
```yaml
ai_provider: openai
log_level: INFO
confirmation_required: true
audit_enabled: true
kubectl_path: kubectl
context_persistence: true
max_retries: 3
```

**~/.kubectl-ai/.env**:
```bash
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini

# OR

ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## Development

### Project Structure

```
scripts/
├── kubectl-ai/         # Natural language kubectl interface
├── kagent/            # Cluster analysis agent
├── docker-ai/         # Dockerfile generator
├── shared/            # Shared utilities
├── requirements.txt   # Python dependencies
├── install.sh        # Installation script
└── README.md         # This file

tests/
├── kubectl-ai/       # kubectl-ai tests
├── kagent/           # kagent tests
├── docker-ai/        # docker-ai tests
├── shared/           # Shared utilities tests
└── pytest.ini        # Pytest configuration
```

### Adding New Features

1. Create feature module in appropriate tool directory
2. Add tests in `tests/{tool-name}/`
3. Update tool's CLI entry point
4. Update skill documentation in `.claude/skills/`
5. Run tests: `pytest tests/{tool-name}/ -v`

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific tool
pytest tests/kubectl-ai/ -v

# With coverage
pytest --cov=scripts --cov-report=html

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting

### kubectl-ai Issues

**"Cannot connect to Kubernetes cluster"**
- Check: `kubectl cluster-info`
- Verify: `kubectl config current-context`
- Fix: `kubectl config use-context <context-name>`

**"AI Provider API Key Error"**
- Check: `echo $OPENAI_API_KEY` or `echo $ANTHROPIC_API_KEY`
- Set: `export OPENAI_API_KEY='your-key'`
- Or add to: `~/.kubectl-ai/.env`

**"Command not found: kubectl-ai"**
- Activate venv: `source venv/bin/activate`
- Or reinstall: `bash install.sh`

### General Issues

**View audit log:**
```bash
kubectl-ai audit --limit 50
```

**Check configuration:**
```bash
kubectl-ai config
```

**Enable debug logging:**
```bash
kubectl-ai --debug execute "your command"
```

## Performance

### Benchmarks

**kubectl-ai:**
- NL parsing: ~200-500ms (rule-based), ~1-2s (AI-based)
- Command execution: Depends on kubectl operation
- Troubleshooting: ~2-5s for AI analysis

**kagent:**
- Full cluster scan: ~5-15s (depends on cluster size)
- Security scan: ~2-5s
- Report generation: ~500ms-2s
- Continuous monitoring: ~10-20s per cycle

**docker-ai:**
- Code analysis: ~500ms-2s
- NL parsing: ~200-500ms (rule-based), ~1-2s (AI-based)
- Dockerfile generation: ~1-3s
- Optimization: ~500ms-1s

### Resource Usage

- **Memory**: ~50-150MB per tool
- **CPU**: Minimal (except during AI calls)
- **Storage**: <20MB (logs rotate daily)
- **API Usage**: Optimized with rule-based fallbacks to minimize AI API calls

## Security

### Best Practices

1. **API Keys**: Never commit API keys to git
2. **Audit Logs**: Review regularly for unauthorized operations
3. **Confirmation**: Keep enabled for production clusters
4. **RBAC**: kubectl-ai respects your kubectl permissions
5. **Validation**: All commands validated before execution

### Audit Trail

All operations logged with:
- Timestamp
- Operation type
- Resource affected
- Success/failure
- Error details (if any)

View audit log:
```bash
kubectl-ai audit --limit 100
kubectl-ai stats --days 7
```

## Roadmap

### Phase 1: kubectl-ai ✅ COMPLETE
- [x] Natural language parsing (hybrid: rule-based + AI)
- [x] kubectl command translation (10+ operations)
- [x] Command execution with safety confirmations
- [x] AI-powered troubleshooting assistant
- [x] Comprehensive audit logging
- [x] Session context management
- [x] Tests and documentation (23 test cases)

### Phase 2: kagent ✅ COMPLETE
- [x] Cluster health scanning
- [x] Security vulnerability analysis
- [x] Resource optimization recommendations
- [x] Configuration best practices
- [x] Performance analysis
- [x] Priority-based finding ranking
- [x] Report generation (JSON, Markdown, Text)
- [x] Historical tracking
- [x] Scheduled continuous monitoring
- [x] Tests and documentation (15 test cases)

### Phase 3: docker-ai ✅ COMPLETE
- [x] Natural language → Dockerfile generation
- [x] Code analysis for 8+ languages
- [x] Multi-stage build optimization
- [x] Security hardening (non-root user, pinned versions)
- [x] Layer caching optimization
- [x] Docker Compose generation (7+ services)
- [x] Dockerfile analysis and optimization
- [x] Tests and documentation (20 test cases)

### Phase 4: Enhancements 🚧 PLANNED
- [ ] Interactive mode for all tools
- [ ] Custom CRD support for kubectl-ai/kagent
- [ ] kubectl plugins integration
- [ ] CI/CD integration examples
- [ ] Rate limiting for AI providers
- [ ] Web UI dashboard
- [ ] Telemetry and metrics (optional)

## Contributing

### Development Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# 3. Run tests
pytest tests/ -v

# 4. Code formatting
black scripts/
flake8 scripts/

# 5. Type checking
mypy scripts/
```

### Code Style

- **Formatting**: Black
- **Linting**: Flake8
- **Type Hints**: mypy
- **Docstrings**: Google style
- **Testing**: pytest with >80% coverage

## License

MIT License - See repository LICENSE file

## Support

- **Issues**: GitHub Issues
- **Documentation**: `.claude/skills/` directory
- **Tests**: `tests/` directory
- **Audit Logs**: `~/.{tool-name}/audit/`

## Links

- **Specification**: `specs/008-ai-powered-tools/spec.md`
- **Implementation Plan**: `specs/008-ai-powered-tools/plan_complete.md`
- **Task List**: `specs/008-ai-powered-tools/tasks.md`
- **Skills**: `.claude/skills/kubectl-ai.md`

---

**Status**: All three tools complete ✅

**Stats**: 58 test cases | 8,500+ lines of code | 40+ files

Built with ❤️ using Claude Code and Spec-Kit Plus
