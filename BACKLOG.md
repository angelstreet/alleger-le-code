# Backlog — Alléger le Code

Une ligne par idée, bug ou tâche. Joachim ajoute ; Claude trie, découpe et distribue aux workers.
Statuts : `todo` · `doing` · `done` · `later` · `no` (avec la raison).
Une tâche prête pour un worker a un périmètre, un fichier de sortie et un critère de fin.

## Produit

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| P1 | done | Liens vers les documents cités + liste des sources | Chaque article a déjà son lien Légifrance/Fedlex. À faire : les références de chapitre (« L1233-1 → L1233-91 ») cliquables, section « Sources » complète avec dates d'état des textes. |
| P2 | done | Transparence : site apolitique, fait par un citoyen avec l'IA Claude | Une mention en tête et dans « Méthode et limites ». |
| P3 | doing | Le « Code allégé » consultable : la version finale simplifiée, lisible en langage simple, avec un lien en haut de page | Pilote fait pour le licenciement : 62 articles, 5 205 mots (contre 31 644), 356/356 articles actuels tracés (remplacés ou supprimés). Section « Le Code allégé » + lien en tête. Restent à rédiger : temps de travail (59), congés (49), santé (21). Relecture juridique nécessaire avant toute diffusion. |
| P4 | done | Export PDF / lecture hors ligne | PDF généré au build par Chrome headless (`site/alleger-le-code.pdf`, ~116 pages, tous les sujets et textes dépliés) ; les boutons « Télécharger · PDF » lʼouvrent quand il est servi à côté de la page, sinon impression navigateur. |
| P5 | todo | Votes publics (Supabase) | `supabase/schema.sql` prêt ; il faut un projet Supabase actif (le connecteur actuel pointe vers un projet introuvable) et son URL + clé anon. |
| P6 | done | Déploiement public sur Vercel | https://alleger-le-code.vercel.app — déploiement automatique à chaque push sur `main` (repo github.com/angelstreet/alleger-le-code). Nom de domaine à choisir. |
| P7 | doing | Sujets suivants | Fait : santé et sécurité (Livre Ier, 267 vs 18). Restent : représentation du personnel · salaire · formation du contrat, CDD, intérim · apprentissage. Un couple de workers (FR + CH) par sujet, même schéma JSON. |
| P8 | later | Relecture par des juristes du travail | Chaque verdict doit être validé ou contesté par au moins une personne du métier avant l'envoi aux candidats. |
| P9 | later | Version anglaise | Après stabilisation du contenu français. |

## Bugs

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| B1 | done | Accents cassés en aperçu local | `<meta charset>` ajouté au template. |

## Convention pour les workers

Prompt autonome : contexte du projet, fichiers à lire (`scripts/`, `data/*.json`), schéma de sortie exact, critère de vérification (`python3 -m json.tool`, `python3 site/build.py` doit passer), rapport < 250 mots sans texte d'article.
