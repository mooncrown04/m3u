import requests
import os
import re
import json
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from pytz import timezone as ZoneInfo  # fallback için pytz olabilir

# Türkiye saat dilimini ayarla
try:
    TURKEY_TZ = ZoneInfo("Europe/Istanbul")
except Exception:
    # fallback UTC+3 sabit offset yapabiliriz:
    from datetime import timezone, timedelta
    TURKEY_TZ = timezone(timedelta(hours=3))

def now_turkey():
    return datetime.now(TURKEY_TZ)

# Virgül temizleyici, kanallarda virgül problem yapar, burada virgülü boşlukla değiştiriyoruz
def clean_channel_name(name):
    return name.replace(",", " ").strip()

# extract_channel_key içinde kanal adı temizleniyor
def extract_channel_key(extinf_line, url_line):
    match = re.match(r'#EXTINF:.*?,(.*)', extinf_line)
    channel_name = clean_channel_name(match.group(1)) if match else ''
    url = url_line.strip()
    return (channel_name, url)

# Tarih format fonksiyonları değişmedi ama artık Türkiye saatine göre kullanacağız
def format_tr_date(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.day}.{d.month}.{d.year}"

def format_tr_datehour(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return f"{d.day}.{d.month}.{d.year} {d.hour:02d}:{d.minute:02d}"

# ensure_group_title fonksiyonuna dokunmadım, olduğu gibi kullandım

today_obj = now_turkey().date()  # sadece tarih kısmı
today = today_obj.strftime("%Y-%m-%d")
now_full = now_turkey().strftime("%Y-%m-%d %H:%M:%S")

# Ana JSON dosyasını yükle
ana_link_dict = load_json(ana_kayit_json)

with open(birlesik_dosya, "w", encoding="utf-8") as outfile:
    outfile.write("#EXTM3U\n")
    for m3u_url, source_name in m3u_sources:
        try:
            req = requests.get(m3u_url, timeout=20)
            req.raise_for_status()
        except Exception as e:
            print(f"{m3u_url} alınamadı: {e}")
            continue
        lines = req.text.splitlines()
        kanal_list = parse_m3u_lines(lines)

        yeni_kanallar, eski_kanallar = [], []

        for (key, extinf, url) in kanal_list:
            dict_key = f"{key[0]}|{key[1]}"
            extinf = ensure_group_title(extinf, source_name)

            if dict_key in ana_link_dict:
                ilk_tarih = ana_link_dict[dict_key]["tarih"]
                ilk_tarih_saat = ana_link_dict[dict_key]["tarih_saat"]
                eski_kanallar.append((key, extinf, url, ilk_tarih, ilk_tarih_saat))
            else:
                ana_link_dict[dict_key] = {"tarih": today, "tarih_saat": now_full}
                yeni_kanallar.append((key, extinf, url, today, now_full))

        # Yeni kanal yazımı
        yeni_grup_satirlari = []
        for (key, extinf, url, eklenme_tarihi, eklenme_tarihi_saat) in yeni_kanallar:
            ilk_ad = clean_channel_name(key[0])
            saat_str = format_tr_datehour(eklenme_tarihi_saat)
            group_title = f'[YENİ] [{source_name}]'
            kanal_isim = f'{ilk_ad} [{saat_str}]'
            extinf_clean = re.sub(r'group-title="[^"]*"', f'group-title="{group_title}"', extinf)
            extinf_clean = re.sub(r',.*', f',{kanal_isim}', extinf_clean)
            yeni_grup_satirlari.append((extinf_clean, url))

        if yeni_grup_satirlari:
            outfile.write(f'#EXTINF:-1 group-title="[YENİ] [{source_name}]",\n')
            for extinf, url in yeni_grup_satirlari:
                outfile.write(extinf + "\n")
                outfile.write(url + "\n")

        # Normal grup yazımı
        normal_grup_satirlari = []
        for (key, extinf, url, eklenme_tarihi, eklenme_tarihi_saat) in eski_kanallar:
            ilk_ad = clean_channel_name(key[0])
            tarih_obj = datetime.strptime(eklenme_tarihi, "%Y-%m-%d").date()
            tarih_str = format_tr_date(eklenme_tarihi)
            original_group = get_original_group_title(extinf)

            if (today_obj - tarih_obj).days >= 7:
                if original_group and f"[{source_name}]" not in original_group:
                    new_group_title = f'{original_group}[{source_name}]'
                else:
                    new_group_title = f'{source_name}'
                extinf_clean = re.sub(r'group-title="[^"]*"', f'group-title="{new_group_title}"', extinf)
                kanal_isim = f'{ilk_ad} [{tarih_str}]'
            else:
                saat_str = format_tr_datehour(eklenme_tarihi_saat)
                group_title = f'[YENİ] [{source_name}]'
                extinf_clean = re.sub(r'group-title="[^"]*"', f'group-title="{group_title}"', extinf)
                kanal_isim = f'{ilk_ad} [{saat_str}]'

            extinf_clean = re.sub(r',.*', f',{kanal_isim}', extinf_clean)
            normal_grup_satirlari.append((extinf_clean, url))

        if normal_grup_satirlari:
            outfile.write(f'#EXTINF:-1 group-title="[{source_name}]",\n')
            for extinf, url in normal_grup_satirlari:
                outfile.write(extinf + "\n")
                outfile.write(url + "\n")

# Ana JSON dosyasını kaydet
save_json(ana_link_dict, ana_kayit_json)
print(f"Kayıt dosyası güncellendi: {ana_kayit_json}")
