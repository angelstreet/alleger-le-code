import json
from parse_co import load_soup, get_all_articles

OUT_PATH = "/Users/joachimndoye/Library/Application Support/Claude/scratch-workspaces/b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6/f4376b92-1b81-43b2-9c5f-059506ff32d8/scratch-2026-09-10-54498a/data/ch_licenciement.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LTR_URL = "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr"

def art_display_num(a):
    return f"Art. {a['num']}{a['letter']}"

def art_url(a):
    return f"{CO_URL}#{a['id']}"

def main():
    co_soup = load_soup('co_20260101.html')
    co_arts = get_all_articles(co_soup)
    co_by_id = {a['id']: a for a in co_arts}

    ltr_soup = load_soup('ltr_20230901.html')
    ltr_arts = get_all_articles(ltr_soup)

    # ---- code_totals ----
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

    # ---- sections for the termination topic (art. 334 - 339c) ----
    section_defs = [
        {
            "id": "co-tit10-chap1-G-I",
            "title": "I. Contrat de durée déterminée",
            "path_suffix": "I. Contrat de durée déterminée",
            "ids": ["art_334"],
        },
        {
            "id": "co-tit10-chap1-G-II-1",
            "title": "II. Contrat de durée indéterminée – 1. Congé en général",
            "path_suffix": "II. Contrat de durée indéterminée > 1. Congé en général",
            "ids": ["art_335"],
        },
        {
            "id": "co-tit10-chap1-G-II-2",
            "title": "II. Contrat de durée indéterminée – 2. Délais de congé",
            "path_suffix": "II. Contrat de durée indéterminée > 2. Délais de congé",
            "ids": ["art_335_a", "art_335_b", "art_335_c"],
        },
        {
            "id": "co-tit10-chap1-G-IIbis",
            "title": "II bis. Licenciement collectif",
            "path_suffix": "II bis. Licenciement collectif",
            "ids": ["art_335_d", "art_335_e", "art_335_f", "art_335_g", "art_335_h",
                    "art_335_i", "art_335_j", "art_335_k"],
        },
        {
            "id": "co-tit10-chap1-G-III",
            "title": "III. Protection contre les congés",
            "path_suffix": "III. Protection contre les congés",
            "ids": ["art_336", "art_336_a", "art_336_b", "art_336_c", "art_336_d"],
        },
        {
            "id": "co-tit10-chap1-G-IV",
            "title": "IV. Résiliation immédiate",
            "path_suffix": "IV. Résiliation immédiate",
            "ids": ["art_337", "art_337_a", "art_337_b", "art_337_c", "art_337_d"],
        },
        {
            "id": "co-tit10-chap1-G-V",
            "title": "V. Décès du travailleur ou de l’employeur",
            "path_suffix": "V. Décès du travailleur ou de l’employeur",
            "ids": ["art_338", "art_338_a"],
        },
        {
            "id": "co-tit10-chap1-G-VI",
            "title": "VI. Conséquences de la fin du contrat",
            "path_suffix": "VI. Conséquences de la fin du contrat",
            "ids": ["art_339", "art_339_a", "art_339_b", "art_339_c"],
        },
    ]

    base_path = "CO > Titre dixième: Du contrat de travail > Chapitre premier: Du contrat individuel de travail > G. Fin des rapports de travail"

    sections = []
    topic_articles_count = 0
    topic_words_count = 0
    all_article_nums = []
    for sd in section_defs:
        arts_out = []
        for aid in sd["ids"]:
            a = co_by_id.get(aid)
            if a is None:
                raise SystemExit(f"MISSING ARTICLE: {aid}")
            entry = {
                "num": art_display_num(a),
                "marginal_title": None,
                "url": art_url(a),
                "text": a["text"],
                "words": a["words"],
            }
            arts_out.append(entry)
            topic_articles_count += 1
            topic_words_count += a["words"]
            all_article_nums.append(art_display_num(a))
        sections.append({
            "id": sd["id"],
            "path": f"{base_path} > {sd['path_suffix']}",
            "title": sd["title"],
            "articles": arts_out,
        })

    result = {
        "country": "CH",
        "source": f"{CO_URL} ; {LTR_URL} ; consolidated HTML via https://fedlex.data.admin.ch/filestore/... (CO état 1er janvier 2026; LTr état 1er septembre 2023)",
        "fetched_at": "2026-09-10",
        "topic": "Fin des rapports de travail (résiliation)",
        "code_totals": {
            "co_titre10": co_titre10,
            "ltr": ltr_totals,
            "co_whole": co_whole,
            "note": "Counts are per <article> element in the Fedlex consolidated HTML (fr), including lettered sub-articles (e.g. 335a) and a handful of jointly-repealed article ranges (e.g. 'art. 226a–226d') that count as one element each. Words = whitespace-separated tokens of the plain article text (footnote markers/footnotes excluded). CO whole = art. 1–1186 (Livre cinquième du Code civil suisse), état 1er janvier 2026. LTr = RS 822.11, état 1er septembre 2023.",
        },
        "topic_totals": {
            "articles": topic_articles_count,
            "words": topic_words_count,
        },
        "sections": sections,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Wrote", OUT_PATH)
    print("topic_articles_count", topic_articles_count)
    print("topic_words_count", topic_words_count)
    print("article list:", all_article_nums)

if __name__ == "__main__":
    main()
