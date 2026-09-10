import json, re
from parse_co import load_soup, get_all_articles, extract_article

SCRATCH = "/private/tmp/claude-501/-Users-joachimndoye-Library-Application-Support-Claude-scratch-workspaces-b3470433-b0fd-4a2f-a65b-cb0c29e8bfa6-f4376b92-1b81-43b2-9c5f-059506ff32d8-scratch-2026-09-10-54498a/f19149da-59bb-4aad-af75-0f42365d23a9/scratchpad"
OUT_PATH = "/Users/joachimndoye/alleger-le-code/data/ch_cdd.json"

CO_URL = "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr"
LSE_URL = "https://www.fedlex.admin.ch/eli/cc/1991/392_392_392/fr"


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
            # strip a leading footnote-reference number left over from the anchor text
            # (e.g. "8 Conventions collectives..." -> "Conventions collectives...")
            rest = re.sub(r'^\d+\s+', '', rest)
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
    co_soup = load_soup(f"{SCRATCH}/co_20260101.html")
    lse_soup = load_soup(f"{SCRATCH}/lse_20260101.html")
    ose_soup = load_soup(f"{SCRATCH}/ose_20240801.html")

    # ---------------------------------------------------------------
    # code_totals: copied from ch_sante.json, plus olse (OSE, context only)
    # ---------------------------------------------------------------
    with open("/Users/joachimndoye/alleger-le-code/data/ch_sante.json", encoding="utf-8") as f:
        sante = json.load(f)
    code_totals = dict(sante["code_totals"])

    ose_arts = get_all_articles(ose_soup)
    code_totals["olse"] = {
        "articles": len(ose_arts),
        "words": sum(a["words"] for a in ose_arts),
    }

    final_sections = []
    topic_articles_count = 0
    topic_words_count = 0

    # ---------------------------------------------------------------
    # CO > Titre dixième > Fin des rapports de travail > Contrat de durée
    # déterminée (section G/I). Confirmed against raw HTML: this section
    # holds only art. 334; section G/II "Contrat de durée indéterminée"
    # follows immediately after.
    # ---------------------------------------------------------------
    co_ids = ["art_334"]
    missing_co = [i for i in co_ids if not co_soup.find('article', id=i)]
    co_articles = [entry(co_soup, i, CO_URL) for i in co_ids]
    co_section = {
        "id": "co-tit10-G-I-cdd",
        "path": "CO > Titre dixième > Fin des rapports de travail > Contrat de durée déterminée",
        "title": "Contrat de durée déterminée",
        "articles": co_articles,
    }
    final_sections.append(co_section)
    for a in co_articles:
        topic_articles_count += 1
        topic_words_count += a["words"]

    # ---------------------------------------------------------------
    # LSE > Chapitre 3 "Location de services" (art. 12-23), split by its
    # three sections. Confirmed against raw HTML:
    #   Section 1 "Activités soumises à l'autorisation" -> art. 12-17
    #   Section 2 "Activités de location de services"   -> art. 18-22
    #   Section 3 "..." -> art. 23, which is REPEALED (abrogé par
    #     l'annexe 1 ch. II 28 du CPC du 19 déc. 2008, effet 1er janv.
    #     2011); its section heading text itself now reads literally
    #     "Section 3 ..." in the consolidated Fedlex HTML because the
    #     title was struck along with the sole article it contained
    #     (originally the "Garantie" provision, moved to the CPC).
    #     No lettered sub-articles (18a/19a etc.) exist in this chapter
    #     in the état 1er janvier 2026 consolidation.
    # ---------------------------------------------------------------
    lse_sections_def = [
        ("lse-chap3-sec1-autorisation", "Section 1 Activités soumises à l’autorisation",
         ["art_12", "art_13", "art_14", "art_15", "art_16", "art_17"]),
        ("lse-chap3-sec2-activites", "Section 2 Activités de location de services",
         ["art_18", "art_19", "art_20", "art_21", "art_22"]),
    ]
    missing_lse = []
    repealed_lse = []

    for sec_id, sec_title, ids in lse_sections_def:
        missing_lse += [i for i in ids if not lse_soup.find('article', id=i)]
        arts = [entry(lse_soup, i, LSE_URL) for i in ids]
        sec = {
            "id": sec_id,
            "path": f"LSE > Chapitre 3 > {sec_title}",
            "title": sec_title,
            "articles": arts,
        }
        final_sections.append(sec)
        for a in arts:
            topic_articles_count += 1
            topic_words_count += a["words"]

    # Section 3 (art. 23) is fully repealed (no text) -> excluded from
    # sections, listed separately.
    art23_tag = lse_soup.find('article', id='art_23')
    if art23_tag is not None:
        a23 = extract_article(art23_tag)
        if a23["words"] == 0:
            repealed_lse.append("Art. 23 (Section 3, LSE, Chapitre 3) - abrogé par l’annexe 1 ch. II 28 du "
                                 "CPC du 19 déc. 2008, avec effet au 1er janv. 2011 (RO 2010 1739)")

    result = {
        "country": "CH",
        "source": (
            f"{CO_URL} ; {LSE_URL} ; "
            "consolidated HTML via https://fedlex.data.admin.ch/filestore/... "
            "(CO état 1er janvier 2026; LSE, RS 823.11, état 1er janvier 2026; "
            "OSE, RS 823.111, état 1er août 2024, context only)"
        ),
        "fetched_at": "2026-09-10",
        "topic": "CDD et location de services",
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
    print("missing_lse:", missing_lse)
    print("repealed_lse:", repealed_lse)
    print("code_totals.olse:", code_totals["olse"])
    for sd in final_sections:
        print(" -", sd["title"], ":", [a["num"] for a in sd["articles"]])
        for a in sd["articles"]:
            print("    ", a["num"], "|", a["marginal_title"], "|", a["words"], "words")


if __name__ == "__main__":
    main()
