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

print("📂 Import Technical Assessment → VILLAGE + BOREHOLE...")
df = pd.read_excel(f"{BASE_PATH}\\Technical_Assessment_February_2026.xlsx")
df.columns = df.columns.str.strip()

# --- VILLAGE ---
villages = df[["Village Name", "District", "Province", "Ward"]].drop_duplicates(subset=["Village Name"])
villages = villages[villages["Village Name"].notna()]
v_inserted = 0
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
        v_inserted += 1
    except Exception as e:
        print(f"❌ VILLAGE {row['Village Name']} : {e}")
conn.commit()
print(f"  ✅ {v_inserted} villages insérés")

# --- BOREHOLE ---
inserted = skipped = 0
for _, row in df.iterrows():
    co2 = row.get("CO2 ID")
    if is_null(co2):
        skipped += 1
        continue
    co2 = str(co2).strip()
    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM BOREHOLE WHERE co2_id=?)
            INSERT INTO BOREHOLE (
                co2_id, village_name, province, district, ward,
                gps_lat, gps_lon, elevation_ft,
                estimated_year_construction, well_depth, depth_from_surface,
                apron, previous_water_source, publicly_owned,
                exp_seasons_without_water, installed_before_2010,
                no_households, improved_water_source_2km,
                date_first_visit, near_swamp, power_line, estimated_population
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            co2, co2,
            clean_str(row.get("Village Name"), 150),
            clean_str(row.get("Province"), 100),
            clean_str(row.get("District"), 100),
            clean_str(row.get("Ward"), 100),
            clean_float(row.get("Phone GPS-S")),
            clean_float(row.get("Phone GPS-E")),
            clean_float(row.get("Elevation (ft)")),
            clean_int(row.get("Estimated year of construction")),
            clean_float(row.get("Well Depth")),
            clean_float(row.get("Depth from surface to main water supply")),
            clean_str(row.get("Apron"), 50),
            clean_str(row.get("Previous Water Source"), 200),
            clean_bit(row.get("Is the borehole publicly owned if no RM")),
            clean_bit(row.get("Borehole exp seasons without water RM")),
            clean_bit(row.get("Handpump installed before 2010 RM")),
            clean_int(row.get("No. of households")),
            clean_bit(row.get("Improved water source within 2 km RM")),
            clean_date(row.get("Date first visit")),
            clean_bit(row.get("Borehole near swamps or flooded area RM")),
            clean_bit(row.get("Power line in the village RM")),
            clean_int(row.get("Estimated Population"))
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1
conn.commit()
print(f"  ✅ {inserted} forages insérés, {skipped} ignorés")