# SPEC.md — Idea Lifecycle Tracker (v1.3)

## 1. Règle d'implémentation (priorité absolue)

Commencer par `POST /ideas` + `GET /ideas` uniquement.
Utiliser l'outil 3 jours avant d'ajouter timeline, dashboard ou scoring.

> Si l'outil n'est pas utilisé après 2 semaines, le problème est le design, pas la technique.

---

## 2. Vision

Outil local solo permettant de **capturer, suivre et réactiver des idées** dans un contexte
d'architecture IA, innovation et stratégie technique.

Objectifs :

- préserver le **contexte d'émergence**
- tracer les **décisions et arbitrages**
- visualiser l'**évolution dans le temps**
- faciliter la **réactivation**

**Contexte d'usage** : outil mono-utilisateur, local, sans authentification.

---

## 3. Principes de conception

- **Idée = entité vivante** — évolue, peut être abandonnée puis relancée
- **Valeur = trace des décisions** — ce qui compte, c'est le *pourquoi*
- **Zéro friction à la capture** — sinon l'outil ne sera pas utilisé
- **Réactivation > archivage** — une idée "morte" peut redevenir stratégique

---

## 4. Modèle de données

### 4.1 Entité `Idea`

```json
{
  "id": "uuid",
  "title": "string",
  "description": "text | null",
  "domain": "enum (default: OTHER)",
  "tags": ["string"],
  "source_type": "enum (default: INTUITION)",
  "source_context": "text | null",

  "created_at": "datetime",
  "updated_at": "datetime",

  "current_status": "enum (default: GERME)",

  "confidence_level": "int (1-5) | null",
  "estimated_value": "int (1-5) | null",
  "estimated_effort": "int (1-5) | null",

  "next_action": "text | null",
  "revisit_at": "datetime | null",

  "archived": "boolean (default: false)"
}
```

**Décisions v1.3 :**

- `current_owner` supprimé — outil solo, champ sans valeur
- `parent_idea_id` supprimé — toutes les relations passent par `IdeaLink`
- `confidence_level`, `estimated_value`, `estimated_effort` sont **optionnels** à la capture,
  enrichissables ultérieurement (zéro friction)
- `revisit_at` : positionné **manuellement** lors d'une transition vers `EN_VEILLE` uniquement
  (voir §7.2). Pas de calcul automatique en v1.
- `domain` et `source_type` ont des **défauts automatiques** — jamais obligatoires à la saisie

---

### 4.2 Entité `IdeaEvent`

Journal de vie — une ligne par action significative.

```json
{
  "id": "uuid",
  "idea_id": "uuid",
  "event_type": "enum",
  "from_status": "enum | null",
  "to_status": "enum | null",
  "comment": "text",
  "reason_code": "enum | null",
  "created_at": "datetime"
}
```

Types d'événements (`event_type`) :

```
CREATION
TRANSITION
EDIT
NOTE
```

---

### 4.3 Entité `IdeaLink`

```json
{
  "id": "uuid",
  "source_idea_id": "uuid",
  "target_idea_id": "uuid",
  "link_type": "enum"
}
```

Types de liens :

```
parent
child
related
duplicate
derived_from
```

**Les liens ne sont pas automatiquement symétriques.**
Si une relation bidirectionnelle est souhaitée, deux entrées `IdeaLink` doivent être créées
(une dans chaque sens). Le graphe reflète exactement ce qui est explicitement déclaré.

---

## 5. Domaines

```
IA4IT
IA4ALL
STRATEGY
ARCHITECTURE
OTHER        ← défaut
```

---

## 6. Types de source

```
CONVERSATION
MEETING
READING
EXPERIMENT
INTUITION    ← défaut
OTHER
```

---

## 7. Cycle de vie des statuts

```
GERME → EXPLORATION → POC → TRANSMIS → REALISE
              ↘ EN_VEILLE ↗
              ↘ ABANDONNE → EXPLORATION
```

### 7.1 Matrice des transitions autorisées

