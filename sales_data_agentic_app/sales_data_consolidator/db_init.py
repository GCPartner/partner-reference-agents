import sys
import os
import sqlalchemy

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from tools import get_connection_pool
else:
    from .tools import get_connection_pool

def init_db():
    print("Connecting to database and initializing daily_sales table...")
    try:
        pool = get_connection_pool()
        query = sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS daily_sales (
                sales_date DATE,
                location VARCHAR(255),
                product_line VARCHAR(255),
                sales_amount NUMERIC,
                PRIMARY KEY (sales_date, location, product_line)
            );
        """)
        with pool.connect() as conn:
            print("Executing CREATE TABLE IF NOT EXISTS daily_sales...")
            conn.execute(query)
            conn.commit()
        print("daily_sales table initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        print("Please check that DB_CONNECTION_NAME, DB_USER, DB_PASSWORD, and DB_NAME are correctly configured.")

if __name__ == "__main__":
    init_db()
