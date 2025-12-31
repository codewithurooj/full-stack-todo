"""Environment configuration loading and validation.

Manages configuration files in user home directories and environment variables.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv
from rich.console import Console

console = Console()


class EnvConfig:
    """Environment configuration manager."""

    def __init__(self, tool_name: str):
        """Initialize environment configuration.

        Args:
            tool_name: Name of the tool (kubectl-ai, kagent, docker-ai)
        """
        self.tool_name = tool_name
        self.config_dir = Path.home() / f".{tool_name}"
        self.config_file = self.config_dir / "config.yaml"
        self.env_file = self.config_dir / ".env"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load environment variables from multiple sources
        self._load_env_vars()

    def _load_env_vars(self) -> None:
        """Load environment variables from all sources."""
        # 1. Load from tool-specific .env file
        if self.env_file.exists():
            load_dotenv(self.env_file)

        # 2. Load from project root .env file
        project_root = Path.cwd()
        project_env = project_root / ".env"
        if project_env.exists():
            load_dotenv(project_env)

        # 3. System environment variables are already loaded

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_file.exists():
            return self._create_default_config()

        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f) or {}

        return config

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration file.

        Returns:
            Default configuration dictionary
        """
        default_config = {
            'version': '1.0',
            'ai_provider': os.getenv('AI_PROVIDER', 'openai'),
            'log_level': 'INFO',
            'confirmation_required': True,
            'audit_enabled': True,
        }

        # Tool-specific defaults
        if self.tool_name == 'kubectl-ai':
            default_config.update({
                'kubectl_path': 'kubectl',
                'context_persistence': True,
                'max_retries': 3,
                'timeout': 30,
            })
        elif self.tool_name == 'kagent':
            default_config.update({
                'scan_interval': 3600,
                'report_format': 'markdown',
                'history_retention_days': 30,
                'auto_analyze': False,
            })
        elif self.tool_name == 'docker-ai':
            default_config.update({
                'default_base_image': 'alpine',
                'enable_multistage': True,
                'security_hardening': True,
                'optimize_size': True,
            })

        # Save default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.

        Args:
            config: Configuration dictionary to save
        """
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def require_env(self, key: str) -> str:
        """Get required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable {key} is not set. "
                f"Set it in {self.env_file} or system environment."
            )
        return value

    def validate_api_keys(self) -> bool:
        """Validate AI provider API keys.

        Returns:
            True if valid API key is configured
        """
        config = self.get_config()
        provider = config.get('ai_provider', 'openai')

        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                console.print("[red]Error: OPENAI_API_KEY not set[/red]")
                console.print(f"Set it in {self.env_file} or system environment:")
                console.print("  export OPENAI_API_KEY='your-key-here'")
                return False

        elif provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                console.print("[red]Error: ANTHROPIC_API_KEY not set[/red]")
                console.print(f"Set it in {self.env_file} or system environment:")
                console.print("  export ANTHROPIC_API_KEY='your-key-here'")
                return False

        return True

    def create_env_template(self) -> None:
        """Create a template .env file with placeholders."""
        if self.env_file.exists():
            console.print(f"[yellow].env file already exists at {self.env_file}[/yellow]")
            return

        template_content = """# AI Provider Configuration
# Choose: openai or anthropic
AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Logging
LOG_LEVEL=INFO

# Feature Flags
CONFIRMATION_REQUIRED=true
AUDIT_ENABLED=true
"""

        with open(self.env_file, 'w') as f:
            f.write(template_content)

        console.print(f"[green]Created .env template at {self.env_file}[/green]")
        console.print("Please edit it with your API keys.")

    def display_config(self) -> None:
        """Display current configuration."""
        config = self.get_config()

        console.print(f"\n[bold]Configuration for {self.tool_name}:[/bold]\n")
        console.print(f"Config file: {self.config_file}")
        console.print(f"Env file: {self.env_file}\n")

        for key, value in config.items():
            # Mask sensitive values
            if 'key' in key.lower() or 'secret' in key.lower():
                value = '***'
            console.print(f"  {key}: {value}")

        console.print()

        # Check API keys
        provider = config.get('ai_provider', 'openai')
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            status = '[green]✓ Set[/green]' if api_key else '[red]✗ Not set[/red]'
            console.print(f"OPENAI_API_KEY: {status}")

        elif provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            status = '[green]✓ Set[/green]' if api_key else '[red]✗ Not set[/red]'
            console.print(f"ANTHROPIC_API_KEY: {status}")

        console.print()


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Configuration dictionary
    """
    env_config = EnvConfig(tool_name)
    return env_config.get_config()


def validate_tool_env(tool_name: str) -> bool:
    """Validate environment configuration for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        True if configuration is valid
    """
    env_config = EnvConfig(tool_name)
    return env_config.validate_api_keys()
