import json
import sys
sys.path.insert(0, '/Users/joachimndoye/alleger-le-code/scripts/ch')
from parse_co import load_soup, get_all_articles

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_salaire.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"


def main():
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    co_arts = {a['id']: a for a in get_all_articles(co_soup)}

    # code_totals: copied identically from ch_conges.json
    with open("/Users/joachimndoye/alleger-le-code/data/ch_conges.json", encoding="utf-8") as f:
        conges = json.load(f)
    code_totals = conges["code_totals"]

    def display_num(art_id):
        rest = art_id[len('art_'):]
        parts = rest.split('_')
        num = parts[0]
        suffix = ''.join(parts[1:])
        return f"Art. {num}{suffix}"

    def entry(art_id, marginal_title):
        a = co_arts[art_id]
        return {
            "num": display_num(art_id),
            "marginal_title": marginal_title,
            "url": f"{CO_URL}#{art_id}",
            "text": a["text"],
            "words": a["words"],
        }

    base_path = ("CO > Titre dixième: Du contrat de travail > Chapitre premier: "
                 "Du contrat individuel de travail > C. Obligations de l’employeur")

    # Verified against the Fedlex consolidated HTML (état 1er janvier 2026):
    # C. Obligations de l'employeur (NOT "B." as in older CO editions)
    #   I. Salaire
    #     1. Nature et montant en général -> art. 322
    #     2. Participation au résultat de l'exploitation -> art. 322a
    #     3. Provision
    #       a. Naissance du droit à la provision -> art. 322b
    #       b. Décompte -> art. 322c
    #     4. Gratification -> art. 322d
    #   II. Paiement du salaire
    #     1. Délais et terme de paiement -> art. 323
    #     2. Retenue sur le salaire -> art. 323a
    #     3. Garantie du salaire -> art. 323b
    #   III. Salaire en cas d'empêchement de travailler
    #     1. En cas de demeure de l'employeur -> art. 324
    #     2. En cas d'empêchement du travailleur
    #       a. Principe -> art. 324a
    #       b. Exceptions -> art. 324b
    #   IV. Cession et mise en gage de créances -> art. 325
    #   V. Travail aux pièces ou à la tâche
    #     1. Fourniture de travail -> art. 326
    #     2. Salaire -> art. 326a
    # VI. Instruments de travail, matériaux et frais (art. 327 ff.) is a DIFFERENT
    # topic (equipment/expense reimbursement), not part of the wage section, and is
    # excluded from scope.

    sections_def = [
        ("co-tit10-chap1-C-I-1", "I. Salaire > 1. Nature et montant en général",
         [("art_322", None)]),
        ("co-tit10-chap1-C-I-2", "I. Salaire > 2. Participation au résultat de l’exploitation",
         [("art_322_a", None)]),
        ("co-tit10-chap1-C-I-3", "I. Salaire > 3. Provision",
         [("art_322_b", "Naissance du droit à la provision"),
          ("art_322_c", "Décompte")]),
        ("co-tit10-chap1-C-I-4", "I. Salaire > 4. Gratification",
         [("art_322_d", None)]),
        ("co-tit10-chap1-C-II-1", "II. Paiement du salaire > 1. Délais et terme de paiement",
         [("art_323", None)]),
        ("co-tit10-chap1-C-II-2", "II. Paiement du salaire > 2. Retenue sur le salaire",
         [("art_323_a", None)]),
        ("co-tit10-chap1-C-II-3", "II. Paiement du salaire > 3. Garantie du salaire",
         [("art_323_b", None)]),
        ("co-tit10-chap1-C-III-1",
         "III. Salaire en cas d’empêchement de travailler > 1. En cas de demeure de l’employeur",
         [("art_324", None)]),
        ("co-tit10-chap1-C-III-2",
         "III. Salaire en cas d’empêchement de travailler > 2. En cas d’empêchement du travailleur",
         [("art_324_a", "Principe"),
          ("art_324_b", "Exceptions")]),
        ("co-tit10-chap1-C-IV", "IV. Cession et mise en gage de créances",
         [("art_325", None)]),
        ("co-tit10-chap1-C-V-1", "V. Travail aux pièces ou à la tâche > 1. Fourniture de travail",
         [("art_326", None)]),
        ("co-tit10-chap1-C-V-2", "V. Travail aux pièces ou à la tâche > 2. Salaire",
         [("art_326_a", None)]),
    ]

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    for sid, title, arts in sections_def:
        articles = [entry(art_id, mt) for art_id, mt in arts]
        final_sections.append({
            "id": sid,
            "path": f"{base_path} > {title}",
            "title": title,
            "articles": articles,
        })
        for a in articles:
            topic_articles_count += 1
            topic_words_count += a["words"]

    expected = ["art_322", "art_322_a", "art_322_b", "art_322_c", "art_322_d",
                "art_323", "art_323_a", "art_323_b",
                "art_324", "art_324_a", "art_324_b",
                "art_325", "art_326", "art_326_a"]
    missing = [a for a in expected if a not in co_arts]
    if missing:
        raise SystemExit(f"MISSING CO articles: {missing}")

    result = {
        "country": "CH",
        "source": f"{CO_URL} ; consolidated HTML via https://fedlex.data.admin.ch/filestore/... (CO état 1er janvier 2026)",
        "fetched_at": "2026-09-10",
        "topic": "Salaire",
        "code_totals": code_totals,
        "topic_totals": {
            "articles": topic_articles_count,
            "words": topic_words_count,
        },
        "context_notes": [
            "La Suisse ne connaît pas de salaire minimum fédéral. Des salaires minimums "
            "cantonaux existent dans certains cantons (Genève, Neuchâtel, Jura, Tessin, "
            "Bâle-Ville)."
        ],
        "sections": final_sections,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("Wrote", OUT_PATH)
    print("topic_articles_count:", topic_articles_count)
    print("topic_words_count:", topic_words_count)
    print("missing:", missing)
    print("sections:")
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])


if __name__ == "__main__":
    main()
