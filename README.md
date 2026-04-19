# Idea Lifecycle Tracker (v1.3)

Application locale solo pour capturer, suivre et reactiver des idees autour de l'IA, de l'architecture et de la strategie technique.

## Ce qui est livre

- backend FastAPI avec SQLite + FTS5
- frontend React 18 + Vite
- capture rapide d'idees
- liste filtree avec recherche full-text
- fiche idee editable
- timeline des evenements
- transitions de statut avec validations metier
- dashboard minimal de pilotage

## Stack

- FastAPI
- React 18
- Vite
- sqlite3 natif
- SQLite local (`data/ideas.db`)

## Lancer

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm install
start.bat
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
./start.sh
```

Frontend: <http://127.0.0.1:5173>

API docs: <http://127.0.0.1:8000/docs>

Au premier lancement, l'application cree la base SQLite locale sans injecter de donnees de demonstration.

## API disponible

### Ideas

- `POST /ideas`
- `GET /ideas`
- `GET /ideas/{id}`
- `PUT /ideas/{id}`
- `DELETE /ideas/{id}`

### Lifecycle

- `POST /ideas/{id}/transition`
- `GET /ideas/{id}/events`
- `GET /ideas/{id}/graph`
- `GET /search?q=...`

## Exemples

Creation rapide :

```bash
curl -X POST http://127.0.0.1:8000/ideas \
  -H 'content-type: application/json' \
  -d '{"title":"Agentic architecture notebook"}'
```

Liste triee par derniere activite :

```bash
curl 'http://127.0.0.1:8000/ideas?sort=last_activity&order=desc'
```

Recherche :

```bash
curl 'http://127.0.0.1:8000/search?q=notebook'
```
