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

print("📂 Import Villages...")
df = pd.read_excel(f"{BASE_PATH}\\Technical_Assessment_February_2026.xlsx")
df.columns = df.columns.str.strip()

villages = df[["Village Name", "District", "Province", "Ward"]].drop_duplicates(subset=["Village Name"])
villages = villages[villages["Village Name"].notna()]
inserted = skipped = 0

for _, row in villages.iterrows():
    try:
        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM VILLAGE WHERE village_name=?) "
            "INSERT INTO VILLAGE (village_name, district, province, ward) VALUES (?,?,?,?)",
            row["Village Name"], row["Village Name"],
            clean_str(row.get("District"), 100),
            clean_str(row.get("Province"), 100),
            clean_str(row.get("Ward"), 100)
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {row['Village Name']} : {e}")
        skipped += 1

conn.commit()
print(f"  ✅ {inserted} villages insérés, {skipped} ignorés")