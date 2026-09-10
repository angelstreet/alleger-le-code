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
# Premiere partie > Livre II : Le contrat de travail > Titre II : Formation et execution
# du contrat de travail -- every chapter EXCEPT Chapitre V (Maternite, paternite,
# adoption et education des enfants, L1225-x / D1225-x -- already extracted in the
# "Conges, maternite, paternite" topic).
#
# Chapitre Ier   : Formation du contrat de travail                        (1221)
# Chapitre II    : Execution et modification du contrat de travail        (1222)
# Chapitre III   : Formation et execution de certains types de contrats   (1223)
# Chapitre IV    : Transfert du contrat de travail                        (1224)
# Chapitre V     : Maternite, paternite, adoption... -- EXCLUDED           (1225)
# Chapitre VI    : Maladie, accident et inaptitude medicale               (1226)
# Chapitre VII   : Dispositions penales                                   (1227)
LEG_TITRE_II = "LEGISCTA000006160709"
REG_TITRE_II = "LEGISCTA000018537944"

LEG_CHAP_V_MATERNITE = "LEGISCTA000006177854"
REG_CHAP_V_MATERNITE = "LEGISCTA000018537838"

# Allowed article-number prefixes (chapter numbers) for this topic. Verified by
# inspecting each chapter directly (no cross-chapter prefix leakage found, unlike the
# congés-payés Titre III/Titre V quirks): each chapter's in-force articles use exactly
# its own 4-digit prefix. Chapitre III and Chapitre IV of the partie réglementaire are
# empty (no children at all, so no in-force R/D articles) but are still walked below.
ALLOWED_PREFIXES = {"1221", "1222", "1223", "1224", "1226", "1227"}
EXCLUDED_PREFIX = "1225"


def num_prefix(num):
    m = re.match(r'^[LRD]\s*(\d{4})', num or "")
    return m.group(1) if m else None


BASE_URL_ARTICLE = "https://www.legifrance.gouv.fr/codes/article_lc/{}"


def collect_sections_from_children(node, path_prefix):
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


def collect_sections_for_node(node, path_prefix):
    """Like collect_sections_from_children, but treats `node` itself (not just its
    children) as a candidate for direct in-force articles -- needed here because some
    chapters (e.g. Chapitre IV : Transfert, Chapitre VII : Dispositions pénales) hold
    their articles directly as children of the chapter, with no intermediate Section
    node. collect_sections_from_children only inspects each child's own children, so
    calling it with the chapter itself as `node` would silently miss chapter-level
    articles. Reuses the same recurse closure shape by calling collect_sections_from_children
    on a synthetic wrapper: wrap `node` as the sole child of a throwaway parent.
    """
    wrapper = {"children": [node]}
    return collect_sections_from_children(wrapper, path_prefix)


leg_node_titre_ii = find(root, LEG_TITRE_II)
reg_node_titre_ii = find(root, REG_TITRE_II)

BOOK_PATH = ["Première partie : Les relations individuelles de travail",
             "Livre II : Le contrat de travail",
             "Titre II : Formation et exécution du contrat de travail"]

# Walk every chapter of Titre II directly (skip Chapitre V by id), rather than
# hardcoding each remaining chapter id, so the script self-documents which chapters
# it found and which one it excluded.
leg_chapters = [c for c in leg_node_titre_ii.get("children", []) if c["type"] == "section"]
reg_chapters = [c for c in reg_node_titre_ii.get("children", []) if c["type"] == "section"]

print("\nLEG Titre II chapters found:")
for c in leg_chapters:
    d = c["data"]
    marker = " <-- EXCLUDED (topic 3, congés/maternité)" if d.get("id") == LEG_CHAP_V_MATERNITE else ""
    print("  ", d.get("id"), d.get("title"), marker)

print("\nREG Titre II chapters found:")
for c in reg_chapters:
    d = c["data"]
    marker = " <-- EXCLUDED (topic 3, congés/maternité)" if d.get("id") == REG_CHAP_V_MATERNITE else ""
    print("  ", d.get("id"), d.get("title"), marker)

leg_sections = []
for c in leg_chapters:
    if c["data"].get("id") == LEG_CHAP_V_MATERNITE:
        continue
    leg_sections += collect_sections_for_node(c, BOOK_PATH)

reg_sections = []
for c in reg_chapters:
    if c["data"].get("id") == REG_CHAP_V_MATERNITE:
        continue
    reg_sections += collect_sections_for_node(c, BOOK_PATH)

all_sections = leg_sections + reg_sections

# sanity: make sure nothing with the excluded prefix slipped through
for sec in all_sections:
    for a in sec["articles"]:
        assert num_prefix(a["num"]) != EXCLUDED_PREFIX, a["num"]

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

print("\nTOPIC TOTALS:", topic_L, topic_R, topic_D, topic_total, topic_words)
print("num sections:", len(all_sections))
for s in all_sections:
    print(" -", s["part"], s["id"], s["title"], "| articles:", len(s["articles"]), "| path:", s["path"])

output = {
    "country": "FR",
    "source": "https://registry.npmjs.org/@socialgouv/legi-data (npm package @socialgouv/legi-data, data/LEGITEXT000006072050.json - Code du travail, sourced from DILA/Legifrance LEGI open data); article permalinks on https://www.legifrance.gouv.fr/codes/article_lc/",
    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "topic": "Contrat de travail : formation, exécution, maladie, transfert",
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

OUT = "/Users/joachimndoye/alleger-le-code/data/fr_contrat.json"

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

print("\n=== PER-PREFIX BREAKDOWN ===")
for pref in sorted(breakdown.keys()):
    print(f"--- {pref} ---")
    for p in ["L", "R", "D"]:
        info = breakdown[pref][p]
        if info["count"] == 0:
            continue
        nums_sorted = sorted(info["nums"], key=sort_key)
        print(f"  {p}: count={info['count']} words={info['words']} first={nums_sorted[0]} last={nums_sorted[-1]}")
