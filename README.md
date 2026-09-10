# Code du travail simplifié

Projet « Alléger le Code » — mêmes droits, moins de texte. En ligne : https://codedutravailsimplifie.com

Le Code du travail français comparé, sujet par sujet et à périmètre égal, au droit du travail suisse — avec une feuille de route de simplification : ce qu'on garde, ce qu'on simplifie, ce qu'on délègue aux branches, ce qu'on supprime, ce qu'on ajoute.

Site indépendant et apolitique, réalisé par un citoyen avec l'IA Claude (Anthropic). Aucun parti, syndicat, organisation patronale ni financement. Les verdicts sont une proposition ouverte à la critique, pas une expertise juridique validée.

## Ce que ça mesure

Le nombre d'articles en vigueur et de mots que doivent lire un employeur et un salarié pour appliquer la loi sur un même sujet. Pas la qualité de la protection : un droit court peut être complexe par ses juges, un droit long simple à appliquer.

| Sujet | France (articles) | Suisse (articles) |
|---|---|---|
| Licenciement | 356 | 29 |
| Temps de travail et repos | 301 | 26 |
| Congés, maternité, paternité | 433 | 17 |

## Contact

ndoye.joachim@gmail.com — remarques, corrections et relectures juridiques bienvenues.

## Sources

- France : [Légifrance](https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006072050), données [LEGI](https://www.data.gouv.fr/datasets/legi-codes-lois-et-reglements-consolides) (DILA) via le paquet [@socialgouv/legi-data](https://github.com/SocialGouv/legi-data). Articles en vigueur, parties législative (L) et réglementaire (R, D).
- Suisse : [Fedlex](https://www.fedlex.admin.ch/) — Code des obligations (RS 220, état au 1er janvier 2026), Loi sur le travail (RS 822.11, état au 1er septembre 2023).

## Structure

```
data/       JSON extraits, un fichier par pays et par sujet (texte intégral des articles, comptes)
scripts/    extracteurs FR (legi-data) et CH (Fedlex filestore + SPARQL)
site/       template.html + build.py → index.html (site statique, une page)
supabase/   schéma des votes « Je soutiens » pour la version publique
BACKLOG.md  idées, bugs, tâches à distribuer
```

## Reconstruire le site

```bash
python3 site/build.py
```

`build.py` vérifie que la somme des lignes de chaque sujet égale exactement les totaux extraits. Pour activer les votes publics : exporter `SUPABASE_URL` et `SUPABASE_ANON_KEY` avant le build, après avoir exécuté `supabase/schema.sql`.

## Ajouter un sujet

1. Extraire le côté français (`scripts/fr/`) et le côté suisse (`scripts/ch/`) dans `data/` avec le même schéma que les fichiers existants.
2. Déclarer le sujet et ses questions dans `site/build.py` (comptes par chapitre ou par section, articles cités, verdict, cible, plan).
3. `python3 site/build.py` doit passer sans assertion.