```python
ALLOWED_TRANSITIONS = {
    "GERME":       ["EXPLORATION", "ABANDONNE"],
    "EXPLORATION": ["POC", "EN_VEILLE", "ABANDONNE"],
    "POC":         ["TRANSMIS", "EN_VEILLE", "ABANDONNE"],
    "TRANSMIS":    ["REALISE", "EN_VEILLE"],
    "EN_VEILLE":   ["EXPLORATION", "ABANDONNE"],
    "ABANDONNE":   ["EXPLORATION"],
    "REALISE":     []
}
```

**Garde-fous :**

- Transition vers le **même statut interdite** — rejetée avec une erreur 400.
- Transition vers un statut absent de `ALLOWED_TRANSITIONS[current_status]` — rejetée avec 400.

---

### 7.2 Obligations de transition

| Statut cible | `comment`      | `reason_code`  | `revisit_at`   |
|---|---|---|---|
| EXPLORATION  | optionnel      | —              | —              |
| POC          | optionnel      | —              | —              |
| TRANSMIS     | **obligatoire** | —             | —              |
| EN_VEILLE    | **obligatoire** | **obligatoire** | **obligatoire** |
| ABANDONNE    | **obligatoire** | **obligatoire** | —              |
| REALISE      | **obligatoire** | —             | —              |

---

### 7.3 Reason codes

**EN_VEILLE**

```
TOO_EARLY
NO_PRIORITY
WAITING_DEPENDENCY
```

**ABANDONNE**

```
NO_VALUE
TOO_COMPLEX
DUPLICATE
CONTEXT_CHANGED
```

---

### 7.4 Payload de transition (standard)

```python
class TransitionRequest(BaseModel):
    to_status: str
    comment: str = ""               # vide autorisé côté schéma, validé dans le service
    reason_code: Optional[str]      # validé selon §7.2
    revisit_at: Optional[datetime]  # obligatoire si to_status == EN_VEILLE
```

Validation à effectuer dans le **service**, pas uniquement dans le schéma Pydantic.
Ordre des validations :

1. `to_status != current_status` (même statut interdit)
2. `to_status` dans `ALLOWED_TRANSITIONS[current_status]`
3. Champs obligatoires selon §7.2

---

## 8. Règles sur `updated_at`

`updated_at` sur `Idea` est mis à jour **à chaque écriture** qui concerne l'idée :

| Action | `updated_at` mis à jour |
|---|---|
| `PUT /ideas/{id}` (édition directe) | oui |
| `POST /ideas/{id}/transition` | oui |
| Création d'un `IdeaEvent` (type NOTE, EDIT) | oui |

Cette règle garantit que le filtre `?stale=true` (aucune activité depuis > 30 jours)
est fiable sur toutes les formes d'activité — y compris les notes sans transition.

---

## 9. Définition de `last_activity`

`last_activity` n'est **pas un champ stocké** dans `ideas`.

Il est calculé à la volée comme :

```sql
MAX(ideas.updated_at, MAX(idea_events.created_at))
```

Le tri `?sort=last_activity` utilise cette valeur calculée.
Le filtre `?stale=true` utilise cette même valeur (> 30 jours).

Implémentation recommandée : sous-requête ou CTE dans `GET /ideas`.

---

## 10. Comportement des endpoints sur les idées archivées

### Règle générale

`archived = true` équivaut à une suppression logique. Par défaut, les idées archivées
sont **invisibles** dans tous les endpoints de liste et de recherche.

### Tableau de référence

| Endpoint | Comportement par défaut | Opt-in |
|---|---|---|
| `GET /ideas` | `archived = false` uniquement | `?include_archived=true` |
| `GET /search?q=` | `archived = false` uniquement | `?include_archived=true` |
| `GET /ideas/{id}` | retourne l'idée **même si archivée** | — |
| `GET /ideas/{id}/events` | retourne les events **même si archivée** | — |
| `GET /ideas/{id}/graph` | retourne le graph **même si archivée** | — |

### Justification

`GET /ideas/{id}` retourne toujours l'idée archivée pour permettre la consultation directe
(lien partagé, référence depuis une autre idée) sans polluer les listes.

---

## 11. Recherche full-text (FTS5)

### 11.1 Table virtuelle

