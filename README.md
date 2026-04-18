# Idea Lifecycle Tracker (v1.3 - bootstrap)

Ce dossier contient un **nouveau squelette de repo** pour démarrer l'application décrite dans `SPEC.md`.

## Portée implémentée (règle §1)

Conformément à la règle d'implémentation prioritaire, cette version implémente uniquement :

- `POST /ideas`
- `GET /ideas`

## Stack

- FastAPI
- sqlite3 natif
- SQLite local (`data/ideas.db`)

## Lancer

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

API: <http://127.0.0.1:8000/docs>

## Exemples

Création rapide :

```bash
curl -X POST http://127.0.0.1:8000/ideas \
  -H 'content-type: application/json' \
  -d '{"title":"Agentic architecture notebook"}'
```

Liste :

```bash
curl 'http://127.0.0.1:8000/ideas'
```

Inclure les idées archivées :

```bash
curl 'http://127.0.0.1:8000/ideas?include_archived=true'
```
