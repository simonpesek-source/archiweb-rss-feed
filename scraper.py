import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

url = 'https://www.archiweb.cz/p'

# Jednodušší hlavičky, aby se s nimi server Archiwebu popasoval
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'cs-CZ,cs;q=0.9,en;q=0.8'
}

rss_items = ""
count = 0
seen_links = set()

try:
    session = requests.Session()
    
    # Krok 1: Návštěva domovské stránky pro získání přístupových cookies (Nette session)
    print("Krok 1: Získávám cookies z hlavní stránky...")
    session.get('https://www.archiweb.cz/', headers=headers, timeout=15)
    time.sleep(2) # Dáme serveru 2 vteřiny, abychom nevypadali jako spamovací bot
    
    # Krok 2: Samotné stažení projektů
    print("Krok 2: Stahuji projekty...")
    response = session.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    
    print(f"Stavový kód odpovědi: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hledáme bloky s třídou 'buildings'
        projects = soup.find_all('div', class_='buildings')
        
        for project in projects:
            link_tag = project.find('a')
            if not link_tag:
                continue
                
            href = link_tag.get('href', '')
            if href.startswith('/'):
                full_url = 'https://www.archiweb.cz' + href
            elif href.startswith('http'):
                full_url = href
            else:
                continue
                
            title_tag = project.find('h3')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            
            author_spans = project.find_all('span')
            authors = ", ".join([span.get_text(strip=True) for span in author_spans if span.get_text(strip=True)])
            
            if full_url not in seen_links:
                seen_links.add(full_url)
                count += 1
                
                # Obaleno do CDATA, aby jakékoliv speciální znaky v textu nerozbily XML
                rss_items += f"""
        <item>
            <title><![CDATA[{title}]]></title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
            <description><![CDATA[Architekti / Ateliér: {authors}]]></description>
        </item>"""
                
                if count >= 25:
                    break
    else:
        print("Server stále vrací chybový kód.")

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

print(f"HOTOVO: Zpracováno {count} projektů.")
