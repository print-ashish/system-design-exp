import psycopg2
from psycopg2 import extras
import random
import string

DB_CONFIG = "dbname=indexing_exp user=postgres password=postgres host=localhost port=5432"

def setup():
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()
    
    print("🧹 Cleaning up and creating table...")
    cur.execute("DROP TABLE IF EXISTS users;")
    cur.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT, name TEXT);")
    
    print("📦 Generating 200,000 rows...")
    data = [(f"user{i}@gmail.com", ''.join(random.choices(string.ascii_letters, k=10))) for i in range(1, 200001)]
    
    extras.execute_values(cur, "INSERT INTO users (email, name) VALUES %s", data)
    
    conn.commit()
    print("✅ Database ready.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    setup()
