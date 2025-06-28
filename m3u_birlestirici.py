import re
import requests
import datetime
import pytz
import os
import json

# Türkiye saati için timezone ayarı
TR_TZ = pytz.timezone('Europe/Istanbul')

def format_tr_datehour(dt):
    # Türkiye saati formatı: Gün.Ay Saat:Dakika
    dt_tr = dt.astimezone(TR_TZ)
    return dt_tr.strftime('%d.%m %H:%M')

def group_title_guncelle(extinf, source_name):
    # Eğer group-title="" var ve içi boşsa, içini source_name ile doldur
    if re.search(r'group-title=""', extinf):
        extinf = re.sub(r'group-title=""', f'group-title="{source_name}"', extinf)
    # Eğer hiç group-title yoksa, ekle
    elif 'group-title=' not in extinf:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF: group-title="{source_name}",')
    # group-title doluysa dokunma
    return extinf

def m3u_birlestir():
    kaynaklar = {
        "Kaynak1": "https://example.com/m3u1.m3u",
        "Kaynak2": "https://example.com/m3u2.m3u"
    }
    
    birlesik_list = ['#EXTM3U']
    links_json = {}
    bugun = datetime.datetime.now(TR_TZ)

    for source_name, url in kaynaklar.items():
        response = requests.get(url)
        icerik = response.text.splitlines()
        
        for i, line in enumerate(icerik):
            if line.startswith('#EXTINF'):
                # group-title kontrolü uygula
                line = group_title_guncelle(line, source_name)

                # Örnek: kanal başlığına tarih ve saat ekleme
                # #EXTINF:-1, kanaladı -> #EXTINF:-1, kanaladı [28.06 14:30]
                parts = line.split(',', 1)
                if len(parts) == 2:
                    tarih_saat = format_tr_datehour(bugun)
                    # Zaten tarih yoksa ekle
                    if tarih_saat not in parts[1]:
                        parts[1] = f"{parts[1].strip()} [{tarih_saat}]"
                    line = ','.join(parts)

            birlesik_list.append(line)
        links_json[source_name] = url

    # Dosyaya yaz
    with open('birlesik.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(birlesik_list))

    if not os.path.exists('kayit_json'):
        os.makedirs('kayit_json')
    with open('kayit_json/birlesik_links.json', 'w', encoding='utf-8') as f:
        json.dump(links_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    m3u_birlestir()