```sql
CREATE VIRTUAL TABLE ideas_fts USING fts5(
    idea_id UNINDEXED,
    title,
    description,
    aggregated_events_text
);
```

### 11.2 Règles d'indexation

- `title` et `description` : depuis `ideas`
- `aggregated_events_text` : concaténation des `comment` de tous les `IdeaEvent` liés
- `reason_code` **non indexé** — valeur technique, pas sémantique
- Les idées avec `archived = true` **ne sont pas filtrées dans la table FTS5 elle-même**,
  le filtre est appliqué dans la requête SQL finale (jointure avec `ideas.archived = false`)

### 11.3 Stratégie de synchronisation

**Choix retenu : logique applicative** (pas de triggers SQLite).

Un **rebuild complet** de `aggregated_events_text` pour une idée donnée est déclenché à chaque :

- modification de `ideas.title`
- modification de `ideas.description`
- création d'un `IdeaEvent` (tout type)
- modification du `comment` d'un `IdeaEvent` existant

```python
def build_events_text(idea_id: str, db) -> str:
    rows = db.execute(
        "SELECT comment FROM idea_events WHERE idea_id = ? ORDER BY created_at ASC",
        [idea_id]
    ).fetchall()
    return " ".join(r[0] for r in rows if r[0])

# Dans chaque transaction d'écriture concernée :
with db.begin():
    # ... écriture principale ...
    db.execute(
        "UPDATE ideas_fts SET title=?, description=?, aggregated_events_text=? WHERE idea_id=?",
        [title, description, build_events_text(idea_id, db), idea_id]
    )
```

---

## 12. API (FastAPI)

### 12.1 Ideas

```
POST   /ideas              # capture rapide — title seul obligatoire
GET    /ideas              # liste (archived=false par défaut)
GET    /ideas/{id}         # fiche complète (retourne même si archivée)
PUT    /ideas/{id}         # édition des champs enrichissables
DELETE /ideas/{id}         # soft delete : archived = true
```

Paramètres de filtre pour `GET /ideas` :

```
?status=EN_VEILLE
?domain=IA4IT
?tags=llm,infra
?stale=true                  # last_activity > 30 jours
?revisit_before=2026-05-01
?include_archived=true       # inclut les idées archivées
?sort=created_at|last_activity|estimated_value
?order=asc|desc
```

---

### 12.2 Transitions

```
POST /ideas/{id}/transition
```

Payload : voir §7.4.

Comportement (dans cet ordre) :

1. Vérifier que `to_status != current_status`
2. Vérifier que `to_status` est dans `ALLOWED_TRANSITIONS[current_status]`
3. Valider les champs obligatoires selon §7.2
4. Créer un `IdeaEvent` de type `TRANSITION`
5. Mettre à jour `current_status` et `updated_at` dans `ideas`
6. Rebuilder `ideas_fts` dans la même transaction (§11.3)

---

### 12.3 Events

```
GET /ideas/{id}/events     # timeline ordonnée par created_at ASC
```

---

### 12.4 Graph

```
GET /ideas/{id}/graph
```

Réponse :

```json
{
  "idea": { "...idea object..." },
  "links": [
    {
      "link_type": "related",
      "direction": "outgoing",
      "target": {
        "id": "uuid",
        "title": "string",
        "current_status": "enum",
        "archived": "boolean"
      }
    },
    {
      "link_type": "derived_from",
      "direction": "incoming",
      "target": {
        "id": "uuid",
        "title": "string",
        "current_status": "enum",
        "archived": "boolean"
      }
    }
  ]
}
```

Note : `direction = "outgoing"` si `source_idea_id == id`, `"incoming"` si `target_idea_id == id`.
Les deux sens sont retournés dans la même réponse. `archived` est inclus pour permettre
un affichage différencié des idées archivées dans le graphe.

---

### 12.5 Recherche

```
GET /search?q=...&include_archived=true
```

Réponse : liste d'idées avec score de pertinence FTS5, ordonnée par rank.
Par défaut : `archived = false` uniquement.

---

## 13. Base de données (SQLite)

Tables :

