from db import get_engine
from sqlalchemy import text

print("1. Starting")

engine = get_engine()

print("2. Engine created")

try:
    print("3. Attempting connection")

    with engine.connect() as conn:
        print("4. Connected")

        result = conn.execute(text("SELECT DATABASE()"))
        print("5. Query executed")

        print(result.fetchone())

except Exception as e:
    print("ERROR:")
    print(type(e))
    print(e)

print("6. Finished")