import requests
import os
import re
import json
from datetime import datetime, timezone, timedelta

# M3U kaynak listesi
m3u_sources = [
    ("https://dl.dropbox.com/scl/fi/dj74gt6awxubl4yqoho07/github.m3u?rlkey=m7pzzvk27d94bkfl9a98tluai", "moon"),
    ("https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u", "iptvTR"),
    ("https://raw.githubusercontent.com/Zerk1903/zerkfilm/refs/heads/main/Filmler.m3u", "zerkfilm"),
    ("https://tinyurl.com/2ao2rans", "powerboard"),
]

# Çıktı dosyaları
birlesik_dosya = "birlesik.m3u"
kayit_json_dir = "kayit_json"
ana_kayit_json = os.path.join(kayit_json_dir, "birlesik_links.json")

# Türkiye saat dilimi
turkiye_saati = timezone(timedelta(hours=3))
now = datetime.now(turkiye_saati)
today = now.strftime("%Y-%m-%d")
now_full = now.strftime("%Y-%m-%d %H:%M:%S")
today_obj = datetime.strptime(today, "%Y-%m-%d")

# Gerekli klasör yoksa oluştur
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

def format_tr_date(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.day}.{d.month}.{d.year}"

def format_tr_datehour(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return f"{d.day}.{d.month}.{d.year} {d.hour:02d}:{d.minute:02d}"

def ensure_group_title(extinf_line, source_name):
    if 'group-title="' not in extinf_line:
        parts = extinf_line.split(" ", 1)
        if len(parts) == 2:
            prefix, rest = parts
            return f'{prefix} group-title="[{source_name}]" {rest}'
        else:
            return f'#EXTINF:-1 group-title="[{source_name}]", Kanal İsimsiz'
    return extinf_line

def get_original_group_title(extinf_line):
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    retu
