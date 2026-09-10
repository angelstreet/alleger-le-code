import json, re
from parse_co import load_soup, get_all_articles, art_num_from_id, extract_article

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_conges.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LTR_URL = "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr"


def clean(txt):
    txt = txt.replace('\xa0', ' ').replace('­', '')
    txt = re.sub(r'\s+\d+$', '', txt.strip())  # strip trailing footnote-marker digits
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt


def strip_letter_prefix(txt):
    # "a.  Durée" -> "Durée"
    return re.sub(r'^[a-z]\.\s*', '', txt).strip()


def strip_number_prefix_footnote(txt):
    # keep leading "N. " but strip trailing footnote digits already done by clean()
    return txt


def main():
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    co_arts = {a['id']: a for a in get_all_articles(co_soup)}
    # article 329_g_bis is not matched by the standard num/letter regex; extract it directly
    art_gbis_tag = co_soup.find('article', id='art_329_g_bis')
    co_arts['art_329_g_bis'] = extract_article(art_gbis_tag)

    ltr_soup = load_soup(f"{SCRATCH}/ltr_20230901.html")
    ltr_arts = {a['id']: a for a in get_all_articles(ltr_soup)}

    # ---------------------------------------------------------------
    # code_totals: copied identically from ch_temps_travail.json
    # ---------------------------------------------------------------
    with open("/Users/joachimndoye/alleger-le-code/data/ch_temps_travail.json", encoding="utf-8") as f:
        temps = json.load(f)
    code_totals = temps["code_totals"]

    # ---------------------------------------------------------------
    # CO Titre dixième, C. Obligations de l'employeur, VIII. Congés et vacances
    # ---------------------------------------------------------------
    def co_display_num(art_id):
        # art_id like "art_329", "art_329_a", "art_329_g_bis"
        rest = art_id[len('art_'):]
        parts = rest.split('_')
        num = parts[0]
        suffix = ''.join(parts[1:])
        return f"Art. {num}{suffix}"

    def co_entry(art_id, marginal_title):
        a = co_arts[art_id]
        return {
            "num": co_display_num(art_id),
            "marginal_title": marginal_title,
            "url": f"{CO_URL}#{art_id}",
            "text": a["text"],
            "words": a["words"],
        }

    base_path_co = ("CO > Titre dixième: Du contrat de travail > Chapitre premier: "
                     "Du contrat individuel de travail > C. Obligations de l’employeur > "
                     "VIII. Congés et vacances")

    co_sections_def = [
        ("co-tit10-chap1-C-VIII-1", "1. Congés hebdomadaire et usuels",
         [("art_329", None)]),
        ("co-tit10-chap1-C-VIII-2", "2. Vacances",
         [("art_329_a", "Durée"),
          ("art_329_b", "Réduction"),
          ("art_329_c", "Continuité et date"),
          ("art_329_d", "Salaire")]),
        ("co-tit10-chap1-C-VIII-3", "3. Congé pour les activités de jeunesse extra-scolaires",
         [("art_329_e", None)]),
        ("co-tit10-chap1-C-VIII-4", "4. Congé de maternité",
         [("art_329_f", None)]),
        ("co-tit10-chap1-C-VIII-5", "5. Congé de l’autre parent",
         [("art_329_g", "En général"),
          ("art_329_g_bis", "En cas de décès de la mère")]),
        ("co-tit10-chap1-C-VIII-6", "6. Congé pour la prise en charge de proches",
         [("art_329_h", None)]),
        ("co-tit10-chap1-C-VIII-7",
         "7. Congé pour la prise en charge d’un enfant gravement atteint dans sa santé "
         "en raison d’une maladie ou d’un accident",
         [("art_329_i", None)]),
        ("co-tit10-chap1-C-VIII-8", "8. Congé d’adoption",
         [("art_329_j", None)]),
    ]

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    for sid, title, arts in co_sections_def:
        articles = [co_entry(art_id, mt) for art_id, mt in arts]
        final_sections.append({
            "id": sid,
            "path": f"{base_path_co} > {title}",
            "title": title,
            "articles": articles,
        })
        for a in articles:
            topic_articles_count += 1
            topic_words_count += a["words"]

    # verify expected CO articles all exist
    expected_co = ["art_329", "art_329_a", "art_329_b", "art_329_c", "art_329_d",
                    "art_329_e", "art_329_f", "art_329_g", "art_329_g_bis",
                    "art_329_h", "art_329_i", "art_329_j"]
    missing_co = [a for a in expected_co if a not in co_arts]
    if missing_co:
        raise SystemExit(f"MISSING CO articles: {missing_co}")
    # also confirm no art_329_k or beyond exists (i.e. 330 is next)
    extra = [k for k in co_arts if k.startswith('art_329_') and k not in expected_co]
    if extra:
        print("NOTE: extra art_329_* ids found beyond expected list:", extra)

    # ---------------------------------------------------------------
    # LTr > Protection spéciale (art. 35, 35a, 35b, 36, 36a)
    # ---------------------------------------------------------------
    def ltr_display_num(art_id):
        rest = art_id[len('art_'):]
        parts = rest.split('_')
        num = parts[0]
        suffix = ''.join(parts[1:])
        return f"Art. {num}{suffix}"

    def ltr_entry(art_id, marginal_title):
        a = ltr_arts[art_id]
        return {
            "num": ltr_display_num(art_id),
            "marginal_title": marginal_title,
            "url": f"{LTR_URL}#{art_id}",
            "text": a["text"],
            "words": a["words"],
        }

    ltr_articles_def = [
        ("art_35", "Protection de la santé durant la maternité"),
        ("art_35_a", "Occupation durant la maternité"),
        ("art_35_b", "Déplacement de l’horaire et paiement du salaire durant la maternité"),
        ("art_36", "Travailleurs ayant des responsabilités familiales"),
        ("art_36_a", "Autres catégories de travailleurs"),
    ]

    expected_ltr = ["art_35", "art_35_a", "art_35_b", "art_36", "art_36_a"]
    present_ltr = [a for a in expected_ltr if a in ltr_arts]
    missing_ltr_expected = [a for a in expected_ltr if a not in ltr_arts]
    # art_36_b is explicitly checked as it may or may not exist
    has_36b = "art_36_b" in ltr_arts
    if has_36b:
        ltr_articles_def.append(("art_36_b", None))

    ltr_articles = [ltr_entry(art_id, mt) for art_id, mt in ltr_articles_def]

    ltr_section = {
        "id": "ltr-protection-speciale",
        "path": "LTr > Protection spéciale",
        "title": "Protection spéciale",
        "articles": ltr_articles,
    }
    final_sections.append(ltr_section)
    for a in ltr_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    result = {
        "country": "CH",
        "source": f"{CO_URL} ; {LTR_URL} ; consolidated HTML via https://fedlex.data.admin.ch/filestore/... (CO état 1er janvier 2026; LTr état 1er septembre 2023)",
        "fetched_at": "2026-09-10",
        "topic": "Congés, vacances, maternité et paternité",
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
    print("missing_ltr_expected (of 35,35a,35b,36,36a):", missing_ltr_expected)
    print("art_36_b exists:", has_36b)
    print("sections:")
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])


if __name__ == "__main__":
    main()
