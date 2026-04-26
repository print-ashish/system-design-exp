import psycopg2
import time

DB_CONFIG = "dbname=indexing_exp user=postgres password=postgres host=localhost port=5432"
QUERY = "SELECT * FROM users WHERE email = 'user150000@gmail.com';"

def run():
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()

    # 1. Create Index
    print("⚡ Creating index on email column...")
    start_idx = time.perf_counter()
    cur.execute("CREATE INDEX idx_email ON users(email);")
    conn.commit()
    print(f"✅ Index created in {(time.perf_counter() - start_idx)*1000:.2f} ms")

    # 2. Show Query Plan
    print("\n🔍 --- QUERY PLAN (WITH INDEX) ---")
    cur.execute(f"EXPLAIN ANALYZE {QUERY}")
    for line in cur.fetchall(): print(line[0])

    # 3. Benchmark
    print("\n⏱️  Running benchmark (50 runs)...")
    latencies = []
    for _ in range(50):
        start = time.perf_counter()
        cur.execute(QUERY)
        cur.fetchall()
        latencies.append((time.perf_counter() - start) * 1000)

    avg = sum(latencies) / len(latencies)
    print(f"\n📊 RESULT: Avg Latency = {avg:.4f} ms")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    run()
