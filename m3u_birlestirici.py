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

# Örnek fonksiyon, M3U linklerinden çekme ve birleştirme burada olur
def m3u_birlestir():
    # Örnek, kaynak isimleri ve url listesi
    kaynaklar = {
        "Kaynak1": "https://example.com/m3u1.m3u",
        "Kaynak2": "https://example.com/m3u2.m3u"
    }
    
    birlesik_list = []
    links_json = {}
    bugun = datetime.datetime.now(TR_TZ).date()

    for source_name, url in kaynaklar.items():
        response = requests.get(url)
        icerik = response.text.splitlines()
        
        for line in icerik:
            if line.startswith('#EXTINF'):
                # extinf satırına group-title kontrolü uygula
                line = group_title_guncelle(line, source_name)
                # Tarih veya saat bilgisi eklemek istersen burada yapabilirsin
                # Örnek: kanal ismi içine tarih ekle
                # ...
            birlesik_list.append(line)
        links_json[source_name] = url

    # Dosyalara yazma
    with open('birlesik.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(birlesik_list))

    if not os.path.exists('kayit_json'):
        os.makedirs('kayit_json')
    with open('kayit_json/birlesik_links.json', 'w', encoding='utf-8') as f:
        json.dump(links_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    m3u_birlestir()
