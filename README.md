# Idea Lifecycle Tracker (v1.3 - bootstrap)

Ce dossier contient un **nouveau squelette de repo** pour démarrer l'application décrite dans `SPEC.md`.

## Avancement actuel

L'application est en **phase backend v1** avec la base "ideas" en place.

Implémenté :

- `POST /ideas` (capture rapide)
- `GET /ideas` (filtres + tri)
- `GET /ideas/{id}` (lecture directe, y compris archivé)
- `PUT /ideas/{id}` (édition)
- `DELETE /ideas/{id}` (soft delete `archived = true`)
- tables `idea_events`, `idea_links`, `ideas_fts` initialisées côté SQLite
- calcul `last_activity` dans `GET /ideas` basé sur `ideas.updated_at` + derniers events

Non implémenté (prochain lot) :

- `POST /ideas/{id}/transition`
- `GET /ideas/{id}/events`
- `GET /ideas/{id}/graph`
- `GET /search`
- dashboard frontend

## Stack

- FastAPI
- sqlite3 natif
- SQLite local (`data/ideas.db`)

## Lancer

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
start.bat
```

API: <http://127.0.0.1:8000/docs>

## Endpoints

### `POST /ideas`

`title` est le seul champ obligatoire.

Defaults automatiques appliqués :

- `domain = OTHER`
- `source_type = INTUITION`
- `current_status = GERME`
- `archived = false`

### `GET /ideas`

Filtres supportés :

- `status`
- `domain`
- `tags=llm,infra`
- `stale=true` (basé sur `last_activity` > 30 jours)
- `revisit_before=YYYY-MM-DD`
- `include_archived=true`
- `sort=created_at|last_activity|estimated_value`
- `order=asc|desc`

### `GET /ideas/{id}`

Retourne une idée même si `archived = true`.

### `PUT /ideas/{id}`

Met à jour les champs enrichissables et met à jour `updated_at`.

### `DELETE /ideas/{id}`

Suppression logique : passe `archived=true`.

## Exemples

Création rapide :

```bash
curl -X POST http://127.0.0.1:8000/ideas \
  -H 'content-type: application/json' \
  -d '{"title":"Agentic architecture notebook"}'
```

Liste :

```bash
curl 'http://127.0.0.1:8000/ideas?sort=last_activity&order=desc'
```

Inclure les idées archivées :

```bash
curl 'http://127.0.0.1:8000/ideas?include_archived=true'
```
