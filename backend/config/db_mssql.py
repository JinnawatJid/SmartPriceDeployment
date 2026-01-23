import pyodbc

# =========================
# MSSQL CONFIG
# =========================
MSSQL_CONFIG = {
    "server": "192.192.0.220,50681",        # เช่น localhost หรือ 192.168.x.x
    "database": "SP681",    # DB ที่มี Items_Test
    "username": "sp681_user",                    # หรือ user ที่ใช้จริง
    "password": "Tng#kmitl2",
    "driver": "{ODBC Driver 17 for SQL Server}",
}

def get_mssql_conn():
    conn_str = (
        f"DRIVER={MSSQL_CONFIG['driver']};"
        f"SERVER={MSSQL_CONFIG['server']};"
        f"DATABASE={MSSQL_CONFIG['database']};"
        f"UID={MSSQL_CONFIG['username']};"
        f"PWD={MSSQL_CONFIG['password']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

