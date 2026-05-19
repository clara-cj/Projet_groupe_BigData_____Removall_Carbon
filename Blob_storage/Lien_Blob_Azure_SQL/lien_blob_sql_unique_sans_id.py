"""
Récupère toutes les URLs des images sur Azure Blob Storage,
les insère dans la table Photos de Azure SQL,
et effectue un QA/QC pour vérifier les URLs manquantes et les doublons.

Installation : pip install azure-storage-blob pyodbc
Lancer le code : python lien_blob_sql.py
"""

from azure.storage.blob import BlobServiceClient
import pyodbc

# ── 1. Connexion au Blob Storage ──────────────────────────────────────────────
BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=..."
CONTAINER_NAME = "fichiers-terrain"
FOLDER = "photos/"

blob_service = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container = blob_service.get_container_client(CONTAINER_NAME)

# Récupère toutes les URLs des images dans le dossier photos/
blob_urls = [
    f"https://removallcarbonstorage.blob.core.windows.net/{CONTAINER_NAME}/{blob.name}"
    for blob in container.list_blobs(name_starts_with=FOLDER)
]

print(f"{len(blob_urls)} images trouvées sur Blob")

# ── 2. Connexion à Azure SQL ──────────────────────────────────────────────────

SQL_CONNECTION_STRING = "Driver={ODBC Driver 18 for SQL Server};Server=...;Database=...;Uid=...;Pwd=...;Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"

conn = pyodbc.connect(SQL_CONNECTION_STRING)
cursor = conn.cursor()

# Récupérer les URLs déjà existantes en base
cursor.execute("SELECT blob_url FROM Photos")
urls_existantes = set(row[0] for row in cursor.fetchall())
print(f"{len(urls_existantes)} URLs déjà présentes en SQL")

# ── 3. Insertion filtrée ──────────────────────────────────────────────────────
inserees = 0
erreurs = []

for url in blob_urls:
    # On n'insère QUE si l'URL n'est pas dans l'ensemble urls_existantes
    if url not in urls_existantes:
        try:
            cursor.execute("INSERT INTO Photos (blob_url) VALUES (?)", url)
            inserees += 1
        except Exception as e:
            erreurs.append({"url": url, "erreur": str(e)})

conn.commit()
print(f"{inserees} nouvelles URLs insérées.")

# ── 4. QA/QC : vérification que toutes les URLs sont bien dans SQL ────────────
cursor.execute("SELECT blob_url FROM Photos")
urls_dans_sql = set(row[0] for row in cursor.fetchall())

manquantes = [url for url in blob_urls if url not in urls_dans_sql]
doublons   = [url for url in blob_urls if blob_urls.count(url) > 1]

conn.close()

# ── 5. Rapport QA/QC ──────────────────────────────────────────────────────────
print(f"\n── Résultats ──────────────────────────────")
print(f"Images trouvées sur Blob  : {len(blob_urls)}")
print(f"URLs insérées avec succès : {inserees}")
print(f"Erreurs d'insertion       : {len(erreurs)}")
print(f"URLs manquantes dans SQL  : {len(manquantes)}")
print(f"URLs en doublon           : {len(set(doublons))}")

if erreurs:
    print(f"\n── Détail des erreurs ─────────────────────")
    for e in erreurs:
        print(f"  URL    : {e['url']}")
        print(f"  Erreur : {e['erreur']}")
        print()

if manquantes:
    print(f"\n── URLs manquantes dans SQL ───────────────")
    for url in manquantes:
        print(f"  {url}")