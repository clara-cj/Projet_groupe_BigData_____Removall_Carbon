import pandas as pd
import pyodbc
import os

SERVER   = "..."
DATABASE = "..."
USERNAME = "..."
PASSWORD = "..."

conn_str = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server=tcp:{SERVER},1433;"
    f"Database={DATABASE};"
    f"Uid={USERNAME};"
    f"Pwd={PASSWORD};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
)

conn   = pyodbc.connect(conn_str)
cursor = conn.cursor()
print("✅ Connexion réussie !")

BASE_PATH = os.path.join(os.getcwd(), "All Reports February 2026")

def clean_int(val):
    try:
        if pd.isna(val): return None
        return int(val)
    except: return None

def clean_bit(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except: pass
    if isinstance(val, bool): return int(val)
    if isinstance(val, (int, float)): return int(bool(val))
    s = str(val).strip().lower()
    return 1 if s in ("yes", "true", "1", "oui") else 0

def clean_date(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except: pass
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except: return None

def clean_str(val, max_len=None):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except: pass
    s = str(val).strip()
    if max_len: s = s[:max_len]
    return s

def is_null(val):
    try: return pd.isna(val)
    except: return val is None

print("📂 Import Repair Parts...")
df = pd.read_excel(f"{BASE_PATH}\\Repair_Parts_Needed_February_2026.xlsx")
df.columns = df.columns.str.strip()
inserted = skipped = 0

for _, row in df.iterrows():
    co2 = row.get("CO2 ID")
    if is_null(co2):
        skipped += 1
        continue
    co2 = str(co2).strip()
    try:
        cursor.execute("""
            INSERT INTO REPAIR_PART (co2_id, village_name, repair_date, repairs_name,
                quantity, repairs_needed, other_part, re_repair, local_partner)
            VALUES (?,?,?,?,?,?,?,?,?)
        """,
            co2,
            clean_str(row.get("Village Name"), 150),
            clean_date(row.get("Repair Date")),
            clean_str(row.get("Repairs Name"), 200),
            clean_int(row.get("Quantity")),
            clean_str(row.get("Repairs needed"), 500),
            clean_str(row.get("Other part"), 200),
            clean_bit(row.get("Re-repair?")),
            clean_str(row.get("Local Partner"), 200)
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1

conn.commit()
print(f"  ✅ {inserted} pièces insérées, {skipped} ignorées")

cursor.close()
conn.close()