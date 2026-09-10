import json, re, html
from datetime import datetime, timezone

SRC = "package/data/LEGITEXT000006072050.json"

with open(SRC, encoding="utf-8") as f:
    root = json.load(f)


def find(node, target_id):
    if isinstance(node.get("data"), dict) and node["data"].get("id") == target_id:
        return node
    for c in node.get("children", []):
        r = find(c, target_id)
        if r:
            return r
    return None


def clean_html_to_text(s):
    if not s:
        return ""
    s = re.sub(r'(?i)<br\s*/?>', '\n', s)
    s = re.sub(r'(?i)</p\s*>', '\n\n', s)
    s = re.sub(r'(?i)<p[^>]*>', '', s)
    s = re.sub(r'(?i)</?li[^>]*>', '\n', s)
    s = re.sub(r'(?i)</?ul[^>]*>', '\n', s)
    s = re.sub(r'(?i)</?ol[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in s.split('\n')]
    out_lines = []
    blank = False
    for ln in lines:
        if ln == "":
            if not blank:
                out_lines.append("")
            blank = True
        else:
            out_lines.append(ln)
            blank = False
    text = "\n".join(out_lines).strip()
    return text


def word_count(text):
    return len(text.split())


def article_part(num):
    if num and num.startswith("L"):
        return "L"
    if num and num.startswith("R"):
        return "R"
    if num and num.startswith("D"):
        return "D"
    return "?"


# ---- code-wide totals: walk entire tree, count in-force articles ----
def walk_all_articles(node):
    if node["type"] == "article":
        yield node
    for c in node.get("children", []):
        yield from walk_all_articles(c)


code_L = code_R = code_D = 0
code_words = 0
code_total = 0
for art in walk_all_articles(root):
    d = art["data"]
    if d.get("etat") != "VIGUEUR":
        continue
    num = d.get("num") or ""
    part = article_part(num)
    text = clean_html_to_text(d.get("texteHtml") or d.get("texte") or "")
    w = word_count(text)
    code_total += 1
    code_words += w
    if part == "L":
        code_L += 1
    elif part == "R":
        code_R += 1
    elif part == "D":
        code_D += 1

print("CODE TOTALS:", code_L, code_R, code_D, code_total, code_words)

# ---- topic sections ----
# Troisieme partie > Livre Ier : Duree du travail, repos et conges
LEG_TITRE_II = "LEGISCTA000006160754"   # Titre II : Duree du travail, repartition et amenagement des horaires
LEG_TITRE_III = "LEGISCTA000006160755"  # Titre III : Repos et jours feries
REG_TITRE_II = "LEGISCTA000018534652"
REG_TITRE_III = "LEGISCTA000018534452"

# Allowed article-number prefixes (chapter numbers) per scope.
ALLOWED_PREFIXES = {"3121", "3122", "3123", "3131", "3132", "3133", "3134"}


def num_prefix(num):
    m = re.match(r'^[LRD]\s*(\d{4})', num or "")
    return m.group(1) if m else None


BASE_URL_ARTICLE = "https://www.legifrance.gouv.fr/codes/article_lc/{}"


def collect_sections(node, path_prefix):
    sections = []

    def recurse(n, path):
        title = n["data"].get("title", "").strip() if isinstance(n.get("data"), dict) else ""
        cur_path = path + [title] if title else path
        direct_articles = [c for c in n.get("children", []) if c["type"] == "article"]
        sub_sections = [c for c in n.get("children", []) if c["type"] == "section"]

        if direct_articles:
            arts = []
            for a in direct_articles:
                ad = a["data"]
                if ad.get("etat") != "VIGUEUR":
                    continue
                num = ad.get("num") or ""
                if num_prefix(num) not in ALLOWED_PREFIXES:
                    continue
                text = clean_html_to_text(ad.get("texteHtml") or ad.get("texte") or "")
                arts.append({
                    "num": num,
                    "url": BASE_URL_ARTICLE.format(ad.get("id")),
                    "text": text,
                    "words": word_count(text),
                })
            if arts:
                part = article_part(arts[0]["num"])
                sections.append({
                    "id": n["data"].get("id"),
                    "path": " > ".join(cur_path[:-1]) if len(cur_path) > 1 else "",
                    "title": title,
                    "part": part,
                    "articles": arts,
                })
        for sc in sub_sections:
            recurse(sc, cur_path)

    for c in node.get("children", []):
        recurse(c, path_prefix)
    return sections


leg_node_2 = find(root, LEG_TITRE_II)
leg_node_3 = find(root, LEG_TITRE_III)
reg_node_2 = find(root, REG_TITRE_II)
reg_node_3 = find(root, REG_TITRE_III)

BOOK_PATH = ["Livre Ier : Durée du travail, repos et congés"]

leg_sections = (
    collect_sections(leg_node_2, BOOK_PATH + ["Titre II : Durée du travail, répartition et aménagement des horaires"])
    + collect_sections(leg_node_3, BOOK_PATH + ["Titre III : Repos et jours fériés"])
)
reg_sections = (
    collect_sections(reg_node_2, BOOK_PATH + ["Titre II : Durée du travail, répartition et aménagement des horaires"])
    + collect_sections(reg_node_3, BOOK_PATH + ["Titre III : Repos et jours fériés"])
)

all_sections = leg_sections + reg_sections

topic_L = topic_R = topic_D = 0
topic_words = 0
topic_total = 0
for sec in all_sections:
    for a in sec["articles"]:
        p = article_part(a["num"])
        topic_total += 1
        topic_words += a["words"]
        if p == "L":
            topic_L += 1
        elif p == "R":
            topic_R += 1
        elif p == "D":
            topic_D += 1

print("TOPIC TOTALS:", topic_L, topic_R, topic_D, topic_total, topic_words)
print("num sections:", len(all_sections))
for s in all_sections:
    print(" -", s["part"], s["id"], s["title"], "| articles:", len(s["articles"]), "| path:", s["path"])

output = {
    "country": "FR",
    "source": "https://registry.npmjs.org/@socialgouv/legi-data (npm package @socialgouv/legi-data, data/LEGITEXT000006072050.json - Code du travail, sourced from DILA/Legifrance LEGI open data); article permalinks on https://www.legifrance.gouv.fr/codes/article_lc/",
    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "topic": "Durée du travail, repos et jours fériés",
    "code_totals": {
        "articles_L": code_L,
        "articles_R": code_R,
        "articles_D": code_D,
        "articles_total": code_total,
        "words_total": code_words,
        "note": "Computed over the entire Code du travail (LEGITEXT000006072050) tree from the @socialgouv/legi-data dataset, counting only articles with etat == 'VIGUEUR' (currently in force), across Partie législative, Partie réglementaire, and their 'ancienne' (superseded) subtrees if any in-force articles remain there. Word count = whitespace-split tokens of the HTML-stripped article text."
    },
    "topic_totals": {
        "articles_L": topic_L,
        "articles_R": topic_R,
        "articles_D": topic_D,
        "articles_total": topic_total,
        "words_total": topic_words,
    },
    "sections": all_sections,
}

OUT = "/Users/joachimndoye/Library/Application Support/Claude/scratch-workspaces/b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6/f4376b92-1b81-43b2-9c5f-059506ff32d8/scratch-2026-09-10-54498a/data/fr_temps_travail.json"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("WROTE", OUT)

# ---- per-chapter (article-number prefix) breakdown ----
from collections import defaultdict

breakdown = defaultdict(lambda: {"L": {"count": 0, "words": 0, "nums": []},
                                  "R": {"count": 0, "words": 0, "nums": []},
                                  "D": {"count": 0, "words": 0, "nums": []}})

def sort_key(num):
    m = re.match(r'^[LRD]\s*\d{4}-(\d+)', num or "")
    return int(m.group(1)) if m else 0

for sec in all_sections:
    for a in sec["articles"]:
        pref = num_prefix(a["num"])
        p = article_part(a["num"])
        breakdown[pref][p]["count"] += 1
        breakdown[pref][p]["words"] += a["words"]
        breakdown[pref][p]["nums"].append(a["num"])

print("\n=== PER-CHAPTER BREAKDOWN ===")
for pref in sorted(breakdown.keys()):
    print(f"--- {pref} ---")
    for p in ["L", "R", "D"]:
        info = breakdown[pref][p]
        if info["count"] == 0:
            continue
        nums_sorted = sorted(info["nums"], key=sort_key)
        print(f"  {p}: count={info['count']} words={info['words']} first={nums_sorted[0]} last={nums_sorted[-1]}")
