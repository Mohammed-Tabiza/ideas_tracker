# Plan de finalisation - Idea Lifecycle Tracker

## Objectif

Amener le repo du bootstrap backend actuel vers une v1 utilisable et conforme a `SPEC.md`, avec priorite sur la solidite du backend et une interface minimale mais complete.

## Etat actuel

- Phase 1 terminee : audit du code existant et comparaison avec `SPEC.md`
- Phase 2 terminee : formalisation du reste a faire et du plan de reprise
- Phase 3 et 4 terminees : backend v1 en place, prochaine etape = frontend et finition

## Phases

| Phase | Statut | Description |
|---|---|---|
| 1 | complete | Auditer le code et mesurer l'ecart avec la spec |
| 2 | complete | Produire le reste a faire priorise et la feuille de route |
| 3 | complete | Completer le schema SQLite et les primitives repository manquantes |
| 4 | complete | Implementer les endpoints backend v1 hors bootstrap |
| 5 | complete | Ajouter le frontend React/Vite prevu par la spec |
| 6 | complete | Ajouter les tests, la doc de lancement et la verification finale |

## Lots recommandes

### Lot A - Backend coeur

- Ajouter `idea_events`, `idea_links`, `ideas_fts`
- Implementer `GET /ideas/{id}`, `PUT /ideas/{id}`, `DELETE /ideas/{id}`
- Implementer `POST /ideas/{id}/transition`
- Implementer `GET /ideas/{id}/events`
- Implementer `GET /ideas/{id}/graph`
- Implementer `GET /search`

### Lot B - Regles metier

- Centraliser `ALLOWED_TRANSITIONS`
- Valider les obligations `comment`, `reason_code`, `revisit_at`
- Garantir `updated_at` a chaque ecriture liee a une idee
- Calculer `last_activity` via SQL et non via `updated_at` seul
- Rebuilder `ideas_fts` a chaque ecriture concernee

### Lot C - Frontend v1

- Initialiser le projet React/Vite
- Ecran capture rapide
- Liste des idees avec filtres et tri
- Fiche idee avec edition, timeline, liens et modal de transition
- Vue dashboard minimale

### Lot D - Qualite et livraison

- Tests API sur creation, listing, transitions, recherche
- Jeux de donnees de demo
- Scripts `start.bat` et `start.sh` pour lancer backend + frontend
- README aligne sur l'etat reel

## Etat de reprise

- Backend v1 API du chapitre 12 implemente
- Base SQLite et FTS5 du chapitre 13 implementees
- Tests API de base en place et passants
- Frontend React/Vite en place avec capture, liste, fiche idee, timeline, recherche et dashboard

## Risques a surveiller

- Derive de schema entre `ideas` et la spec si on continue sans couche service claire
- Mauvais calcul de `stale` tant que `last_activity` ne tient pas compte des events
- Recherche incoherente tant que FTS5 et rebuild applicatif ne sont pas en place
- Faux sentiment d'avancement tant que le frontend prevu par la spec n'existe pas

## Definition de fini v1

- Tous les endpoints du chapitre 12 sont disponibles
- Les regles de cycle de vie du chapitre 7 sont enforcees cote service
- Les tables et index du chapitre 13 existent
- Un frontend React/Vite permet les usages 14.1 a 14.6
- Le lancement local demarre backend et frontend comme indique au chapitre 16
- Les comportements sur les idees archivees suivent le chapitre 10
