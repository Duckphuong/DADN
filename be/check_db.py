import sqlite3

conn = sqlite3.connect('water_quality.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    table_name = table[0]
    print(f'\n--- {table_name} ---')

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print('Columns:', [col[1] for col in columns])

    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
    rows = cursor.fetchall()
    if rows:
        print('Sample data:')
        for row in rows:
            print(row)
    else:
        print('No data')

    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f'Total rows: {count}')

conn.close()