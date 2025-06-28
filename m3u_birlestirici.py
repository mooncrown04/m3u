import os
import requests
import json

# Kaynak URL'lerin bulunduğu dosya
URL_LIST_FILE = 'm3u_kanal_listesi.txt'

# Kayıt klasörü ve dosyaları
OUTPUT_FILE = 'birlesik.m3u'
JSON_FOLDER = 'kayit_json'
JSON_OUTPUT_FILE = os.path.join(JSON_FOLDER, 'birlesik_links.json')

# Klasör yoksa oluştur
os.makedirs(JSON_FOLDER, exist_ok=True)

# Dosya varsa sil
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)
if os.path.exists(JSON_OUTPUT_FILE):
    os.remove(JSON_OUTPUT_FILE)

# JSON kayıt listesi
kayitli_kanallar = []

with open(URL_LIST_FILE, 'r', encoding='utf-8') as url_file:
    urls = [url.strip() for url in url_file.readlines() if url.strip()]

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    outfile.write('#EXTM3U\n')

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                lines = response.text.splitlines()
                for i in range(len(lines)):
                    line = lines[i].strip()
                    if line.startswith('#EXTINF:'):
                        # Sonraki satırda link olmalı
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            kanal_adi = line.split(',')[-1].strip()

                            # Aynı kanal adı varsa geç
                            if kanal_adi in kayitli_kanallar:
                                continue

                            # tvg-logo içinde virgül varsa temizle
                            if 'tvg-logo="' in line:
                                start = line.find('tvg-logo="') + 10
                                end = line.find('"', start)
                                logo_url = line[start:end]
                                logo_url_clean = logo_url.replace(',', '')
                                line = line[:start] + logo_url_clean + line[end:]

                            # Kaydet
                            outfile.write(line + '\n')
                            outfile.write(next_line + '\n')

                            kayitli_kanallar.append(kanal_adi)
        except Exception as e:
            print(f"Hata ({url}): {e}")

# JSON'a yaz
with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as json_file:
    json.dump(kayitli_kanallar, json_file, ensure_ascii=False, indent=2)
