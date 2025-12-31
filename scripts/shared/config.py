"""Shared configuration module for AI-powered DevOps tools.

Manages API keys, settings, and tool-specific configurations.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import yaml
from dotenv import load_dotenv


class Config:
    """Centralized configuration manager."""

    def __init__(self, tool_name: str):
        """Initialize configuration for a specific tool.

        Args:
            tool_name: Name of the tool (kubectl-ai, kagent, docker-ai)
        """
        self.tool_name = tool_name
        self.config_dir = Path.home() / f".{tool_name}"
        self.config_file = self.config_dir / "config.yaml"

        # Load environment variables
        load_dotenv()

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load or create config
        self.settings = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        else:
            # Create default config
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config

    def _get_default_config(self) -> Dict:
        """Get default configuration for the tool."""
        base_config = {
            'ai_provider': os.getenv('AI_PROVIDER', 'openai'),
            'log_level': 'INFO',
            'confirmation_required': True,
            'audit_enabled': True,
        }

        # Tool-specific defaults
        if self.tool_name == 'kubectl-ai':
            base_config.update({
                'kubectl_path': 'kubectl',
                'context_persistence': True,
                'max_retries': 3,
            })
        elif self.tool_name == 'kagent':
            base_config.update({
                'scan_interval': 3600,  # 1 hour
                'report_format': 'markdown',
                'history_retention_days': 30,
            })
        elif self.tool_name == 'docker-ai':
            base_config.update({
                'default_base_image': 'alpine',
                'enable_multistage': True,
                'security_hardening': True,
            })

        return base_config

    def _save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    def get(self, key: str, default: Optional[any] = None) -> any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: any) -> None:
        """Set a configuration value and persist it.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.settings[key] = value
        self._save_config(self.settings)

    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment."""
        return os.getenv('OPENAI_API_KEY')

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key from environment."""
        return os.getenv('ANTHROPIC_API_KEY')

    @property
    def ai_provider(self) -> str:
        """Get configured AI provider."""
        return self.get('ai_provider', 'openai')

    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        provider = self.ai_provider

        if provider == 'openai' and not self.openai_api_key:
            print("Error: OPENAI_API_KEY not set in environment")
            return False
        elif provider == 'anthropic' and not self.anthropic_api_key:
            print("Error: ANTHROPIC_API_KEY not set in environment")
            return False

        return True
