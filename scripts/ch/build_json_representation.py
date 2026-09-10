import json
from parse_co import load_soup, extract_article
from build_json_sante import marginal_title, display_num

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_representation.json"

# eli found via SPARQL (title search on jolux:Work / jolux:isRealizedBy / jolux:title,
# language FRA, CONTAINS "information et la consultation des travailleurs") ->
# https://fedlex.data.admin.ch/eli/cc/1994/1037_1037_1037 (RS 822.14).
# Latest consolidation found via jolux:isMemberOf on that work: 2011-01-01
# (dates found: 1994-05-01, 2000-08-01, 2004-04-01, 2011-01-01 -- no later one).
PARTICIPATION_URL = "https://www.fedlex.admin.ch/eli/cc/1994/1037_1037_1037/fr"
CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LTR_URL = "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr"


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
    part_soup = load_soup(f"{SCRATCH}/loiparticipation_20110101.html")
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    ltr_soup = load_soup(f"{SCRATCH}/ltr_20230901.html")

    # code_totals: copied verbatim from ch_sante.json (keeping olt3/opa as allowed).
    with open("/Users/joachimndoye/alleger-le-code/data/ch_sante.json", encoding="utf-8") as f:
        sante = json.load(f)
    code_totals = dict(sante["code_totals"])

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    # ---------------------------------------------------------------
    # Loi sur la participation (RS 822.14), all 16 articles, grouped by
    # the law's own "Section N ..." headings (confirmed in the raw HTML:
    # sec_1..sec_6, art_1 to art_16, no lettered/repealed articles).
    # ---------------------------------------------------------------
    part_section_defs = [
        ("sec_1", "Section 1 Dispositions générales", ["art_1", "art_2", "art_3", "art_4"]),
        ("sec_2", "Section 2 Représentation des travailleurs", ["art_5", "art_6", "art_7", "art_8"]),
        ("sec_3", "Section 3 Droits de participation", ["art_9", "art_10"]),
        ("sec_4", "Section 4 Collaboration", ["art_11", "art_12", "art_13", "art_14"]),
        ("sec_5", "Section 5 Organisation et procédure judiciaire", ["art_15"]),
        ("sec_6", "Section 6 Dispositions finales", ["art_16"]),
    ]
    missing_part = []
    for sec_id, heading, art_ids in part_section_defs:
        for i in art_ids:
            if not part_soup.find('article', id=i):
                missing_part.append(i)
        articles = [entry(part_soup, i, PARTICIPATION_URL) for i in art_ids]
        section = {
            "id": f"participation-{sec_id.replace('_', '-')}",
            "path": f"Loi sur la participation > {heading}",
            "title": heading.split(' ', 2)[-1] if heading.startswith('Section') else heading,
            "articles": articles,
        }
        final_sections.append(section)
        for a in articles:
            topic_articles_count += 1
            topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # CO > Titre dixième > Protection contre les congés (art. 336 only --
    # al. 2 let. b/c protects elected staff/workers' representatives
    # against abusive dismissal during / shortly after their mandate).
    # ---------------------------------------------------------------
    co_articles = [entry(co_soup, "art_336", CO_URL)]
    co_section = {
        "id": "co-tit10-protection-conges",
        "path": "CO > Titre dixième > Protection contre les congés",
        "title": "Protection contre les congés",
        "articles": co_articles,
    }
    final_sections.append(co_section)
    for a in co_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # LTr > Participation (art. 48). NOTE: the LTr has no chapter
    # literally titled "Participation" -- art. 48 (info./consultation on
    # santé / temps de travail / travail de nuit) sits under the raw
    # heading hierarchy "VI. Exécution de la loi > 3. Obligations des
    # employeurs et des travailleurs > Information et consultation".
    # Content confirms it is the correct/only participation article
    # (no other numbering candidate found; "participation" as a word does
    # not appear anywhere else in the LTr HTML). Kept path as instructed
    # ("LTr > Participation") and used the real heading as title.
    # ---------------------------------------------------------------
    ltr_articles = [entry(ltr_soup, "art_48", LTR_URL)]
    ltr_section = {
        "id": "ltr-participation",
        "path": "LTr > Participation",
        "title": "Information et consultation",
        "articles": ltr_articles,
    }
    final_sections.append(ltr_section)
    for a in ltr_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    result = {
        "country": "CH",
        "source": (
            f"{PARTICIPATION_URL} ; {CO_URL} ; {LTR_URL} ; "
            "consolidated HTML via https://fedlex.data.admin.ch/filestore/... "
            "(Loi sur la participation, RS 822.14, état 1er janvier 2011 -- latest "
            "consolidation on record; CO état 1er janvier 2026; LTr état 1er septembre 2023)"
        ),
        "fetched_at": "2026-09-10",
        "topic": "Représentation du personnel",
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
    print("missing_part:", missing_part)
    for sd in final_sections:
        print(" -", sd["path"], ":", [a["num"] for a in sd["articles"]])
        for a in sd["articles"]:
            print("    ", a["num"], "|", a["marginal_title"], "|", a["words"], "words")


if __name__ == "__main__":
    main()
