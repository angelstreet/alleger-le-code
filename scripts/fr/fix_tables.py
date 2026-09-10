"""Rebuild the plain text of articles whose Légifrance HTML contains a table: one row per line, cells joined by ' · '."""
import json, re, sys, glob, pathlib
from html.parser import HTMLParser

SRC = pathlib.Path(sys.argv[1])
tree = json.load(open(SRC))
html_by_id = {}
def walk(n):
    if isinstance(n, dict):
        d = n.get('data', n)
        i = d.get('id') if isinstance(d, dict) else None
        if isinstance(i, str) and i.startswith('LEGIARTI'):
            h = d.get('texteHtml') or d.get('texte') or ''
            if h: html_by_id[i] = h
        for v in n.values(): walk(v)
    elif isinstance(n, list):
        for v in n: walk(v)
walk(tree)

class Conv(HTMLParser):
    def __init__(self):
        super().__init__(); self.out = []; self.cell = None; self.row = None; self.in_table = 0
    def handle_starttag(self, t, a):
        if t == 'table': self.in_table += 1
        elif t == 'tr': self.row = []
        elif t in ('td', 'th'): self.cell = []
        elif t in ('p', 'div', 'br', 'li') and not self.in_table: self.out.append('\n')
    def handle_endtag(self, t):
        if t in ('td', 'th') and self.cell is not None:
            txt = re.sub(r'\s+', ' ', ''.join(self.cell)).strip()
            if self.row is not None: self.row.append(txt)
            self.cell = None
        elif t == 'tr' and self.row is not None:
            cells = [c for c in self.row if c]
            if cells: self.out.append('\n' + ' · '.join(cells))
            self.row = None
        elif t == 'table':
            self.in_table -= 1; self.out.append('\n')
        elif t in ('p', 'div', 'li') and not self.in_table: self.out.append('\n')
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
        elif self.row is None: self.out.append(d)
    def text(self):
        s = ''.join(self.out)
        s = re.sub(r'[ \t]+', ' ', s)
        s = re.sub(r'\n{3,}', '\n\n', s)
        return s.strip()

def convert(h):
    c = Conv(); c.feed(h); return c.text()

changed = 0
for f in sorted(glob.glob('data/fr_*.json')):
    d = json.load(open(f)); n = 0
    for s in d.get('sections', []):
        for a in s['articles']:
            i = a['url'].rsplit('/', 1)[-1]
            h = html_by_id.get(i)
            if h and '<table' in h:
                a['text'] = convert(h); n += 1
    if n:
        json.dump(d, open(f, 'w'), ensure_ascii=False, indent=1); changed += n
        print(f'{f}: {n} table articles rebuilt')
print('total', changed)
