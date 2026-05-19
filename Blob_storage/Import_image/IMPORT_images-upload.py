import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from bs4 import BeautifulSoup

# ===================== CONFIGURATION =====================
AZURE_CONNECTION_STRING = "XXX"
CONTAINER_NAME = "XXX"
ALL_PHOTOS_FILE = r"XXX"
METER_READINGS_FILE = r"XXX"
FAILED_URLS_LOG     = "XXX"   # QA/QC
# =========================================================

def get_urls(filepath, date_col, url_col):
    with open(filepath, encoding="ISO-8859-1") as f:
        contenu = BeautifulSoup(f, "html.parser")
        toutes_les_lignes = contenu.find_all("tr")
        rows = toutes_les_lignes[1:]  # on saute la 1ère ligne (en-tête)
    urls = []
    #seen = set(), déduplique les URLs identiques dans l'Excel (nécéssaire ou pas?)
    for row in rows:
        cols = row.find_all("td")
        if cols:
            date = cols[date_col].text.strip()  # format DD/MM/YYYY
            yyyymm = date[6:10] + date[3:5]     # ex: "16/07/2025" → "202507"
            if yyyymm <= "202602":              # garder jusqu'à février 2026 inclus
                urls.append(cols[url_col].text.strip())
    return urls

#récupérer les urls des fichiers excel à upload ensuite en blob 
#(fonctionne 1 par 1 pour + de sécurité ou les 2 à la fois)
image_urls = (
    #get_urls(METER_READINGS_FILE, date_col=8, url_col=6) +
    get_urls(ALL_PHOTOS_FILE, date_col=0, url_col=4)   
)
print(f"{len(image_urls)} images à uploader")
 
# Connexion Blob
blob_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container = blob_client.get_container_client(CONTAINER_NAME)

# Compteurs
uploades      = 0
deja_presents = 0
http_errors   = 0   # URL inaccessible (expired, 403, 404, timeout…)
failed_urls   = []

#fonction pour le QA/QC visible même en interrompant le code
def sauvegarder_failed_urls(failed_urls):
    if failed_urls:
        with open(FAILED_URLS_LOG, "a", encoding="utf-8") as f:
            for idx, url, reason in failed_urls:
                f.write(f"{idx}\t{reason}\t{url}\n")


for i, url in enumerate(image_urls, start=1):
    blob_name = f"photos/{url.split('/')[-1]}.jpg"
    blob = container.get_blob_client(blob_name)
 
    try:

        # Vérifie si le blob existe déjà dans Azure
        if blob.exists():
            deja_presents += 1
            print(f"⏭️  [{i}/{len(image_urls)}] Déjà présent, ignoré : {blob_name}")
            continue
        # Télécharger l'image depuis la source
        response = requests.get(url, timeout=20)
 
        if response.status_code == 200:
            # overwrite=False : on n'écrase pas les blobs déjà présents (sauve du temps)
            # C'est sûr ici car le contenu est identique (même URL → même image).
            blob.upload_blob(
                response.content,
                overwrite=False,
                content_settings=ContentSettings(content_type="image/jpeg"),
            )
            uploades += 1
            print(f"✅ [{i}/{len(image_urls)}] Uploadé : {blob_name}")
 
        elif response.status_code == 304:
            # Not Modified — blob déjà à jour côté source
            deja_presents += 1
            print(f"⏭️  [{i}/{len(image_urls)}] Non modifié (304) : {url.split('/')[-1]}")
 
        else:
            http_errors += 1
            failed_urls.append((i, url, f"HTTP {response.status_code}"))
            print(f"❌ [{i}/{len(image_urls)}] HTTP {response.status_code} : {url}")
 
    except requests.exceptions.Timeout:
        http_errors += 1
        failed_urls.append((i, url, "Timeout"))
        print(f"❌ [{i}/{len(image_urls)}] Timeout : {url}")
 
    except requests.exceptions.RequestException as e:
        http_errors += 1
        failed_urls.append((i, url, str(e)))
        print(f"❌ [{i}/{len(image_urls)}] Erreur réseau : {e}")
 
    except Exception as e:
        # Erreur Azure inattendue
        http_errors += 1
        failed_urls.append((i, url, str(e)))
        print(f"❌ [{i}/{len(image_urls)}] Erreur Azure : {e}")

    # Sauvegarde intermédiaire du QA/QC toutes les 1000 uploads
    if i % 1000 == 0:
        sauvegarder_failed_urls(failed_urls)
        failed_urls.clear()  # évite les doublons dans le txt


# Sauvegarde finale des erreurs restantes
sauvegarder_failed_urls(failed_urls)
 
# Résumé final
print()
print("========== RÉSUMÉ ==========")
print(f"✅ Uploadés         : {uploades}")
print(f"⏭️  Déjà à jour      : {deja_presents}")
print(f"❌ Erreurs réseau   : {http_errors}")
print(f"📦 Total traités    : {uploades + deja_presents + http_errors}/{len(image_urls)}")
print("============================")