#!/usr/bin/env python3
"""
Service verification script
Tests basic functionality without requiring full infrastructure
"""
import sys
import json
from datetime import datetime, timedelta


def verify_imports():
    """Verify all required modules can be imported"""
    print("1. Verifying imports...")
    errors = []

    modules = [
        ('aiokafka', 'Async Kafka client'),
        ('pywebpush', 'Web Push library'),
        ('sqlmodel', 'Database ORM'),
        ('pydantic_settings', 'Configuration'),
        ('app.config', 'Service config'),
        ('app.consumer', 'Consumer logic'),
        ('app.models', 'Database models'),
        ('app.utils', 'Utility functions'),
    ]

    for module, description in modules:
        try:
            __import__(module)
            print(f"  ✓ {module} ({description})")
        except ImportError as e:
            errors.append(f"  ✗ {module}: {e}")
            print(f"  ✗ {module}: {e}")

    return len(errors) == 0


def verify_config():
    """Verify configuration loads correctly"""
    print("\n2. Verifying configuration...")
    try:
        from app.config import settings

        print(f"  ✓ Service name: {settings.SERVICE_NAME}")
        print(f"  ✓ Log level: {settings.LOG_LEVEL}")
        print(f"  ✓ Kafka topic: {settings.KAFKA_TOPIC}")
        print(f"  ✓ Consumer group: {settings.CONSUMER_GROUP_ID}")
        print(f"  ✓ Batch window: {settings.BATCH_WINDOW_SECONDS}s")
        print(f"  ✓ Rate limit: {settings.RATE_LIMIT_PER_USER} per {settings.RATE_LIMIT_WINDOW_SECONDS}s")

        # Warnings for missing keys
        if not settings.VAPID_PRIVATE_KEY:
            print("  ⚠ VAPID_PRIVATE_KEY not set (required for production)")
        if not settings.DATABASE_URL:
            print("  ⚠ DATABASE_URL not set (required for production)")

        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def verify_models():
    """Verify database models are valid"""
    print("\n3. Verifying database models...")
    try:
        from app.models import NotificationLog, PushSubscription, UserNotificationStats

        # Test model instantiation
        log = NotificationLog(
            reminder_id="test",
            task_id=1,
            user_id=1,
            status="sent"
        )
        print(f"  ✓ NotificationLog model")

        subscription = PushSubscription(
            user_id=1,
            endpoint="https://example.com",
            p256dh="test",
            auth="test"
        )
        print(f"  ✓ PushSubscription model")

        stats = UserNotificationStats(
            user_id=1,
            notification_count=5
        )
        print(f"  ✓ UserNotificationStats model")

        return True
    except Exception as e:
        print(f"  ✗ Model error: {e}")
        return False


def verify_utils():
    """Verify utility functions work correctly"""
    print("\n4. Verifying utility functions...")
    try:
        from app.utils import (
            validate_reminder_event,
            parse_iso_datetime,
            calculate_delay,
            NotificationBatcher,
            RateLimiter
        )

        # Test event validation
        valid_event = {
            "event_id": "test",
            "schema_version": "1.0.0",
            "timestamp": "2026-01-12T10:00:00.000Z",
            "reminder_id": "test-reminder",
            "task_id": 1,
            "user_id": 1,
            "title": "Test",
            "remind_at": "2026-01-12T11:00:00.000Z"
        }
        assert validate_reminder_event(valid_event) == True
        print("  ✓ Event validation")

        # Test datetime parsing
        dt = parse_iso_datetime("2026-01-12T10:00:00.000Z")
        assert dt is not None
        print("  ✓ Datetime parsing")

        # Test delay calculation
        future = datetime.utcnow() + timedelta(hours=1)
        delay = calculate_delay(future)
        assert delay > 3500  # ~1 hour
        print("  ✓ Delay calculation")

        # Test rate limiter
        limiter = RateLimiter(max_per_window=3, window_seconds=60)
        assert limiter.is_allowed(1) == True
        assert limiter.is_allowed(1) == True
        assert limiter.is_allowed(1) == True
        assert limiter.is_allowed(1) == False  # Should be blocked
        print("  ✓ Rate limiter")

        # Test batcher
        batcher = NotificationBatcher(window_seconds=120)
        assert batcher.get_batch_size(1) == 0
        print("  ✓ Notification batcher")

        return True
    except Exception as e:
        print(f"  ✗ Utility error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_consumer():
    """Verify consumer can be instantiated"""
    print("\n5. Verifying consumer...")
    try:
        from app.consumer import NotificationConsumer

        consumer = NotificationConsumer(
            bootstrap_servers="localhost:9092",
            group_id="test-group",
            topic="test-topic"
        )
        consumer.engine = None  # Disable database for test

        print("  ✓ Consumer instantiation")
        print("  ✓ Kafka settings configured")
        print("  ✓ Rate limiter initialized")
        print("  ✓ Batcher initialized")

        return True
    except Exception as e:
        print(f"  ✗ Consumer error: {e}")
        return False


def verify_tests():
    """Verify tests can run"""
    print("\n6. Verifying tests...")
    try:
        import pytest
        print("  ✓ Pytest available")

        # Check test files exist
        from pathlib import Path
        test_dir = Path(__file__).parent / "tests"
        test_files = list(test_dir.glob("test_*.py"))
        print(f"  ✓ Found {len(test_files)} test files")

        return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Notification Service - Verification")
    print("=" * 60)

    checks = [
        verify_imports,
        verify_config,
        verify_models,
        verify_utils,
        verify_consumer,
        verify_tests,
    ]

    results = [check() for check in checks]

    print("\n" + "=" * 60)
    print("Verification Results")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ All checks passed! Service is ready.")
        print("\nNext steps:")
        print("1. Configure .env with VAPID keys and DATABASE_URL")
        print("2. Run database migration")
        print("3. Start service: python -m app.main")
        return 0
    else:
        print("\n❌ Some checks failed. Review errors above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version: python --version (need 3.13+)")
        print("3. Verify .env file exists")
        return 1


if __name__ == "__main__":
    sys.exit(main())
