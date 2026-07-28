import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

url = 'https://www.archiweb.cz/p'

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
    
    print("Krok 1: Získávám cookies z hlavní stránky...")
    session.get('https://www.archiweb.cz/', headers=headers, timeout=15)
    time.sleep(2) 
    
    print("Krok 2: Stahuji projekty...")
    response = session.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
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
            
            # Získání obrázku z pozadí
            image_url = ""
            project_box = project.find('div', class_='project_box')
            if project_box and project_box.has_attr('style'):
                style = project_box['style']
                match = re.search(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)', style)
                if match:
                    image_url = match.group(1).replace('\\/', '/').replace('\\.', '.').replace('\\', '').strip()
            
            if full_url not in seen_links:
                seen_links.add(full_url)
                
                # Příprava popisu BEZ vloženého obrázku (obrázek bude jen v enclosure) a BEZ perexu
                description_html = f'<p><strong>Architekti / Ateliér:</strong> {authors}</p>'
                
                enclosure_tag = ""
                media_tag = ""
                if image_url:
                    clean_img = image_url.replace('&', '&amp;')
                    enclosure_tag = f'<enclosure url="{clean_img}" type="image/jpeg" length="1024" />'
                    media_tag = f'<media:content url="{clean_img}" medium="image" />'
                
                rss_items += f"""
        <item>
            <title><![CDATA[{title}]]></title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
            <description><![CDATA[{description_html}]]></description>
            {enclosure_tag}
            {media_tag}
        </item>"""
                
                count += 1
                if count >= 25: # Vráceno na 25 nejnovějších projektů
                    break
    else:
        print("Chyba serveru. Status:", response.status_code)

except Exception as e:
    print(f"Kritická chyba: {e}")

rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
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
