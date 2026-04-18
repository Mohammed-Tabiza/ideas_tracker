# Idea Lifecycle Tracker (v1.3 - bootstrap)

Ce dossier contient un **nouveau squelette de repo** pour démarrer l'application décrite dans `SPEC.md`.

## Portée implémentée (règle §1)

Conformément à la règle d'implémentation prioritaire, cette version implémente uniquement :

- `POST /ideas`
- `GET /ideas`

Aucun endpoint de timeline, dashboard, scoring ou transition n'est ajouté dans ce lot.

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
- `stale=true` (basé sur `updated_at` > 30 jours)
- `revisit_before=YYYY-MM-DD`
- `include_archived=true`
- `sort=created_at|last_activity|estimated_value`
- `order=asc|desc`

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
