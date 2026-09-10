import re, json, sys
from bs4 import BeautifulSoup

def load_soup(path):
    with open(path, encoding='utf-8') as f:
        data = f.read()
    return BeautifulSoup(data, 'html.parser')

def art_num_from_id(art_id):
    # art_id like "art_334" or "art_335_a"
    m = re.match(r'art_(\d+)(?:_([a-z]))?$', art_id)
    if not m:
        return None, None
    num = int(m.group(1))
    letter = m.group(2) or ''
    return num, letter

def art_sort_key(art_id):
    num, letter = art_num_from_id(art_id)
    return (num, letter)

def heading_text(article_tag):
    """Extract 'Art. 334' or 'Art. 335a' style text and any marginal title."""
    h6 = article_tag.find('h6', recursive=False)
    label = ''
    if h6:
        a = h6.find('a')
        if a:
            label = a.get_text(' ', strip=True)
        # sometimes there's a marginal title as sibling text/i after the link outside <b>/<i>
    label = re.sub(r'\s+', ' ', label).strip()
    return label

def strip_footnote_markers(tag):
    """Remove <sup> elements that contain an <a> (footnote back-reference markers),
    while leaving plain alinea-number <sup>N</sup> markers untouched (those have no <a>)."""
    for sup in tag.find_all('sup'):
        if sup.find('a') is not None:
            sup.decompose()
    return tag

def clean_paragraph_text(tag):
    strip_footnote_markers(tag)
    txt = tag.get_text('')
    txt = txt.replace('\xa0', ' ').replace('\n', ' ').replace('\r', ' ')
    txt = re.sub(r'[ \t]+', ' ', txt).strip()
    return txt

def format_dl(dl_tag):
    """Format a <dl> of dt(letter)/dd(text) pairs into 'a. text' lines."""
    lines = []
    dts = dl_tag.find_all('dt', recursive=False)
    dds = dl_tag.find_all('dd', recursive=False)
    for dt, dd in zip(dts, dds):
        letter_txt = clean_paragraph_text(dt).rstrip('.').strip()
        body_txt = clean_paragraph_text(dd)
        if letter_txt:
            lines.append(f"{letter_txt}. {body_txt}")
        else:
            lines.append(body_txt)
    return '\n'.join(lines)

def extract_article(article_tag):
    art_id = article_tag.get('id')
    num, letter = art_num_from_id(art_id)
    label = heading_text(article_tag)
    # Body: direct children div.collapseable holds the real content (paragraphs, lists, footnotes)
    body_div = None
    for child in article_tag.find_all('div', class_='collapseable', recursive=False):
        body_div = child
        break
    paras = []
    if body_div:
        for el in body_div.find_all(recursive=False):
            if el.name == 'div' and 'footnotes' in (el.get('class') or []):
                continue
            if el.name == 'p':
                cls = el.get('class') or []
                if 'absatz' in cls:
                    txt = clean_paragraph_text(el)
                    if txt:
                        paras.append(txt)
                else:
                    # other paragraph types (e.g. plain text lines) - still include if non-footnote
                    txt = clean_paragraph_text(el)
                    if txt:
                        paras.append(txt)
            elif el.name == 'dl':
                txt = format_dl(el)
                if txt:
                    paras.append(txt)
            elif el.name in ('ol', 'ul'):
                txt = clean_paragraph_text(el)
                if txt:
                    paras.append(txt)
            elif el.name == 'div':
                # nested collapseable or other div containers - recurse via get_text as fallback
                txt = clean_paragraph_text(el)
                if txt:
                    paras.append(txt)
    text = '\n'.join(paras)
    words = len(text.split())
    return {
        'id': art_id,
        'num': num,
        'letter': letter,
        'label': label,
        'text': text,
        'words': words,
    }

def get_all_articles(soup):
    articles = soup.find_all('article')
    result = []
    for a in articles:
        art_id = a.get('id')
        if not art_id or not art_id.startswith('art_'):
            continue
        result.append(extract_article(a))
    return result

if __name__ == '__main__':
    path = sys.argv[1]
    soup = load_soup(path)
    arts = get_all_articles(soup)
    print(f"Total articles found: {len(arts)}")
    print("First 5:", [a['id'] for a in arts[:5]])
    print("Last 5:", [a['id'] for a in arts[-5:]])
