import psycopg2
from psycopg2 import extras
import time

DB_CONFIG = "dbname=indexing_exp user=postgres password=postgres host=localhost port=5432"
BATCH_SIZE = 50_000 

def benchmark_batch_inserts(cur, count=BATCH_SIZE):
    # Prepare all data in memory first
    data = [(f"user{i}@penalty.com", "Name") for i in range(count)]
    
    start = time.perf_counter()
    # This sends 50,000 rows in ONE single network trip
    extras.execute_values(cur, "INSERT INTO users (email, name) VALUES %s", data)
    return (time.perf_counter() - start) * 1000

def run():
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()

    print(f"🧹 Resetting table for BATCH write test ({BATCH_SIZE} rows)...")
    cur.execute("DROP TABLE IF EXISTS users;")
    cur.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT, name TEXT);")
    conn.commit()

    # 1. WITHOUT INDEX
    print(f"🚀 Batch Inserting WITHOUT index...")
    time_no_index = benchmark_batch_inserts(cur)
    conn.commit()
    print(f"⏱️  Time: {time_no_index:.2f} ms")

    # Clear table for a fair second test
    cur.execute("TRUNCATE users RESTART IDENTITY;")
    conn.commit()

    # 2. WITH INDEX
    print("\n⚡ Adding index...")
    cur.execute("CREATE INDEX idx_email ON users(email);")
    conn.commit()

    print(f"🐢 Batch Inserting WITH index...")
    time_with_index = benchmark_batch_inserts(cur)
    conn.commit()
    print(f"⏱️  Time: {time_with_index:.2f} ms")

    # 3. Results
    penalty = ((time_with_index - time_no_index) / time_no_index) * 100
    print(f"\n📊 Batch Write Penalty: {penalty:.2f}% Slower")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run()
