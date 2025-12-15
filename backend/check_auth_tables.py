"""
Check if Better Auth tables exist in the database
"""
import asyncio
from sqlalchemy import text, create_engine, inspect
from app.config import settings

def check_tables():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Existing tables in database:")
    for table in tables:
        print(f"  - {table}")

    required_tables = ['user', 'session', 'account']
    missing_tables = [t for t in required_tables if t not in tables]

    if missing_tables:
        print(f"\n⚠️  Missing Better Auth tables: {missing_tables}")
        print("\nBetter Auth needs these tables to function properly.")
    else:
        print("\n✅ All required Better Auth tables exist!")

if __name__ == "__main__":
    check_tables()
