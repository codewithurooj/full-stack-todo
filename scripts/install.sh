#!/bin/bash
# Installation script for AI-powered DevOps tools
# Sets up kubectl-ai, kagent, and docker-ai

set -e

echo "=== AI-Powered DevOps Tools Installer ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.13"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.13+ is required (found ${PYTHON_VERSION})${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} detected${NC}"

# Check if kubectl is installed (for kubectl-ai and kagent)
echo "Checking kubectl installation..."
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}✓ kubectl found${NC}"
else
    echo -e "${YELLOW}⚠ kubectl not found (optional for docker-ai only)${NC}"
fi

# Check if docker is installed (for docker-ai)
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker found${NC}"
else
    echo -e "${YELLOW}⚠ Docker not found (optional for kubectl-ai and kagent)${NC}"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create config directories
echo ""
echo "Creating configuration directories..."
mkdir -p ~/.kubectl-ai/logs
mkdir -p ~/.kagent/logs ~/.kagent/reports
mkdir -p ~/.docker-ai/logs ~/.docker-ai/templates
echo -e "${GREEN}✓ Configuration directories created${NC}"

# Create CLI entry points
echo ""
echo "Creating CLI entry points..."

# kubectl-ai
cat > venv/bin/kubectl-ai <<'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add scripts directory to Python path
scripts_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from kubectl-ai.cli import main

if __name__ == '__main__':
    main()
EOF
chmod +x venv/bin/kubectl-ai

# kagent
cat > venv/bin/kagent <<'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add scripts directory to Python path
scripts_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from kagent.cli import main

if __name__ == '__main__':
    main()
EOF
chmod +x venv/bin/kagent

# docker-ai
cat > venv/bin/docker-ai <<'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add scripts directory to Python path
scripts_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from docker-ai.cli import main

if __name__ == '__main__':
    main()
EOF
chmod +x venv/bin/docker-ai

echo -e "${GREEN}✓ CLI entry points created${NC}"

# Check for API keys
echo ""
echo "Checking for API keys..."
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠ No AI provider API keys found${NC}"
    echo "Please set one of the following environment variables:"
    echo "  - OPENAI_API_KEY for OpenAI"
    echo "  - ANTHROPIC_API_KEY for Anthropic Claude"
    echo ""
    echo "Add to your ~/.bashrc or ~/.zshrc:"
    echo "  export OPENAI_API_KEY='your-key-here'"
else
    if [ -n "$OPENAI_API_KEY" ]; then
        echo -e "${GREEN}✓ OPENAI_API_KEY found${NC}"
    fi
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo -e "${GREEN}✓ ANTHROPIC_API_KEY found${NC}"
    fi
fi

# Installation complete
echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "Available commands:"
echo "  kubectl-ai  - Natural language Kubernetes operations"
echo "  kagent      - Cluster health analysis and recommendations"
echo "  docker-ai   - AI-powered Dockerfile generation"
echo ""
echo "Get started:"
echo "  source venv/bin/activate  # Activate virtual environment"
echo "  kubectl-ai --help         # View kubectl-ai help"
echo "  kagent --help             # View kagent help"
echo "  docker-ai --help          # View docker-ai help"
echo ""
echo "Next steps:"
echo "  1. Set up your AI provider API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
echo "  2. Configure kubectl context for kubectl-ai and kagent"
echo "  3. Run 'kubectl-ai \"list all pods\"' to test"
echo ""
