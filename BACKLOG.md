# Backlog — Alléger le Code

Une ligne par idée, bug ou tâche. Joachim ajoute ; Claude trie, découpe et distribue aux workers.
Statuts : `todo` · `doing` · `done` · `later` · `no` (avec la raison).
Une tâche prête pour un worker a un périmètre, un fichier de sortie et un critère de fin.

## Produit

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| P1 | done | Liens vers les documents cités + liste des sources | Chaque article a déjà son lien Légifrance/Fedlex. À faire : les références de chapitre (« L1233-1 → L1233-91 ») cliquables, section « Sources » complète avec dates d'état des textes. |
| P2 | done | Transparence : site apolitique, fait par un citoyen avec l'IA Claude | Une mention en tête et dans « Méthode et limites ». |
| P3 | todo | Le « Code allégé » consultable : la version finale simplifiée, lisible en langage simple, avec un lien en haut de page | Gros chantier de rédaction : un worker par sujet rédige les articles cibles (62 / 59 / 49…) à partir de la feuille de route, en langage courant, avec renvoi aux articles actuels remplacés. Relecture juridique nécessaire avant publication. |
| P4 | done (étape 1) | Export PDF / lecture hors ligne | Étape 1 faite : feuille de style d'impression + bouton « Télécharger · PDF » (impression navigateur, tous les textes dépliés). Étape 2 (`later`) : PDF généré au build pour téléchargement direct. |
| P5 | todo | Votes publics (Supabase) | `supabase/schema.sql` prêt ; il faut un projet Supabase actif (le connecteur actuel pointe vers un projet introuvable) et son URL + clé anon. |
| P6 | done | Déploiement public sur Vercel | https://alleger-le-code.vercel.app — déploiement automatique à chaque push sur `main` (repo github.com/angelstreet/alleger-le-code). Nom de domaine à choisir. |
| P7 | todo | Sujets suivants | Santé et sécurité · Représentation du personnel · Salaire · Formation du contrat, CDD, intérim · Apprentissage. Un couple de workers (FR + CH) par sujet, même schéma JSON. |
| P8 | later | Relecture par des juristes du travail | Chaque verdict doit être validé ou contesté par au moins une personne du métier avant l'envoi aux candidats. |
| P9 | later | Version anglaise | Après stabilisation du contenu français. |

## Bugs

| # | Statut | Quoi | Notes |
|---|--------|------|-------|
| B1 | done | Accents cassés en aperçu local | `<meta charset>` ajouté au template. |

## Convention pour les workers

Prompt autonome : contexte du projet, fichiers à lire (`scripts/`, `data/*.json`), schéma de sortie exact, critère de vérification (`python3 -m json.tool`, `python3 site/build.py` doit passer), rapport < 250 mots sans texte d'article.
