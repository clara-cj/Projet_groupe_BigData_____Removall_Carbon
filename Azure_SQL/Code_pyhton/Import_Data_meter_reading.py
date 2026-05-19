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
        if pd.isna(val):
            return None
        return float(val)
    except:
        return None

def clean_int(val):
    try:
        if pd.isna(val):
            return None
        return int(val)
    except:
        return None

def clean_bit(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except:
        pass
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        return int(bool(val))
    s = str(val).strip().lower()
    return 1 if s in ("yes", "true", "1", "oui") else 0

def clean_date(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except:
        pass
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except:
        return None

def is_null(val):
    try:
        return pd.isna(val)
    except:
        return val is None

print("📂 Import Meter Readings...")
df = pd.read_excel(f"{BASE_PATH}\\Meter_Readings_February_2026.xlsx")
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
            INSERT INTO METER_READING (co2_id, date_of_reading, meter_reading,
                total_water_usage_m3, litres_per_person_per_day, in_person_reading,
                problem_with_meter, problem_description, latest_ul_total_pop,
                days_since_installation, collecting_drinking_only,
                school_or_institution, restricts_access, closing_time)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            co2,
            clean_date(row.get("Date of reading")),
            clean_float(row.get("Meter reading")),
            clean_float(row.get("Total water usage (m³)")),
            clean_float(row.get("Total litres per person per day usage")),
            clean_bit(row.get("Was this an in person meter reading?")),
            clean_bit(row.get("Problem with meter reading")),
            str(row.get("Problem with meter reading description")) if not is_null(row.get("Problem with meter reading description")) else None,
            clean_int(row.get("Latest UL total pop")),
            clean_int(row.get("Days current reading from installation")),
            clean_bit(row.get("Collecting water for drinking only?")),
            clean_bit(row.get("School or institution using the borehole")),
            clean_bit(row.get("Do you restrict access to the borehole?")),
            str(row.get("If Yes, indicate closing time")) if not is_null(row.get("If Yes, indicate closing time")) else None
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1

conn.commit()
print(f"  ✅ {inserted} relevés insérés, {skipped} ignorés")

cursor.close()
conn.close()