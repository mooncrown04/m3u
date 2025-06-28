import os
import requests
import json
import re

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

# JSON kayıt listesi (detaylı)
kayitli_kanallar = []

def temizle_logo(logo_url):
    return logo_url.replace(',', '')

def parse_extinf(line):
    # Örnek #EXTINF:-1 tvg-id="id" tvg-name="name" tvg-logo="logo" group-title="group",Kanal Adı
    # regex ile çekiyoruz
    pattern = r'#EXTINF:-?\d+((?: [^=]+="[^"]*")*),(.+)'
    match = re.match(pattern, line)
    if not match:
        return None
    attrs_str = match.group(1)
    kanal_adi = match.group(2).strip()

    attrs = {}
    attr_pattern = r' ([^=]+)="([^"]*)"'
    for m in re.finditer(attr_pattern, attrs_str):
        key = m.group(1)
        value = m.group(2)
        if key == 'tvg-logo':
            value = temizle_logo(value)
        attrs[key] = value

    return kanal_adi, attrs

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
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            parse_result = parse_extinf(line)
                            if parse_result is None:
                                continue
                            kanal_adi, attrs = parse_result

                            # Aynı kanal adı varsa geç
                            if any(k['kanal_adi'] == kanal_adi for k in kayitli_kanallar):
                                continue

                            # Kaydet
                            # Önce temizlenmiş satırı tekrar oluştur
                            attr_str = ''.join([f' {k}="{v}"' for k, v in attrs.items()])
                            yeni_extinf = f'#EXTINF:-1{attr_str},{kanal_adi}'

                            outfile.write(yeni_extinf + '\n')
                            outfile.write(next_line + '\n')

                            kayitli_kanallar.append({
                                "kanal_adi": kanal_adi,
                                **attrs,
                                "url": next_line
                            })

        except Exception as e:
            print(f"Hata ({url}): {e}")

# JSON'a yaz
with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as json_file:
    json.dump(kayitli_kanallar, json_file, ensure_ascii=False, indent=2)
