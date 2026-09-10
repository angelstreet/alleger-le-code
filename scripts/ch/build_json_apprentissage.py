import json, re
from parse_co import load_soup, get_all_articles, extract_article
from build_json_sante import marginal_title, display_num

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_apprentissage.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LFPR_URL = "https://www.fedlex.admin.ch/eli/cc/2003/674/fr"


def entry(soup, art_id, url_base):
    tag = soup.find('article', id=art_id)
    a = extract_article(tag)
    mt = marginal_title(tag, a['num'], a['letter'])
    return {
        "num": display_num(a['num'], a['letter']),
        "marginal_title": mt,
        "url": f"{url_base}#{art_id}",
        "text": a["text"],
        "words": a["words"],
    }


def main():
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    lfpr_soup = load_soup(f"{SCRATCH}/lfpr_20250301.html")
    ofpr_soup = load_soup(f"{SCRATCH}/ofpr_20250301.html")

    # ---------------------------------------------------------------
    # code_totals: copied from ch_sante.json, plus lfpr / ofpr
    # ---------------------------------------------------------------
    with open("/Users/joachimndoye/alleger-le-code/data/ch_sante.json", encoding="utf-8") as f:
        sante = json.load(f)
    code_totals = dict(sante["code_totals"])

    lfpr_arts = get_all_articles(lfpr_soup)
    ofpr_arts = get_all_articles(ofpr_soup)
    code_totals["lfpr"] = {
        "articles": len(lfpr_arts),
        "words": sum(a["words"] for a in lfpr_arts),
    }
    code_totals["ofpr"] = {
        "articles": len(ofpr_arts),
        "words": sum(a["words"] for a in ofpr_arts),
    }

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    # ---------------------------------------------------------------
    # CO > Titre dixieme > Chapitre II > A. Du contrat d'apprentissage
    # Confirmed against raw HTML: section "A. Du contrat d'apprentissage"
    # runs from art. 344 to art. 346a inclusive; section "B. Du contrat
    # d'engagement des voyageurs de commerce" opens right after.
    # ---------------------------------------------------------------
    co_ids = ["art_344", "art_344_a", "art_345", "art_345_a", "art_346", "art_346_a"]
    missing_co = [i for i in co_ids if not co_soup.find('article', id=i)]
    co_articles = [entry(co_soup, i, CO_URL) for i in co_ids]
    co_section = {
        "id": "co-tit10-chap2-A-contrat-apprentissage",
        "path": "CO > Titre dixième > Chapitre II > A. Du contrat d’apprentissage",
        "title": "Du contrat d’apprentissage",
        "articles": co_articles,
    }
    final_sections.append(co_section)
    for a in co_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # LFPr > Chapitre 2 "Formation professionnelle initiale"
    # Confirmed against raw HTML: chapter runs art. 12-25, split into 5
    # sections. No lettered/repealed articles in this chapter.
    # ---------------------------------------------------------------
    lfpr_chapter2_sections = [
        ("lfpr-chap2-sec1-dispositions-generales", "Section 1 Dispositions générales",
         ["art_12", "art_13", "art_14"]),
        ("lfpr-chap2-sec2-structure", "Section 2 Structure",
         ["art_15", "art_16", "art_17", "art_18", "art_19"]),
        ("lfpr-chap2-sec3-prestataires", "Section 3 Prestataires",
         ["art_20", "art_21", "art_22", "art_23"]),
        ("lfpr-chap2-sec4-surveillance", "Section 4 Surveillance",
         ["art_24"]),
        ("lfpr-chap2-sec5-maturite-pro-federale", "Section 5 Maturité professionnelle fédérale",
         ["art_25"]),
    ]

    missing_lfpr = []
    for sec_id, sec_title, ids in lfpr_chapter2_sections:
        missing_lfpr += [i for i in ids if not lfpr_soup.find('article', id=i)]
        articles = [entry(lfpr_soup, i, LFPR_URL) for i in ids]
        section = {
            "id": sec_id,
            "path": f"LFPr > Chapitre 2 > {sec_title}",
            "title": sec_title,
            "articles": articles,
        }
        final_sections.append(section)
        for a in articles:
            topic_articles_count += 1
            topic_words_count += a["words"]

    result = {
        "country": "CH",
        "source": (
            f"{CO_URL} ; {LFPR_URL} ; "
            "consolidated HTML via https://fedlex.data.admin.ch/filestore/... "
            "(CO état 1er janvier 2026; LFPr [RS 412.10] état 1er mars 2025; "
            "OFPr [RS 412.101] état 1er mars 2025, context only)"
        ),
        "fetched_at": "2026-09-10",
        "topic": "Apprentissage",
        "code_totals": code_totals,
        "topic_totals": {
            "articles": topic_articles_count,
            "words": topic_words_count,
        },
        "sections": final_sections,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Wrote", OUT_PATH)
    print("topic_articles_count:", topic_articles_count)
    print("topic_words_count:", topic_words_count)
    print("missing_co:", missing_co)
    print("missing_lfpr:", missing_lfpr)
    print("code_totals.lfpr:", code_totals["lfpr"])
    print("code_totals.ofpr:", code_totals["ofpr"])
    for sd in final_sections:
        print(" -", sd["path"], ":", [a["num"] for a in sd["articles"]])
        for a in sd["articles"]:
            print("    ", a["num"], "|", a["marginal_title"], "|", a["words"], "words")


if __name__ == "__main__":
    main()
