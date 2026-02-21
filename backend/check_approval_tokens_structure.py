from config.db_mssql import get_mssql_conn

conn = get_mssql_conn()
cursor = conn.cursor()

cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'approval_tokens'
    ORDER BY ORDINAL_POSITION
""")

print('Columns in approval_tokens:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} (Nullable: {row[2]}, Default: {row[3]})')

conn.close()
