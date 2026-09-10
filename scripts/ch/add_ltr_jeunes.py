import json, re
from parse_co import load_soup, extract_article
from build_json_sante import display_num, LTR_URL, OUT_PATH

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"


def section_marginal_title(article_tag):
    """For LTr Chapitre IV articles, the marginal title is not inline in the
    article's <h6> (unlike LAA) but in a sibling <div class="heading"> that
    opens the enclosing <section>, e.g.:
      <section><div class="heading" ...>Age minimum</div>
        <div class="collapseable"><article id="art_30">...</article></div>
      </section>
    """
    collapseable = article_tag.parent
    section = collapseable.parent if collapseable is not None else None
    if section is None or section.name != 'section':
        return None
    heading = section.find('div', class_='heading', recursive=False)
    if heading is None:
        return None
    txt = heading.get_text(' ', strip=True)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt or None


def entry(soup, art_id, url_base):
    tag = soup.find('article', id=art_id)
    a = extract_article(tag)
    mt = section_marginal_title(tag)
    return {
        "num": display_num(a['num'], a['letter']),
        "marginal_title": mt,
        "url": f"{url_base}#{art_id}",
        "text": a["text"],
        "words": a["words"],
    }


def main():
    ltr_soup = load_soup(f"{SCRATCH}/ltr_20230901.html")

    # ---------------------------------------------------------------
    # LTr > Chapitre 4 (IV. Dispositions spéciales de protection) >
    # 1. Jeunes travailleurs -- art. 29-32. Confirmed against raw HTML:
    # art_29, art_30, art_31, art_32 all exist with real text; no lettered
    # variants (29a/30a/30b/31a/32a) exist in between; art_33 is titled
    # "Art. 33 et 34" (33/34 merged into a single article - not requested,
    # not included) and belongs to a different sub-topic anyway.
    # ---------------------------------------------------------------
    ltr_ids = ["art_29", "art_30", "art_31", "art_32"]
    missing = [i for i in ltr_ids if not ltr_soup.find('article', id=i)]
    lettered_checked = ["art_29_a", "art_30_a", "art_30_b", "art_31_a", "art_32_a"]
    lettered_found = [i for i in lettered_checked if ltr_soup.find('article', id=i)]

    articles = [entry(ltr_soup, i, LTR_URL) for i in ltr_ids]
    new_section = {
        "id": "ltr-chap4-jeunes-gens",
        "path": "LTr > Chapitre 4 > Jeunes travailleurs",
        "title": "Jeunes gens",
        "articles": articles,
    }

    with open(OUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    data["sections"].append(new_section)

    topic_articles = sum(len(s["articles"]) for s in data["sections"])
    topic_words = sum(a["words"] for s in data["sections"] for a in s["articles"])
    data["topic_totals"] = {"articles": topic_articles, "words": topic_words}

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Wrote", OUT_PATH)
    print("missing (should be empty):", missing)
    print("lettered variants found (should be empty):", lettered_found)
    print("new section articles:")
    for a in articles:
        print("   ", a["num"], "|", a["marginal_title"], "|", a["words"], "words")
    print("topic_totals:", data["topic_totals"])


if __name__ == "__main__":
    main()
