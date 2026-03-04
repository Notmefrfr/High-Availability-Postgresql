import psycopg2
import sys

# HAProxy Load Balancer IP
LB_IP = "192.168.56.103"
DB_NAME = "postgres"
DB_USER = "lbuser"
DB_PASS = "password"  # <--- UPDATE THIS

def check_node(port, mode_label):
    print(f"\n--- Checking {mode_label} (Port {port}) ---")
    try:
        # Establish connection
        conn = psycopg2.connect(
            host=LB_IP, port=port, database=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=3
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Check if the node is in Recovery (Read-only)
        cur.execute("SELECT pg_is_in_recovery();")
        is_recovery = cur.fetchone()[0]
        status = "SLAVE (Read-Only)" if is_recovery else "MASTER (Writable)"
        print(f"Status: Connected to {status}")

        # 2. Try to Write if it's the Master port
        if port == 5432:
            cur.execute("INSERT INTO test_ha (val) VALUES ('Data sent to Master port');")
            print("Action: Successfully wrote new row to table.")

        # 3. Try to Read
        cur.execute("SELECT val, created_at FROM test_ha ORDER BY id DESC LIMIT 1;")
        row = cur.fetchone()
        if row:
            print(f"Latest Data: '{row[0]}' at {row[1]}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: Could not connect to Port {port}. {e}")

if __name__ == "__main__":
    # Test the Write Port
    check_node(5432, "WRITE PORT")
    # Test the Read Port
    check_node(5433, "READ PORT")
