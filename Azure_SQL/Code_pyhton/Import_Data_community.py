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

print("📂 Import Community Visits...")
df = pd.read_excel(f"{BASE_PATH}\\FFs_&_Community_Visits_February_2026.xlsx")
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
            INSERT INTO COMMUNITY_VISIT (co2_id, type, date_of_visit, grouped_round,
                problem_with_pump, pump_producing_water, days_water_not_available,
                constant_water, reason_not_constant, open_close_time,
                strokes_before_water, pump_efficiency, within_optimal_range,
                repaired_by_community_past_4mo, taste_acceptable, color_normal,
                increase_in_illness, borehole_surroundings, minor_problems,
                count_rectifications)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            co2,
            clean_str(row.get("Type"), 50),
            clean_date(row.get("Date of visit")),
            clean_str(row.get("Grouped Round"), 50),
            clean_bit(row.get("Is there a problem with the pump?")),
            clean_bit(row.get("Pump producing water")),
            clean_int(row.get("days water not been available?")),
            clean_bit(row.get("Constant Water")),
            clean_str(row.get("Reason water's not constant"), 300),
            clean_str(row.get("Borehole has open and close time"), 200),
            clean_int(row.get("Number of strokes before water comes out")),
            clean_str(row.get("Pump Efficiency"), 50),
            clean_bit(row.get("Not within Optimal Range")),
            clean_bit(row.get("Borehole repaired by community past 4 mo")),
            clean_bit(row.get("Taste of the water acceptable")),
            clean_bit(row.get("color of the water appear normal?")),
            clean_bit(row.get("Have you noticed an increase in illness")),
            clean_str(row.get("Borehole surroundings"), 200),
            clean_str(row.get("Minor problems"), 500),
            clean_int(row.get("Count Rectifications"))
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1

conn.commit()
print(f"  ✅ {inserted} visites insérées, {skipped} ignorées")

cursor.close()
conn.close()