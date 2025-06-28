import requests
import os
import re
import json
from datetime import datetime
import pytz

# Kaynak M3U dosyaları
m3u_sources = [
    ("https://dl.dropbox.com/scl/fi/dj74gt6awxubl4yqoho07/github.m3u?rlkey=m7pzzvk27d94bkfl9a98tluai", "moon"),
    ("https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u", "iptvTR"),
    ("https://raw.githubusercontent.com/Zerk1903/zerkfilm/refs/heads/main/Filmler.m3u", "zerkfilm"),
    ("https://tinyurl.com/2ao2rans", "powerboard"),
]

birlesik_dosya = "birlesik.m3u"
kayit_json_dir = "kayit_json"
kayit_json = os.path.join(kayit_json_dir, "birlesik_links.json")

if not os.path.exists(kayit_json_dir):
    os.makedirs(kayit_json_dir)

def extract_channel_key(extinf_line, url_line):
    match = re.match(r'#EXTINF:.*?,(.*)', extinf_line)
    channel_name = match.group(1).strip() if match else ''
    url = url_line.strip()
    return (channel_name, url)

def parse_m3u_lines(lines):
    kanal_list = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            extinf_line = line
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                kanal_list.append((extract_channel_key(extinf_line, url_line), extinf_line, url_line))
            i += 2
        else:
            i += 1
    return kanal_list

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_group_title(extinf_line, source_name):
    if 'group-title' not in extinf_line:
        extinf_line = extinf_line.replace("#EXTINF:", f"#EXTINF:-1 group-title=\"{source_name}\"", 1)
    return extinf_line

# Saat ayarı Türkiye'ye göre
now_tr = datetime.now(pytz.timezone("Europe/Istanbul"))
timestamp = now_tr.strftime("%Y-%m-%d %H:%M:%S")

birlesik_satirlar = ["#EXTM3U"]
kayitlar = load_json(kayit_json)

for url, source in m3u_sources:
    try:
        response = requests.get(url, timeout=10)
        lines = response.text.strip().splitlines()
        kanallar = parse_m3u_lines(lines)

        for (key, extinf, link) in kanallar:
            extinf = ensure_group_title(extinf, source)
            birlesik_satirlar.append(extinf)
            birlesik_satirlar.append(link)

            key_str = f"{key[0]}|{key[1]}"
            kayitlar[key_str] = {
                "kanal": key[0],
                "url": key[1],
                "kaynak": source,
                "eklenme": timestamp
            }

    except Exception as e:
        print(f"{source} kaynağı indirilemedi: {e}")

with open(birlesik_dosya, "w", encoding="utf-8") as f:
    f.write("\n".join(birlesik_satirlar))

save_json(kayitlar, kayit_json)
print(f"Toplam kanal sayısı: {len(kayitlar)}")
