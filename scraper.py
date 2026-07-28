import requests
from bs4 import BeautifulSoup
from datetime import datetime

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
    response = session.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Podle HTML Archiwebu jsou všechny projekty obalené v <div class="buildings">
    projects = soup.find_all('div', class_='buildings')
    
    for project in projects:
        # Získání odkazu
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
            
        # Získání nadpisu projektu (tag <h3>)
        title_tag = project.find('h3')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        
        # Získání autorů / ateliéru (jsou uloženy ve <span> uvnitř popisu)
        # Získáme texty ze všech spanů a spojíme je čárkou
        author_spans = project.find_all('span')
        authors = ", ".join([span.get_text(strip=True) for span in author_spans if span.get_text(strip=True)])
        
        if full_url not in seen_links:
            seen_links.add(full_url)
            count += 1
            
            # Bezpečné ošetření znaků pro validní XML (např. názvy jako "MACHAR & TEICHMAN")
            clean_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            clean_authors = authors.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            rss_items += f"""
        <item>
            <title>{clean_title}</title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
            <description>Architekti / Ateliér: {clean_authors}</description>
        </item>"""
            
            # Stáhne posledních 25 projektů (můžeš si číslo libovolně upravit)
            if count >= 25: 
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

print(f"HOTOVO: Úspěšně vygenerováno {count} položek z Archiwebu.")
