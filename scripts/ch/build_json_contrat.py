import json, re
from parse_co import load_soup, get_all_articles, extract_article

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_contrat.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"


def main():
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    co_arts = {a['id']: a for a in get_all_articles(co_soup)}

    # ---------------------------------------------------------------
    # code_totals: copied identically from ch_conges.json
    # ---------------------------------------------------------------
    with open("/Users/joachimndoye/alleger-le-code/data/ch_conges.json", encoding="utf-8") as f:
        conges = json.load(f)
    code_totals = conges["code_totals"]

    def co_display_num(art_id):
        # art_id like "art_321_a" -> "Art. 321a"
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
                     "Du contrat individuel de travail")

    # (section_id, section_title, path_suffix, [(art_id, marginal_title), ...])
    co_sections_def = [
        ("co-tit10-chap1-A-I", "I. Définition",
         "A. Définition et formation > I. Définition",
         [("art_319", None)]),
        ("co-tit10-chap1-A-II", "II. Formation",
         "A. Définition et formation > II. Formation",
         [("art_320", None)]),

        ("co-tit10-chap1-B-I", "I. Travail personnel",
         "B. Obligations du travailleur > I. Travail personnel",
         [("art_321", None)]),
        ("co-tit10-chap1-B-II", "II. Diligence et fidélité à observer",
         "B. Obligations du travailleur > II. Diligence et fidélité à observer",
         [("art_321_a", None)]),
        ("co-tit10-chap1-B-III", "III. Obligation de rendre compte et de restituer",
         "B. Obligations du travailleur > III. Obligation de rendre compte et de restituer",
         [("art_321_b", None)]),
        ("co-tit10-chap1-B-IV", "IV. Heures de travail supplémentaires",
         "B. Obligations du travailleur > IV. Heures de travail supplémentaires",
         [("art_321_c", None)]),
        ("co-tit10-chap1-B-V", "V. Directives générales et instructions à observer",
         "B. Obligations du travailleur > V. Directives générales et instructions à observer",
         [("art_321_d", None)]),
        ("co-tit10-chap1-B-VI", "VI. Responsabilité du travailleur",
         "B. Obligations du travailleur > VI. Responsabilité du travailleur",
         [("art_321_e", None)]),

        ("co-tit10-chap1-C-III-2", "2. En cas d’empêchement du travailleur",
         "C. Obligations de l’employeur > III. Salaire en cas d’empêchement de travailler > "
         "2. En cas d’empêchement du travailleur",
         [("art_324_a", "Principe"),
          ("art_324_b", "Exceptions")]),

        ("co-tit10-chap1-C-V-1", "1. Fourniture de travail",
         "C. Obligations de l’employeur > V. Travail aux pièces ou à la tâche > 1. Fourniture de travail",
         [("art_326", None)]),
        ("co-tit10-chap1-C-V-2", "2. Salaire",
         "C. Obligations de l’employeur > V. Travail aux pièces ou à la tâche > 2. Salaire",
         [("art_326_a", None)]),

        ("co-tit10-chap1-C-VI-1", "1. Instruments de travail et matériaux",
         "C. Obligations de l’employeur > VI. Instruments de travail, matériaux et frais > "
         "1. Instruments de travail et matériaux",
         [("art_327", None)]),
        ("co-tit10-chap1-C-VI-2", "2. Frais",
         "C. Obligations de l’employeur > VI. Instruments de travail, matériaux et frais > 2. Frais",
         [("art_327_a", "En général"),
          ("art_327_b", "Véhicule à moteur"),
          ("art_327_c", "Échéance")]),

        ("co-tit10-chap1-C-VII-2", "2. Communauté domestique",
         "C. Obligations de l’employeur > VII. Protection de la personnalité du travailleur > "
         "2. Communauté domestique",
         [("art_328_a", None)]),
        ("co-tit10-chap1-C-VII-3", "3. Lors du traitement de données personnelles",
         "C. Obligations de l’employeur > VII. Protection de la personnalité du travailleur > "
         "3. Lors du traitement de données personnelles",
         [("art_328_b", None)]),

        ("co-tit10-chap1-C-IX-1", "1. Sûreté",
         "C. Obligations de l’employeur > IX. Autres obligations > 1. Sûreté",
         [("art_330", None)]),
        ("co-tit10-chap1-C-IX-2", "2. Certificat",
         "C. Obligations de l’employeur > IX. Autres obligations > 2. Certificat",
         [("art_330_a", None)]),
        ("co-tit10-chap1-C-IX-3", "3. Obligation d’informer",
         "C. Obligations de l’employeur > IX. Autres obligations > 3. Obligation d’informer",
         [("art_330_b", None)]),

        ("co-tit10-chap1-E", "E. Droit sur des inventions et des designs",
         "E. Droit sur des inventions et des designs",
         [("art_332", None),
          ("art_332_a", None)]),

        ("co-tit10-chap1-F-1", "1. Effets",
         "F. Transfert des rapports de travail > 1. Effets",
         [("art_333", None)]),
        ("co-tit10-chap1-F-2", "2. Consultation de la représentation des travailleurs",
         "F. Transfert des rapports de travail > 2. Consultation de la représentation des travailleurs",
         [("art_333_a", None)]),
        ("co-tit10-chap1-F-3", "3. Transfert d’entreprise pour cause d’insolvabilité",
         "F. Transfert des rapports de travail > 3. Transfert d’entreprise pour cause d’insolvabilité",
         [("art_333_b", None)]),

        ("co-tit10-chap1-temps-essai", "Temps d’essai",
         "G. Fin des rapports de travail > II. Contrat de durée indéterminée > 2. Délais de congé > "
         "b. Pendant le temps d’essai (extrait, art. 335b)",
         [("art_335_b", "Pendant le temps d’essai")]),
    ]

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    for sid, title, path_suffix, arts in co_sections_def:
        articles = [co_entry(art_id, mt) for art_id, mt in arts]
        final_sections.append({
            "id": sid,
            "path": f"{base_path_co} > {path_suffix}",
            "title": title,
            "articles": articles,
        })
        for a in articles:
            topic_articles_count += 1
            topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # verify expected CO articles all exist / report absent ones
    # ---------------------------------------------------------------
    expected_present = [
        "art_319", "art_320",
        "art_321", "art_321_a", "art_321_b", "art_321_c", "art_321_d", "art_321_e",
        "art_324_a", "art_324_b",
        "art_326", "art_326_a",
        "art_327", "art_327_a", "art_327_b", "art_327_c",
        "art_328_a", "art_328_b",
        "art_330", "art_330_a", "art_330_b",
        "art_332", "art_332_a",
        "art_333", "art_333_a", "art_333_b",
        "art_335_b",
    ]
    missing = [a for a in expected_present if a not in co_arts]
    if missing:
        raise SystemExit(f"MISSING CO articles: {missing}")

    checked_absent = ["art_320_a", "art_320_b", "art_326_b", "art_328_c", "art_330_c",
                       "art_332_b", "art_333_c"]
    confirmed_absent = [a for a in checked_absent if a not in co_arts]
    unexpectedly_present = [a for a in checked_absent if a in co_arts]

    result = {
        "country": "CH",
        "source": f"{CO_URL} ; consolidated HTML via https://fedlex.data.admin.ch/filestore/... "
                   f"(CO état 1er janvier 2026)",
        "fetched_at": "2026-09-10",
        "topic": "Contrat de travail : formation, exécution, maladie, transfert",
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
    print("missing (should be empty):", missing)
    print("confirmed_absent (checked, not present in CO):", confirmed_absent)
    print("unexpectedly_present (thought absent but exist!):", unexpectedly_present)
    print("sections:")
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])


if __name__ == "__main__":
    main()
