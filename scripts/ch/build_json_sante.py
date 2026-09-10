import json, re
from parse_co import load_soup, get_all_articles, extract_article

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_sante.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LTR_URL = "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr"
LAA_URL = "https://www.fedlex.admin.ch/eli/cc/1982/1676_1676_1676/fr"


def display_num(num, letter):
    return f"Art. {num}{letter or ''}"


def marginal_title(article_tag, num, letter):
    """Extract the marginal title from an <h6> that may have 1 or 2 direct <a> children:
    unlettered articles carry 'Art. N  Title' inside the single <a>; lettered articles
    (e.g. 82a) split it into a first <a> for 'Art. 82a' and a second <a> for the title."""
    h6 = article_tag.find('h6', recursive=False)
    if not h6:
        return None
    anchors = h6.find_all('a', recursive=False)
    if len(anchors) >= 2:
        txt = anchors[-1].get_text(' ', strip=True)
        txt = re.sub(r'\s+', ' ', txt).strip()
        return txt or None
    elif len(anchors) == 1:
        full = re.sub(r'\s+', ' ', anchors[0].get_text(' ', strip=True)).strip()
        prefix = f"Art. {num}"
        if full.startswith(prefix):
            rest = full[len(prefix):].strip()
            if letter and rest.startswith(letter):
                rest = rest[len(letter):].strip()
            return rest or None
        return None
    return None


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
    ltr_soup = load_soup(f"{SCRATCH}/ltr_20230901.html")
    laa_soup = load_soup(f"{SCRATCH}/laa_20260101.html")
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")

    olt3_soup = load_soup(f"{SCRATCH}/olt3_20240901.html")
    opa_soup = load_soup(f"{SCRATCH}/opa_20180501.html")

    # ---------------------------------------------------------------
    # code_totals: copied from ch_conges.json, plus olt3 / opa
    # ---------------------------------------------------------------
    with open("/Users/joachimndoye/alleger-le-code/data/ch_conges.json", encoding="utf-8") as f:
        conges = json.load(f)
    code_totals = dict(conges["code_totals"])

    olt3_arts = get_all_articles(olt3_soup)
    opa_arts = get_all_articles(opa_soup)
    code_totals["olt3"] = {
        "articles": len(olt3_arts),
        "words": sum(a["words"] for a in olt3_arts),
    }
    code_totals["opa"] = {
        "articles": len(opa_arts),
        "words": sum(a["words"] for a in opa_arts),
    }

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    # ---------------------------------------------------------------
    # LTr > Chapitre 2 > Protection de la santé et approbation des plans
    # Confirmed against raw HTML: chapter "II. Protection de la santé et
    # approbation des plans" runs from art. 6 to art. 8; art. 9 opens the
    # next chapter ("III. Durée du travail et repos"). No art. 6a exists.
    # ---------------------------------------------------------------
    ltr_ids = ["art_6", "art_7", "art_8"]
    missing_ltr = [i for i in ltr_ids if not ltr_soup.find('article', id=i)]
    has_6a = ltr_soup.find('article', id='art_6_a') is not None
    ltr_articles = [entry(ltr_soup, i, LTR_URL) for i in ltr_ids]
    ltr_section = {
        "id": "ltr-chap2-protection-sante",
        "path": "LTr > Chapitre 2 > Protection de la santé",
        "title": "Protection de la santé et approbation des plans",
        "articles": ltr_articles,
    }
    final_sections.append(ltr_section)
    for a in ltr_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # LAA > Titre 6 > Prévention des accidents et maladies professionnels
    # art. 81-88 inclusive, including lettered 82a and 87a.
    # ---------------------------------------------------------------
    laa_ids = ["art_81", "art_82", "art_82_a", "art_83", "art_84", "art_85",
               "art_86", "art_87", "art_87_a", "art_88"]
    missing_laa = [i for i in laa_ids if not laa_soup.find('article', id=i)]
    laa_articles = [entry(laa_soup, i, LAA_URL) for i in laa_ids]
    laa_section = {
        "id": "laa-titre6-prevention",
        "path": "LAA > Titre 6 > Prévention des accidents et maladies professionnels",
        "title": "Prévention des accidents et maladies professionnels",
        "articles": laa_articles,
    }
    final_sections.append(laa_section)
    for a in laa_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # CO > Titre dixième > Obligations de l'employeur > Protection de la
    # personnalité (art. 328 only)
    # ---------------------------------------------------------------
    co_articles = [entry(co_soup, "art_328", CO_URL)]
    co_section = {
        "id": "co-tit10-C-protection-personnalite",
        "path": "CO > Titre dixième > Obligations de l’employeur > Protection de la personnalité",
        "title": "Protection de la personnalité",
        "articles": co_articles,
    }
    final_sections.append(co_section)
    for a in co_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    result = {
        "country": "CH",
        "source": (
            f"{LTR_URL} ; {LAA_URL} ; {CO_URL} ; "
            "consolidated HTML via https://fedlex.data.admin.ch/filestore/... "
            "(LTr état 1er septembre 2023; LAA état 1er janvier 2026; CO état 1er janvier 2026; "
            "OLT 3 état 1er septembre 2024, context only; OPA état 1er mai 2018, context only)"
        ),
        "fetched_at": "2026-09-10",
        "topic": "Santé et sécurité : principes et obligations",
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
    print("missing_ltr (6,7,8):", missing_ltr)
    print("art_6a exists:", has_6a)
    print("missing_laa (81-88):", missing_laa)
    print("code_totals.olt3:", code_totals["olt3"])
    print("code_totals.opa:", code_totals["opa"])
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])
        for a in sd["articles"]:
            print("    ", a["num"], "|", a["marginal_title"], "|", a["words"], "words")


if __name__ == "__main__":
    main()
