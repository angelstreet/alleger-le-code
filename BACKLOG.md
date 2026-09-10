# Backlog — Alléger le Code

Une ligne par idée, bug ou tâche. Joachim ajoute ; Claude trie, découpe et distribue aux workers.
Statuts : `todo` · `doing` · `done` · `later` · `no` (avec la raison).
Une tâche prête pour un worker a un périmètre, un fichier de sortie et un critère de fin.

## Produit

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| P1 | done | Liens vers les documents cités + liste des sources | Chaque article a déjà son lien Légifrance/Fedlex. À faire : les références de chapitre (« L1233-1 → L1233-91 ») cliquables, section « Sources » complète avec dates d'état des textes. |
| P2 | done | Transparence : site apolitique, fait par un citoyen avec l'IA Claude | Une mention en tête et dans « Méthode et limites ». |
| P3 | done | Le « Code allégé » consultable : la version finale simplifiée, lisible en langage simple, avec un lien en haut de page | Neuf sujets rédigés : 346 articles proposés pour 2 914 actuels, chaque article tracé (2 571 remplacés + 343 supprimés/transférés, avec raison). Section « Le Code allégé » + lien en tête + lien depuis chaque carte de la feuille de route. Statut affiché : brouillon à relire. |
| P4 | done | Export PDF / lecture hors ligne | PDF généré au build par Chrome headless (`site/alleger-le-code.pdf`, ~116 pages, tous les sujets et textes dépliés) ; les boutons « Télécharger · PDF » lʼouvrent quand il est servi à côté de la page, sinon impression navigateur. |
| P5 | todo | Votes publics (Supabase) | `supabase/schema.sql` prêt ; il faut un projet Supabase actif (le connecteur actuel pointe vers un projet introuvable) et son URL + clé anon. |
| P6 | done | Déploiement public sur Vercel | https://alleger-le-code.vercel.app — déploiement automatique à chaque push sur `main` (repo github.com/angelstreet/alleger-le-code). Nom de domaine à choisir. |
| P7 | done | Sujets suivants | Neuf sujets couverts : licenciement, temps de travail, congés, santé-sécurité (Livre Ier), représentation du personnel, salaire, contrat de travail, CDD-intérim, apprentissage — 2 914 articles FR vs 181 CH. Sujets possibles ensuite : négociation collective et syndicats, formation professionnelle, égalité-discriminations, inspection et sanctions. |
| P8 | todo | Relecture par des juristes du travail | Chaque verdict et chaque article du Code allégé doit être validé ou contesté par au moins une personne du métier avant l'envoi aux candidats. Points déjà repérés à relire : congés payés recomptés en jours ouvrés (25/an) ; protection après mandat des salariés protégés unifiée à douze mois ; grille de rémunération des apprentis renvoyée à un décret unique ; C2P et AGS transférés hors du Code. |
| P9 | later | Version anglaise | Après stabilisation du contenu français. |
| P10 | todo | Poids de la page | index.html ≈ 900 Ko (textes des articles + Code allégé embarqués). Charger les textes et le Code allégé à la demande (JSON séparés) pour la version Vercel ; garder une version tout-en-un pour l'artefact et le PDF. |
| P11 | later | Sujets suivants | Négociation collective et syndicats · formation professionnelle · égalité et discriminations · inspection et sanctions · Outre-mer. |

## Bugs

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| B1 | done | Accents cassés en aperçu local | `<meta charset>` ajouté au template. |

## Convention pour les workers

Prompt autonome : contexte du projet, fichiers à lire (`scripts/`, `data/*.json`), schéma de sortie exact, critère de vérification (`python3 -m json.tool`, `python3 site/build.py` doit passer), rapport < 250 mots sans texte d'article.