```
ideas
idea_events
idea_links
ideas_fts          (table virtuelle FTS5)
```

Index recommandés :

```sql
CREATE INDEX idx_ideas_status    ON ideas(current_status);
CREATE INDEX idx_ideas_domain    ON ideas(domain);
CREATE INDEX idx_ideas_updated   ON ideas(updated_at);
CREATE INDEX idx_ideas_archived  ON ideas(archived);
CREATE INDEX idx_events_idea_id  ON idea_events(idea_id);
CREATE INDEX idx_links_source    ON idea_links(source_idea_id);
CREATE INDEX idx_links_target    ON idea_links(target_idea_id);
```

---

## 14. Fonctionnalités v1

### 14.1 Capture rapide (< 10 secondes)

Seul champ affiché et obligatoire :

- `title`

Valeurs par défaut automatiques — aucun sélecteur requis à la capture :

| Champ | Défaut |
|---|---|
| `domain` | `OTHER` |
| `source_type` | `INTUITION` |
| `current_status` | `GERME` |
| `archived` | `false` |

Champs secondaires accessibles (accordéon ou section optionnelle) :

- `description`
- `domain` (si différent du défaut)
- `source_type` (si différent du défaut)
- `tags`
- `source_context`

---

### 14.2 Liste des idées

Filtres : statut, domaine, tags, stagnation > 30 j, `revisit_at`, archivées (opt-in).
Tri : date création, dernière activité, valeur estimée.

---

### 14.3 Fiche idée

- tous les champs éditables
- statut courant + bouton de transition
- liens (`IdeaLink`) avec accès direct aux idées liées (archivées affichées avec badge)
- timeline des événements (voir §14.4)
- champ `next_action`

---

### 14.4 Timeline

Affichage vertical, ordre chronologique croissant :

```
[2026-04-17] Création (INTUITION)
[2026-04-18] → EXPLORATION — "Valide après discussion avec équipe"
[2026-04-22] → POC
[2026-05-02] → EN_VEILLE (TOO_EARLY) — "Attente roadmap Q3" — revisit: 2026-07-01
```

---

### 14.5 Modal de transition

- sélecteur de statut (uniquement les transitions autorisées depuis `ALLOWED_TRANSITIONS`)
- champ commentaire
- sélecteur `reason_code` (conditionnel : EN_VEILLE, ABANDONNE)
- date picker `revisit_at` (conditionnel : EN_VEILLE uniquement)

---

### 14.6 Vue pilotage (dashboard)

Widgets :

- idées créées cette semaine
- idées stagnantes (last_activity > 30 jours, `archived = false`)
- idées en veille avec `revisit_at` dépassé ou dans les 7 jours
- idées transmises ce mois
- distribution par statut (donut ou barres)
- distribution par domaine

---

## 15. Stack technique

| Composant | Choix |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Base de données | SQLite 3.x + FTS5 |
| Accès DB | `sqlite3` natif — pas d'ORM |
| Frontend | React 18 + Vite |
| HTTP client | `fetch` natif |

**Pas d'ORM** : les requêtes FTS5, les CTEs pour `last_activity` et les agrégats du dashboard
nécessitent du SQL direct. Un ORM ajouterait de la complexité sans valeur.

---

## 16. Lancement

```
start.bat    # Windows
start.sh     # Linux / macOS
```

Les deux scripts lancent :

- backend FastAPI sur le port 8000 (`uvicorn app.main:app --reload`)
- frontend Vite sur le port 5173 (`npm run dev`)

---

## 17. Roadmap

### v2

- scoring automatique (LLM via Anthropic API)
- suggestions de liens entre idées
- résumé automatique de la timeline

### v3

- export markdown
- intégration Notion / Git
- partage partiel

---

## 18. Risques

- **sur-modélisation** : trop de champs → friction → abandon
- **sous-utilisation** : outil non ouvert → inutile
- **FTS désynchronisée** : rebuild oublié → recherche incohérente (mitigé par §11.3)
- **`last_activity` incorrect** : si `updated_at` non mis à jour sur création d'event → filtre `stale` faux (mitigé par §8)
