import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = 'https://www.archiweb.cz/p'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'cs,sk;q=0.9,en;q=0.8',
    'Referer': 'https://www.archiweb.cz/',
    'Connection': 'keep-alive'
}

rss_items = ""
count = 0
seen_links = set()

try:
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    
    # Pro jistotu vypíšeme stavový kód serveru
    print(f"Stavový kód odpovědi: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Hledáme absolutně všechny odkazy na stránce
    all_links = soup.find_all('a')
    
    for link_tag in all_links:
        href = link_tag.get('href', '')
        
        # Zajímají nás jen odkazy na budovy (začínají na /b/ a nejsou to jen prázdné cesty)
        if href.startswith('/b/') and len(href) > 4:
            full_url = 'https://www.archiweb.cz' + href
            
            # Uvnitř odkazu hledáme nadpis
            title_tag = link_tag.find('h3')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            
            # Hledáme autory
            author_spans = link_tag.find_all('span')
            authors = ", ".join([span.get_text(strip=True) for span in author_spans if span.get_text(strip=True)])
            
            if full_url not in seen_links:
                seen_links.add(full_url)
                count += 1
                
                # Zabalení do CDATA pro stoprocentní jistotu, že speciální znaky nerozbijí XML
                rss_items += f"""
        <item>
            <title><![CDATA[{title}]]></title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
            <description><![CDATA[Architekti / Ateliér: {authors}]]></description>
        </item>"""
                
                if count >= 25:
                    break
                    
    print(f"Úspěšně zpracováno {count} projektů.")
    
    # Diagnostika: Pokud se nic nestáhlo, vypíšeme, co server vrátil
    if count == 0:
        print("POZOR: Nenašly se žádné články! Tady je ukázka toho, co server vrátil:")
        print(response.text[:1500])

except Exception as e:
    print(f"Kritická chyba: {e}")

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
