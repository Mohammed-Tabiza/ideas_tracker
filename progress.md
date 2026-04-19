# Progress

## 2026-04-19

- Lecture de `SPEC.md`
- Audit du repo existant
- Verification de l'etat git et des fichiers presents
- Constat : repo limite a un bootstrap backend sur `POST /ideas` et `GET /ideas`
- Creation des fichiers de planification persistants pour reprendre la finalisation
- Formalisation du reste a faire par lots backend, frontend, qualite et livraison
- Implementation du lot backend : schema SQLite complet, FTS5, couche service, endpoints v1
- Ajout de tests API `unittest` avec base SQLite temporaire
- Verification OK : `python -m unittest tests.test_api -v`
- Implementation du frontend v1 en React/Vite
- Mise a jour des scripts `start.bat` et `start.sh` pour lancer backend + frontend
- Verification OK : `npm run build`
- Ajout de l'API d'ecriture `IdeaLink` avec tests de creation, duplication et suppression
- Ajout d'un seed de demonstration idempotent pour peupler l'application au premier lancement
- Verification OK : `python -m unittest tests.test_api -v`
