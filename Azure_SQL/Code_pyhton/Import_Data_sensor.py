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
df = pd.read_excel(f"{BASE_PATH}\\Sensors_Installed_Feb_2026.xlsx")
df.columns = df.columns.str.strip()

# Remplace la partie "Test sur la première ligne" par :
inserted = skipped = 0
for _, row in df.iterrows():
    co2 = row.get("CO2 ID")
    if co2 is None or str(co2).strip() == 'nan':
        skipped += 1
        continue
    co2 = str(co2).strip()
    try:
        cursor.execute("""
            INSERT INTO SENSOR (co2_id, sensor_serial, installation_date,
                type_of_meter, strokes_to_fill_20l, needles_turning, grouped_round)
            VALUES (?,?,?,?,?,?,?)
        """,
            co2,
            str(row.get("Sensor serial #")) if not pd.isna(row.get("Sensor serial #")) else None,
            pd.to_datetime(row.get("Sensor installation date"), dayfirst=True).date() if not pd.isna(row.get("Sensor installation date")) else None,
            str(row.get("Type of water meter")) if not pd.isna(row.get("Type of water meter")) else None,
            int(row.get("Meter install # of strokes to fill 20L")) if not pd.isna(row.get("Meter install # of strokes to fill 20L")) else None,
            int(row.get("Meter needles are turning")) if not pd.isna(row.get("Meter needles are turning")) else None,
            str(row.get("Grouped Round")) if not pd.isna(row.get("Grouped Round")) else None
        )
        inserted += 1
    except Exception as e:
        print(f"❌ {co2} : {e}")
        skipped += 1

conn.commit()
print(f"✅ {inserted} capteurs insérés, {skipped} ignorés")

# Tentative d'insertion
try:
    cursor.execute("""
        INSERT INTO SENSOR (co2_id, sensor_serial, installation_date,
            type_of_meter, strokes_to_fill_20l, needles_turning, grouped_round)
        VALUES (?,?,?,?,?,?,?)
    """,
        co2,
        str(row.get("Sensor serial #")) if row.get("Sensor serial #") else None,
        None,
        str(row.get("Type of water meter")) if row.get("Type of water meter") else None,
        None,
        None,
        None
    )
    conn.commit()
    print("✅ Insertion réussie !")
except Exception as e:
    print(f"❌ Erreur : {e}")

cursor.close()
conn.close()