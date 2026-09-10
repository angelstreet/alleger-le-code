import json, re
from bs4 import BeautifulSoup
from parse_co import load_soup, get_all_articles, art_num_from_id

OUT_PATH = "/Users/joachimndoye/Library/Application Support/Claude/scratch-workspaces/b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6/f4376b92-1b81-43b2-9c5f-059506ff32d8/scratch-2026-09-10-54498a/data/ch_temps_travail.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LTR_URL = "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr"

def clean(txt):
    txt = txt.replace('\xa0', ' ').replace('­', '')
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def art_display_num(a):
    return f"Art. {a['num']}{a['letter']}"

def main():
    co_soup = load_soup('co_20260101.html')
    co_arts = get_all_articles(co_soup)
    co_by_id = {a['id']: a for a in co_arts}

    ltr_soup = load_soup('ltr_20230901.html')
    ltr_arts = get_all_articles(ltr_soup)
    ltr_by_id = {a['id']: a for a in ltr_arts}

    olt1_soup = load_soup('olt1_20240901.html')
    olt1_arts = get_all_articles(olt1_soup)

    # ---- code_totals (identical to topic 1 file) ----
    tit10 = [a for a in co_arts if a['num'] is not None and 319 <= a['num'] <= 362]
    co_titre10 = {
        "articles": len(tit10),
        "words": sum(a['words'] for a in tit10),
        "range": "art. 319–362",
    }
    ltr_totals = {
        "articles": len(ltr_arts),
        "words": sum(a['words'] for a in ltr_arts),
    }
    co_whole = {
        "articles": len(co_arts),
        "words": sum(a['words'] for a in co_arts),
    }
    code_totals_note = "Counts are per <article> element in the Fedlex consolidated HTML (fr), including lettered sub-articles (e.g. 335a) and a handful of jointly-repealed article ranges (e.g. 'art. 226a–226d') that count as one element each. Words = whitespace-separated tokens of the plain article text (footnote markers/footnotes excluded). CO whole = art. 1–1186 (Livre cinquième du Code civil suisse), état 1er janvier 2026. LTr = RS 822.11, état 1er septembre 2023."

    olt1_totals = {
        "articles": len(olt1_arts),
        "words": sum(a['words'] for a in olt1_arts),
    }

    # ---- walk the LTr HTML section 'III. Durée du travail et repos' (id lvl_II_I) ----
    sec_root = ltr_soup.find('section', id='lvl_II_I')
    if sec_root is None:
        raise SystemExit("Could not find LTr section lvl_II_I")

    chapter_heading = None
    h1 = sec_root.find('h1', recursive=False) or sec_root.find('h1')
    # h1 is a direct child structure: <h1 class="heading">...<a>text</a></h1>
    h1_tag = sec_root.find('h1')
    if h1_tag:
        chapter_heading = clean(h1_tag.get_text(' ', strip=True))

    sections = []
    current_section = None  # dict for current h2
    current_marginal = None
    repealed_skipped = []

    for el in sec_root.find_all(['h2', 'div', 'article'], recursive=True):
        if el.name == 'h2':
            title = clean(el.get_text(' ', strip=True))
            # strip trailing footnote-marker digits accidentally concatenated (e.g. "3. Travail continu 57")
            title = re.sub(r'\s+\d+$', '', title)
            current_section = {
                "id": None,  # filled after slug computed
                "title": title,
                "articles": [],
            }
            sections.append(current_section)
            current_marginal = None
        elif el.name == 'div' and 'heading' in (el.get('class') or []):
            current_marginal = clean(el.get_text(' ', strip=True))
        elif el.name == 'article':
            art_id = el.get('id')
            if not art_id or not art_id.startswith('art_'):
                continue
            a = ltr_by_id.get(art_id)
            if a is None:
                continue
            num, letter = art_num_from_id(art_id)
            if num is None or not (9 <= num <= 28):
                current_marginal = None
                continue
            if a['text'].strip() == '':
                # repealed article (empty body, footnote-only "Abrogé ...")
                repealed_skipped.append(art_display_num(a))
                current_marginal = None
                continue
            entry = {
                "num": art_display_num(a),
                "marginal_title": current_marginal,
                "url": f"{LTR_URL}#{art_id}",
                "text": a['text'],
                "words": a['words'],
            }
            current_section["articles"].append(entry)
            current_marginal = None

    # drop any accidental empty sections (shouldn't happen) and assign ids/paths
    def slugify(title):
        m = re.match(r'^(\d+)\.', title)
        n = m.group(1) if m else re.sub(r'\W+', '', title)[:6]
        return f"ltr-chap2-sec{n}"

    base_path = f"LTr > Chapitre II: {chapter_heading.split('. ', 1)[-1] if '. ' in chapter_heading else chapter_heading}" if False else None

    # Build the base path using the actual heading text captured (roman numeral chapter label as in the source)
    chapter_label = chapter_heading  # e.g. "III. Durée du travail et repos"
    base_path_str = f"LTr > {chapter_label}"

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0
    all_article_nums = []
    for sd in sections:
        if not sd["articles"]:
            continue
        sid = slugify(sd["title"])
        final_sections.append({
            "id": sid,
            "path": f"{base_path_str} > {sd['title']}",
            "title": sd["title"],
            "articles": sd["articles"],
        })
        for a in sd["articles"]:
            topic_articles_count += 1
            topic_words_count += a["words"]
            all_article_nums.append(a["num"])

    # ---- CO art. 321c section ----
    co321c = co_by_id.get('art_321_c')
    if co321c is None:
        raise SystemExit("MISSING art_321_c")
    co_entry = {
        "num": art_display_num(co321c),
        "marginal_title": None,
        "url": f"{CO_URL}#art_321_c",
        "text": co321c['text'],
        "words": co321c['words'],
    }
    co_section = {
        "id": "co-tit10-chap1-B-IV",
        "path": "CO > Titre dixième: Du contrat de travail > Chapitre premier: Du contrat individuel de travail > B. Obligations du travailleur > IV. Heures de travail supplémentaires",
        "title": "IV. Heures de travail supplémentaires",
        "articles": [co_entry],
    }
    final_sections.append(co_section)
    topic_articles_count += 1
    topic_words_count += co_entry["words"]
    all_article_nums.append(co_entry["num"])

    result = {
        "country": "CH",
        "source": f"{CO_URL} ; {LTR_URL} ; consolidated HTML via https://fedlex.data.admin.ch/filestore/... (CO état 1er janvier 2026; LTr état 1er septembre 2023)",
        "fetched_at": "2026-09-10",
        "topic": "Durée du travail et repos",
        "code_totals": {
            "co_titre10": co_titre10,
            "ltr": ltr_totals,
            "co_whole": co_whole,
            "note": code_totals_note,
            "olt1": olt1_totals,
        },
        "topic_totals": {
            "articles": topic_articles_count,
            "words": topic_words_count,
        },
        "sections": final_sections,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Wrote", OUT_PATH)
    print("chapter_label:", chapter_label)
    print("topic_articles_count", topic_articles_count)
    print("topic_words_count", topic_words_count)
    print("repealed_skipped:", repealed_skipped)
    print("sections:")
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])

if __name__ == "__main__":
    main()
