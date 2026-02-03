"""Quick validation script for recurring task implementation"""
import sys

def validate_implementation():
    """Validate all recurring task components exist and are syntactically correct"""

    print("Validating recurring task implementation...")
    print()

    # Check imports
    try:
        from app.services.recurring_service import (
            set_recurring_pattern,
            remove_recurring_pattern,
            generate_recurring_instances,
            backfill_missed_instances,
            get_recurring_tasks_due,
            get_task_instances
        )
        print("✓ recurring_service.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import recurring_service.py: {e}")
        return False

    try:
        from app.routes.recurring import router
        print("✓ recurring.py routes imported successfully")
    except Exception as e:
        print(f"✗ Failed to import recurring.py routes: {e}")
        return False

    try:
        from app.jobs.recurring_generator import generate_due_instances
        print("✓ recurring_generator.py imported successfully")
    except Exception as e:
        print(f"✗ Failed to import recurring_generator.py: {e}")
        return False

    # Check Task model has recurring fields
    try:
        from app.models.task import Task
        required_fields = [
            'recurring_pattern',
            'recurring_interval',
            'recurring_days',
            'recurring_end_date',
            'parent_task_id',
            'next_occurrence'
        ]

        task_fields = Task.__fields__.keys()
        for field in required_fields:
            if field in task_fields:
                print(f"✓ Task model has field: {field}")
            else:
                print(f"✗ Task model missing field: {field}")
                return False

    except Exception as e:
        print(f"✗ Failed to validate Task model: {e}")
        return False

    print()
    print("=" * 60)
    print("All validations passed! ✓")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)
