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

def clean_float(val):
    try:
        if pd.isna(val): return None
        return float(val)
    except: return None

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

print("📂 Import Maintenance (Down_Days + Elias rehab)...")
df1 = pd.read_excel(f"{BASE_PATH}\\Down_Days_February_2026.xlsx")
df1.columns = df1.columns.str.strip()
df1["source"] = "down_days"

df2 = pd.read_excel(f"{BASE_PATH}\\elias rehab.xlsx")
df2.columns = df2.columns.str.strip()
df2["source"] = "elias_rehab"

df = pd.concat([df1, df2], ignore_index=True)
inserted = skipped = 0

for _, row in df.iterrows():
    co2 = row.get("CO2 ID")
    if is_null(co2):
        skipped += 1
        continue
    co2 = str(co2).strip()
    try:
        cursor.execute("""
            INSERT INTO MAINTENANCE (co2_id, village_name, date_first_broke_down,
                end_date, completion_date, created_date, days_broken,
                works_required, work_completed, work_completed_by,
                was_pump_producing, grouped_round, re_repair, rectifications, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            co2,
            clean_str(row.get("Village Name"), 150),
            clean_date(row.get("Date it first broke down")),
            clean_date(row.get("End Date")),
            clean_date(row.get("Completion Date")),
            clean_date(row.get("Created Date")),
            clean_int(row.get("Days Broken")),
            clean_str(row.get("Works Required"), 500),
            clean_str(row.get("Work Completed"), 500),
            clean_str(row.get("Work Completed By"), 200),
            clean_bit(row.get("Was the pump still producing water?")),
            clean_str(row.get("Grouped Round"), 50),
            clean_bit(row.get("VW checked for Removall - rerepair")),
            clean_str(row.get("Rectifications/Problems Name"), 500),
            clean_str(row.get("source"), 50)
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1

conn.commit()
print(f"  ✅ {inserted} interventions insérées, {skipped} ignorées")

cursor.close()
conn.close()