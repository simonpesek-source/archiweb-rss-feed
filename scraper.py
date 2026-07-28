import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = 'https://www.archiweb.cz/p'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

rss_items = ""
count = 0
seen_links = set()

try:
    response = requests.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Projdeme všechny odkazy
    for a in soup.find_all('a', href=True):
        href = a['href']
        title = a.get_text(strip=True)
        
        # Projekty na Archiwebu mívají v URL /b/ (budovy) nebo další /p/
        # Podmínka len(title) > 5 ignoruje odkazy, které jsou jen prázdné obrázky bez textu
        if ('/b/' in href or '/p/' in href) and len(title) > 5:
            
            if href.startswith('/'):
                full_url = 'https://www.archiweb.cz' + href
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Vyfiltrujeme případný odkaz na samotnou hlavní rubriku
            if full_url == 'https://www.archiweb.cz/p':
                continue
                
            if full_url not in seen_links and 'archiweb.cz' in full_url:
                seen_links.add(full_url)
                count += 1
                
                # Očištění o speciální znaky pro platné XML
                clean_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                rss_items += f"""
        <item>
            <title>{clean_title}</title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
        </item>"""
                
                if count >= 20: # Stáhne maximálně 20 nejnovějších projektů
                    break

except Exception as e:
    print(f"Chyba při stahování: {e}")

# Sestavení finálního XML
rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Archiweb - Projekty</title>
  <link>{url}</link>
  <description>Nejnovější architektonické projekty z Archiweb.cz</description>
  <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
  {rss_items}
</channel>
</rss>"""

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(rss_feed)

print(f"HOTOVO: Vygenerováno {count} položek z Archiwebu.")
