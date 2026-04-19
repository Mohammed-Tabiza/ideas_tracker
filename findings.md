# Findings - Audit spec vs code

## Synthese

Le repo n'est pas une application v1 incomplete au sens "quelques finitions manquent". C'est un bootstrap backend qui couvre volontairement une petite partie de la spec : `POST /ideas` et `GET /ideas`.

## Ce qui existe

- Backend FastAPI minimal dans `app/main.py`
- Schema Pydantic de creation et reponse dans `app/schemas.py`
- Acces SQLite natif dans `app/db.py`
- Repository avec creation et listing dans `app/repository.py`
- Scripts de lancement backend seuls dans `start.bat` et `start.sh`

## Mise a jour apres implementation backend

- Endpoints disponibles : creation, listing, detail, edition, archivage, transition, events, graph, recherche
- Tables disponibles : `ideas`, `idea_events`, `idea_links`, `ideas_fts`
- Regles de transition principales implementees dans `app/services.py`
- Recherche FTS5 et calcul SQL de `last_activity` en place
- Tests automatises : parcours creation, transition, archivage, recherche

## Ecarts majeurs par rapport a la spec

### Backend API

- Le backend API v1 du chapitre 12 est maintenant couvert
- Une API d'ecriture minimale pour `IdeaLink` existe maintenant : creation et suppression

### Base de donnees

- Le schema principal de la spec est maintenant present
- Il n'y a toujours pas de mecanisme de migration de schema au-dela du `CREATE IF NOT EXISTS`

### Regles metier

- `last_activity` est maintenant calcule avec les events
- Les transitions et obligations principales sont enforcees
- `updated_at` est mis a jour sur edition, transition et archivage
- `updated_at` est aussi mis a jour sur l'idee source lors de creation/suppression d'un `IdeaLink`
- Il n'existe pas encore d'endpoint NOTE, meme si le type d'event est modele

### Frontend

- Projet React/Vite present
- UI v1 disponible : capture, filtres, recherche, detail, transition, timeline, dashboard
- Les scripts de lancement demarrent maintenant backend et frontend

### Qualite

- Des tests backend existent maintenant, mais la couverture reste partielle
- Un jeu de donnees de demonstration est injecte automatiquement si la base est vide
- README aligne sur l'etat reel du projet

## Dette technique implicite

- Pas de separation nette `router -> service -> repository`, ce qui rendra les validations de cycle de vie plus fragiles si on continue dans `repository.py` seul
- Pas de migrations : `init_db()` devra evoluer proprement ou etre remplace par une strategie idempotente plus robuste
- Les tags sont stockes en JSON texte, ce qui est acceptable pour SQLite local mais devra etre traite avec soin dans les filtres et mises a jour

## Ordre de reprise recommande

1. Stabiliser le modele SQLite et les primitives repository
2. Ajouter une couche service pour les transitions et les mises a jour
3. Completer tous les endpoints backend v1
4. Ajouter les tests API
5. Construire le frontend React/Vite conforme aux usages de la spec
6. Finaliser les scripts de lancement et la documentation
