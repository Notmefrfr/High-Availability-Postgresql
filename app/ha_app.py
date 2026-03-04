import psycopg2
import psycopg2.pool
import time
import os
import sys

# ==============================
# CONFIG
# ==============================
LB_IP = "192.168.56.103"
DB_NAME = "postgres"
DB_USER = "lbuser"
DB_PASS = "password"

WRITE_PORT = 5432
READ_PORT = 5433


# ==============================
# COLOR OUTPUT
# ==============================
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    END = "\033[0m"


# ==============================
# CONNECTION POOL
# ==============================
def create_pool(port):
    try:
        pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            host=LB_IP,
            port=port,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return pool
    except Exception as e:
        print(f"{Color.RED}Connection failed: {e}{Color.END}")
        return None


def get_connection(pool):
    return pool.getconn()


def release_connection(pool, conn):
    pool.putconn(conn)


# ==============================
# ROLE CHECK
# ==============================
def get_role(conn):
    cur = conn.cursor()
    cur.execute("SELECT pg_is_in_recovery();")
    is_recovery = cur.fetchone()[0]
    cur.close()
    return "SLAVE (Read-Only)" if is_recovery else "MASTER (Writable)"


# ==============================
# SAFE QUERY EXECUTION
# ==============================
def execute_query(pool, query, write=False):
    conn = None
    try:
        conn = get_connection(pool)
        conn.autocommit = True
        role = get_role(conn)

        if write and "MASTER" not in role:
            print(f"{Color.RED}Write blocked: Connected to SLAVE!{Color.END}")
            return

        cur = conn.cursor()
        cur.execute(query)

        if cur.description:
            rows = cur.fetchall()
            for row in rows:
                print(row)

        cur.close()

    except Exception as e:
        print(f"{Color.RED}Query error: {e}{Color.END}")
    finally:
        if conn:
            release_connection(pool, conn)


# ==============================
# FUNCTIONS
# ==============================
def show_tables(pool):
    print(f"{Color.CYAN}Listing tables...{Color.END}")
    execute_query(pool,
        "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    )


def create_table(pool):
    name = input("Table name: ")
    query = f"""
    CREATE TABLE IF NOT EXISTS {name} (
        id SERIAL PRIMARY KEY,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_query(pool, query, write=True)


def drop_table(pool):
    name = input("Table to drop: ")
    execute_query(pool, f"DROP TABLE IF EXISTS {name};", write=True)


def insert_data(pool):
    table = input("Table name: ")
    value = input("Data value: ")
    query = f"INSERT INTO {table} (data) VALUES ('{value}');"
    execute_query(pool, query, write=True)


def show_role(pool):
    conn = get_connection(pool)
    role = get_role(conn)
    print(f"{Color.GREEN}Connected to: {role}{Color.END}")
    release_connection(pool, conn)


def watch_mode(pool):
    print(f"{Color.YELLOW}Watching node role (Ctrl+C to stop)...{Color.END}")
    try:
        while True:
            conn = get_connection(pool)
            role = get_role(conn)
            print(f"Current Role: {role}")
            release_connection(pool, conn)
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopped watching.")


def interactive_sql(pool):
    print("Enter SQL (type 'exit' to quit)")
    while True:
        sql = input("SQL> ")
        if sql.lower() == "exit":
            break

        write = sql.strip().lower().startswith(
            ("insert", "update", "delete", "create", "drop")
        )
        execute_query(pool, sql, write=write)


# ==============================
# AUTO RETRY MASTER DETECTION
# ==============================
def connect_auto():
    print(f"{Color.BLUE}Attempting MASTER connection...{Color.END}")
    pool = create_pool(WRITE_PORT)

    if pool:
        try:
            conn = pool.getconn()
            role = get_role(conn)
            pool.putconn(conn)

            if "MASTER" in role:
                print(f"{Color.GREEN}Connected to MASTER via 5432{Color.END}")
                return pool
        except:
            pass

    print(f"{Color.YELLOW}Falling back to READ port...{Color.END}")
    return create_pool(READ_PORT)


# ==============================
# MAIN MENU
# ==============================
def main():
    pool = connect_auto()
    if not pool:
        print("Unable to connect.")
        return

    while True:
        print(f"""
{Color.CYAN}==== HA DB Console ===={Color.END}
1. Show Tables (\\dt)
2. Create Table
3. Drop Table
4. Insert Data
5. Interactive SQL
6. Show Current Role
7. Watch Role (Failover Monitor)
8. Exit
""")

        choice = input("Select option: ")

        if choice == "1":
            show_tables(pool)
        elif choice == "2":
            create_table(pool)
        elif choice == "3":
            drop_table(pool)
        elif choice == "4":
            insert_data(pool)
        elif choice == "5":
            interactive_sql(pool)
        elif choice == "6":
            show_role(pool)
        elif choice == "7":
            watch_mode(pool)
        elif choice == "8":
            print("Goodbye.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
