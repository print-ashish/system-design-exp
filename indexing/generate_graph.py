import psycopg2
from psycopg2 import extras
import time
import matplotlib.pyplot as plt

DB_CONFIG = "dbname=indexing_exp user=postgres password=postgres host=localhost port=5432"
# Searching for a user near the end to force a full table scan
READ_QUERY = "SELECT * FROM users WHERE email = 'user950000@gmail.com';"
TOTAL_ROWS = 1_000_000
WRITE_BATCH_SIZE = 100_000

def get_db_metrics():
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()

    # --- SETUP ---
    print(f"🧹 Resetting database for 1M row test...")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT, name TEXT);")
    conn.commit()

    # --- 1. WRITE WITHOUT INDEX ---
    print(f"🚀 Measuring Write speed (No Index, {WRITE_BATCH_SIZE} rows)...")
    data = [(f"write_test_{i}@test.com", "Name") for i in range(WRITE_BATCH_SIZE)]
    start = time.perf_counter()
    extras.execute_values(cur, "INSERT INTO users (email, name) VALUES %s", data)
    conn.commit()
    write_no_index = (time.perf_counter() - start) * 1000

    # --- 2. POPULATE 1M ROWS ---
    print(f"📦 Filling database to {TOTAL_ROWS} rows (this may take a few seconds)...")
    cur.execute("TRUNCATE users RESTART IDENTITY;") # Start fresh for the 1M
    for chunk in range(0, TOTAL_ROWS, 100000):
        chunk_data = [(f"user{i}@gmail.com", "Name") for i in range(chunk, chunk + 100000)]
        extras.execute_values(cur, "INSERT INTO users (email, name) VALUES %s", chunk_data)
        print(f"  ✅ {chunk + 100000} rows inserted...")
    conn.commit()

    # --- 3. READ WITHOUT INDEX ---
    print(f"🔍 Measuring Read speed (No Index - 1M rows)...")
    start = time.perf_counter()
    for _ in range(5): # 5 runs to get average
        cur.execute(READ_QUERY)
        cur.fetchall()
    read_no_index = ((time.perf_counter() - start) / 5) * 1000

    # --- 4. ADD INDEX ---
    print("⚡ Adding Index on 1M rows...")
    start_idx = time.perf_counter()
    cur.execute("CREATE INDEX idx_email ON users(email);")
    conn.commit()
    print(f"✅ Index created in {(time.perf_counter() - start_idx):.2f}s")

    # --- 5. READ WITH INDEX ---
    print("🔍 Measuring Read speed (With Index - 1M rows)...")
    start = time.perf_counter()
    for _ in range(20): # More runs because it's super fast
        cur.execute(READ_QUERY)
        cur.fetchall()
    read_with_index = ((time.perf_counter() - start) / 20) * 1000

    # --- 6. WRITE WITH INDEX ---
    print(f"🐢 Measuring Write speed (With Index, {WRITE_BATCH_SIZE} rows)...")
    start = time.perf_counter()
    extras.execute_values(cur, "INSERT INTO users (email, name) VALUES %s", data)
    conn.commit()
    write_with_index = (time.perf_counter() - start) * 1000

    cur.close()
    conn.close()

    return {
        "read": [read_no_index, read_with_index],
        "write": [write_no_index, write_with_index]
    }

def plot_results(metrics):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    plt.style.use('dark_background')
    
    labels = ['No Index', 'With Index']
    colors = ['#ff4b2b', '#00d2ff']

    # Read Plot
    ax1.bar(labels, metrics['read'], color=colors)
    ax1.set_title('Read Latency (1M Rows)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Average Time (ms)')
    for i, v in enumerate(metrics['read']):
        ax1.text(i, v + (v * 0.05), f"{v:.2f}ms", ha='center', fontweight='bold', color='white')

    # Write Plot
    ax2.bar(labels, metrics['write'], color=colors)
    ax2.set_title(f'Write Latency (Batch of {WRITE_BATCH_SIZE})', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Total Time (ms)')
    for i, v in enumerate(metrics['write']):
        ax2.text(i, v + (v * 0.05), f"{v:.2f}ms", ha='center', fontweight='bold', color='white')

    plt.suptitle('PostgreSQL Indexing: The Million Row Benchmark', fontsize=20, y=1.02)
    plt.figtext(0.5, -0.05, 
                f"Read Speedup: {metrics['read'][0]/metrics['read'][1]:.1f}x faster\n"
                f"Write Penalty: {((metrics['write'][1]-metrics['write'][0])/metrics['write'][0])*100:.1f}% slower", 
                ha="center", fontsize=12, bbox={"facecolor":"#333", "alpha":0.5, "pad":10})

    plt.tight_layout()
    plt.savefig('indexing_1M_benchmark.png', bbox_inches='tight')
    print("\n📊 Final Graph saved as 'indexing_1M_benchmark.png'")
    plt.show()

if __name__ == "__main__":
    results = get_db_metrics()
    plot_results(results)
