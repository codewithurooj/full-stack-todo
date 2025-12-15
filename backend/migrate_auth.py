"""
Create Better Auth tables in the database
"""
from sqlalchemy import create_engine, text
from app.config import settings

def create_auth_tables():
    print("Creating Better Auth tables...")

    engine = create_engine(settings.DATABASE_URL)

    with open("create_auth_tables.sql", "r") as f:
        sql_commands = f.read()

    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        for statement in sql_commands.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    print(f"Statement: {statement[:50]}...")
                    print(f"Error: {e}")
                    continue

    print("Done! Better Auth tables created.")
    print("\nYou can now:")
    print("1. Restart your frontend server")
    print("2. Go to http://localhost:3000/auth/signup")
    print("3. Create your account!")

if __name__ == "__main__":
    create_auth_tables()
