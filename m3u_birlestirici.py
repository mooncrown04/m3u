import requests
import os
import re
import json
from datetime import datetime, timedelta
import pytz

m3u_sources = [
    ("https://dl.dropbox.com/scl/fi/dj74gt6awxubl4yqoho07/github.m3u?rlkey=m7pzzvk27d94bkfl9a98tluai", "moon"),
    ("https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u", "iptvTR"),
    ("https://raw.githubusercontent.com/Zerk1903/zerkfilm/refs/heads/main/Filmler.m3u", "zerkfilm"),
    ("https://tinyurl.com/2ao2rans", "powerboard"),
]

birlesik_dosya = "birlesik.m3u"
kayit_json_dir = "kayit_json"
ana_kayit_json = os.path.join(kayit_json_dir, "birlesik_links.json")

if not os.path.exists(kayit_json_dir):
    os.makedirs(kayit_json_dir)

def escape_logo_commas(line):
    return re.sub(r'logo="([^"]+?)"', lambda m: f'logo="{m.group(1).replace(",", "%2C")}"', line)

def extract_channel_key(extinf_line, url_line):
    name_match = re.match(r'#EXTINF:.*?,(.*)', extinf_line)
    channel_name = name_match.group(1).strip() if name_match else ''
    return (channel_name, url_line.strip())

def parse_m3u(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF') and i + 1 < len(lines):
            extinf = escape_logo_commas(line)
            url = lines[i + 1].strip()
            result.append((extract_channel_key(extinf, url), extinf, url))
            i += 2
        else:
            i += 1
    return result

def load_json(path):
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else {}

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_date_tr(dt):
    return dt.strftime("%d.%m.%Y")

def format_datehour_tr(dt):
    return dt.strftime("%d.%m.%Y %H:%M")

def get_group_title(extinf):
    m = re.search(r'group-title="(.*?)"', extinf)
    return m.group(1).strip() if m else ""

def set_group_title(extinf, new_group):
    if 'group-title="' in extinf:
        return re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
    return extinf.replace("#EXTINF:", f'#EXTINF: group-title="{new_group}"')

def set_channel_name(extinf, new_name):
    return re.sub(r',.*', f',{new_name}', extinf)

tr_timezone = pytz.timezone("Europe/Istanbul")
now = datetime.now(tr_timezone)
today = now.strftime("%Y-%m-%d")
now_full = now.strftime("%Y-%m-%d %H:%M:%S")
today_obj = datetime.strptime(today, "%Y-%m-%d")
ana_link_dict = load_json(ana_kayit_json)

with open(birlesik_dosya, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for m3u_url, source_name in m3u_sources:
        try:
            res = requests.get(m3u_url, timeout=20)
            res.raise_for_status()
        except Exception as e:
            print(f"{m3u_url} alınamadı: {e}")
            continue

        entries = parse_m3u(res.text.splitlines())
        yeni, eski = [], []

        for (key, extinf, url) in entries:
            kanal_key = f"{key[0]}|{key[1]}"
            if kanal_key not in ana_link_dict:
                ana_link_dict[kanal_key] = {"tarih": today, "tarih_saat": now_full}
                yeni.append((key, extinf, url, today, now_full))
            else:
                kayit = ana_link_dict[kanal_key]
                eski.append((key, extinf, url, kayit["tarih"], kayit["tarih_saat"]))

        if yeni:
            f.write(f'#EXTINF:-1 group-title="[YENİ] [{source_name}]",\n')
            for (key, extinf, url, tarih, tarih_saat) in yeni:
                saat_str = format_datehour_tr(datetime.strptime(tarih_saat, "%Y-%m-%d %H:%M:%S"))
                kanal_adi = f"{key[0]} [{saat_str}]"
                extinf = set_group_title(extinf, f"[YENİ] [{source_name}]")
                extinf = set_channel_name(extinf, kanal_adi)
                f.write(extinf + "\n" + url + "\n")

        normal = []
        for (key, extinf, url, tarih, tarih_saat) in eski:
            eklenme = datetime.strptime(tarih, "%Y-%m-%d")
            guncel_group = get_group_title(extinf)
            kanal_adi = f"{key[0]} [{format_date_tr(eklenme)}]"

            if (today_obj - eklenme).days < 7:
                saat_str = format_datehour_tr(datetime.strptime(tarih_saat, "%Y-%m-%d %H:%M:%S"))
                extinf = set_group_title(extinf, f"[YENİ] [{source_name}]")
                extinf = set_channel_name(extinf, f"{key[0]} [{saat_str}]")
            else:
                if not guncel_group:
                    extinf = set_group_title(extinf, source_name)
                elif guncel_group.strip() == "":
                    extinf = set_group_title(extinf, source_name)
                elif f"[{source_name}]" not in guncel_group:
                    extinf = set_group_title(extinf, f"{guncel_group}[{source_name}]")
                extinf = set_channel_name(extinf, kanal_adi)
            normal.append((extinf, url))

        if normal:
            f.write(f'#EXTINF:-1 group-title="[{source_name}]",\n')
            for extinf, url in normal:
                f.write(extinf + "\n" + url + "\n")

save_json(ana_link_dict, ana_kayit_json)
