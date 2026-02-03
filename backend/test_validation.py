"""
Test validation utilities
Run: python test_validation.py
"""

import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.utils.validation import validate_priority, validate_tags, validate_date_range
from fastapi import HTTPException


def test_priority_validation():
    """Test priority validation"""
    print("\n=== Testing Priority Validation ===")

    # Valid priorities
    for priority in ["high", "medium", "low"]:
        try:
            validate_priority(priority)
            print(f"✓ '{priority}' is valid")
        except HTTPException as e:
            print(f"✗ '{priority}' failed: {e.detail}")

    # Invalid priorities
    for priority in ["HIGH", "urgent", "normal", ""]:
        try:
            validate_priority(priority)
            print(f"✗ '{priority}' should have failed but didn't")
        except HTTPException as e:
            print(f"✓ '{priority}' correctly rejected: {e.detail}")


def test_tag_validation():
    """Test tag validation"""
    print("\n=== Testing Tag Validation ===")

    # Valid tags
    valid_tags = [
        ["work", "urgent"],
        ["project-123", "frontend_dev"],
        ["a" * 50],  # Max length
    ]

    for tags in valid_tags:
        try:
            validate_tags(tags)
            print(f"✓ {tags} is valid")
        except HTTPException as e:
            print(f"✗ {tags} failed: {e.detail}")

    # Invalid tags
    invalid_tags = [
        (["tag with spaces"], "spaces not allowed"),
        (["tag@special"], "special characters not allowed"),
        (["a" * 51], "exceeds max length"),
        (["tag"] * 51, "exceeds max tags"),
        ([""], "empty tag"),
    ]

    for tags, reason in invalid_tags:
        try:
            validate_tags(tags)
            print(f"✗ {tags} should have failed ({reason}) but didn't")
        except HTTPException as e:
            print(f"✓ {tags} correctly rejected: {reason}")


def test_date_range_validation():
    """Test date range validation"""
    print("\n=== Testing Date Range Validation ===")

    # Valid date ranges
    valid_ranges = [
        ("2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z"),
        ("2024-01-01T00:00:00Z", None),
        (None, "2024-12-31T23:59:59Z"),
        (None, None),
    ]

    for date_from, date_to in valid_ranges:
        try:
            validate_date_range(date_from, date_to)
            print(f"✓ Range {date_from} to {date_to} is valid")
        except HTTPException as e:
            print(f"✗ Range {date_from} to {date_to} failed: {e.detail}")

    # Invalid date ranges
    invalid_ranges = [
        ("2024-12-31", "2024-01-01", "invalid order"),
        ("invalid-date", None, "invalid format"),
        (None, "not-a-date", "invalid format"),
        ("2024-13-01T00:00:00Z", None, "invalid month"),
    ]

    for date_from, date_to, reason in invalid_ranges:
        try:
            validate_date_range(date_from, date_to)
            print(f"✗ Range {date_from} to {date_to} should have failed ({reason})")
        except HTTPException as e:
            print(f"✓ Range correctly rejected: {reason}")


def test_edge_cases():
    """Test edge cases"""
    print("\n=== Testing Edge Cases ===")

    # Tag with exactly 50 characters
    tag_50 = "a" * 50
    try:
        validate_tags([tag_50])
        print(f"✓ Tag with exactly 50 characters accepted")
    except HTTPException as e:
        print(f"✗ 50-character tag failed: {e.detail}")

    # Tag with 51 characters
    tag_51 = "a" * 51
    try:
        validate_tags([tag_51])
        print(f"✗ Tag with 51 characters should have been rejected")
    except HTTPException as e:
        print(f"✓ Tag with 51 characters correctly rejected")

    # Exactly 50 tags
    tags_50 = [f"tag{i}" for i in range(50)]
    try:
        validate_tags(tags_50)
        print(f"✓ Exactly 50 tags accepted")
    except HTTPException as e:
        print(f"✗ 50 tags failed: {e.detail}")

    # 51 tags
    tags_51 = [f"tag{i}" for i in range(51)]
    try:
        validate_tags(tags_51)
        print(f"✗ 51 tags should have been rejected")
    except HTTPException as e:
        print(f"✓ 51 tags correctly rejected")


if __name__ == "__main__":
    print("=" * 60)
    print("VALIDATION UTILITIES TEST SUITE")
    print("=" * 60)

    test_priority_validation()
    test_tag_validation()
    test_date_range_validation()
    test_edge_cases()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
