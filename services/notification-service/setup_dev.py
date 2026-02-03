#!/usr/bin/env python3
"""
Development setup script for notification service
Generates VAPID keys and sets up environment
"""
import os
from pathlib import Path


def generate_vapid_keys():
    """Generate VAPID keys for Web Push"""
    try:
        from pywebpush import generate_vapid_keys
        vapid_keys = generate_vapid_keys()
        return vapid_keys
    except ImportError:
        print("Error: pywebpush not installed. Run: pip install pywebpush")
        return None


def setup_env():
    """Create .env file from template"""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env setup")
            return

    if not env_example.exists():
        print("Error: .env.example not found")
        return

    # Read template
    with open(env_example) as f:
        content = f.read()

    # Generate VAPID keys
    print("\nGenerating VAPID keys for Web Push...")
    vapid_keys = generate_vapid_keys()

    if vapid_keys:
        # Extract keys from JSON string
        import json
        keys = json.loads(vapid_keys)
        public_key = keys['publicKey']
        private_key = keys['privateKey']

        print(f"✓ Generated VAPID keys")

        # Replace placeholders
        content = content.replace("your-vapid-public-key", public_key)
        content = content.replace("your-vapid-private-key", private_key)

    # Prompt for other values
    print("\nEnter configuration values (or press Enter to use defaults):")

    kafka_servers = input("Kafka bootstrap servers [localhost:9092]: ").strip()
    if kafka_servers:
        content = content.replace("localhost:9092", kafka_servers)

    database_url = input("Database URL [postgresql://user:password@localhost:5432/todo_db]: ").strip()
    if database_url:
        content = content.replace(
            "postgresql://user:password@localhost:5432/todo_db",
            database_url
        )

    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)

    print(f"\n✓ Created .env file")
    print("\nNext steps:")
    print("1. Review and adjust settings in .env")
    print("2. Run database migration: psql $DATABASE_URL -f migrations/001_create_tables.sql")
    print("3. Start service: python -m app.main")


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []

    try:
        import aiokafka
    except ImportError:
        missing.append("aiokafka")

    try:
        import pywebpush
    except ImportError:
        missing.append("pywebpush")

    try:
        import sqlmodel
    except ImportError:
        missing.append("sqlmodel")

    try:
        import pydantic_settings
    except ImportError:
        missing.append("pydantic-settings")

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        return False

    print("✓ All dependencies installed")
    return True


def main():
    """Main setup routine"""
    print("=" * 60)
    print("Notification Service - Development Setup")
    print("=" * 60)

    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_dependencies():
        return

    # Setup environment
    print("\n2. Setting up environment...")
    setup_env()

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
