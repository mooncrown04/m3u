import requests
import os
import re
import json
from datetime import datetime
import pytz

# Kaynak M3U dosyaları (URL, kaynak adı)
m3u_sources = [
    ("https://dl.dropbox.com/scl/fi/dj74gt6awxubl4yqoho07/github.m3u?rlkey=m7pzzvk27d94bkfl9a98tluai", "moon"),
    ("https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u", "iptvTR"),
    ("https://raw.githubusercontent.com/Zerk1903/zerkfilm/refs/heads/main/Filmler.m3u", "zerkfilm"),
    ("https://tinyurl.com/2ao2rans", "powerboard"),
]

birlesik_dosya = "birlesik.m3u"
kayit_json_dir = "kayit_json"
kayit_json = os.path.join(kayit_json_dir, "birlesik_links.json")

# Klasör yoksa oluştur
if not os.path.exists(kayit_json_dir):
    os.makedirs(kayit_json_dir)

def turkiye_saati():
    tr_tz = pytz.timezone("Europe/Istanbul")
    return datetime.now(tr_tz).strftime("%Y-%m-%d %H:%M:%S")

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
    # GROUP-TITLE yoksa ekle
    if 'group-title="' not in extinf_line:
        return re.sub(r'(#EXTINF:-1)', r'\1 group-title="{}"'.format(source_name), extinf_line)
    return extinf_line

# Mevcut veriyi yükle
json_kayit = load_json(kayit_json)
tum_kanallar = []
yeni_json_kayit = {}

for url, kaynak_adi in m3u_sources:
    try:
        yanit = requests.get(url, timeout=10)
        yanit.raise_for_status()
        satirlar = yanit.text.strip().splitlines()
        kanallar = parse_m3u_lines(satirlar)

        for key, extinf, stream_url in kanallar:
            extinf = ensure_group_title(extinf, kaynak_adi)
            kanal_key = f"{key[0]}|{key[1]}"
            yeni_json_kayit[kanal_key] = {
                "kaynak": kaynak_adi,
                "eklenme": turkiye_saati()
            }
            tum_kanallar.append((extinf, stream_url))

    except Exception as e:
        print(f"Hata ({kaynak_adi}): {e}")

# Çık
