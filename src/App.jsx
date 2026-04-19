import { useEffect, useMemo, useState } from "react";
import {
  archiveIdea,
  createIdea,
  getIdea,
  getIdeaEvents,
  getIdeaGraph,
  listIdeas,
  searchIdeas,
  transitionIdea,
  updateIdea
} from "./api";
import {
  ALLOWED_TRANSITIONS,
  DOMAIN_OPTIONS,
  ORDER_OPTIONS,
  REASON_CODES,
  SORT_OPTIONS,
  SOURCE_TYPE_OPTIONS,
  STATUS_OPTIONS
} from "./constants";
import {
  formatDate,
  formatDateTime,
  fromInputDateTime,
  relativeStaleText,
  serializeTags,
  toInputDateTime
} from "./utils";

/* ── Labels de traduction ─────────────────────────────────────── */
const STATUS_LABELS = {
  GERME:       "Germination",
  EXPLORATION: "Exploration",
  POC:         "Prototype",
  TRANSMIS:    "Transmise",
  EN_VEILLE:   "En veille",
  ABANDONNE:   "Abandonnée",
  REALISE:     "Réalisée"
};

function statusLabel(s) { return STATUS_LABELS[s] || s; }

/* ── Icônes SVG ───────────────────────────────────────────────── */
const Icons = {
  brand: () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2.5L12.5 8H18L13.5 11.5L15.5 17L10 13.5L4.5 17L6.5 11.5L2 8H7.5L10 2.5Z"
        fill="white" />
    </svg>
  ),
  dashboard: () => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <rect x="0"  y="0"  width="5.5" height="5.5" rx="1.5"/>
      <rect x="8.5" y="0"  width="5.5" height="5.5" rx="1.5"/>
      <rect x="0"  y="8.5" width="5.5" height="5.5" rx="1.5"/>
      <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.5"/>
    </svg>
  ),
  capture: () => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <path d="M7.8 1.5 2.5 8.5h3.5L4.2 12.5 11.5 5.5H8L7.8 1.5Z"/>
    </svg>
  ),
  ideas: () => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
      <path d="M7 1.5a3.5 3.5 0 0 1 2 6.3V9.5H5V7.8A3.5 3.5 0 0 1 7 1.5Z"/>
      <path d="M5 10.5h4M5.5 12h3"/>
    </svg>
  ),
  stats: () => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <rect x="1"   y="7"  width="2.5" height="6" rx=".8"/>
      <rect x="5.5" y="3.5"width="2.5" height="9.5" rx=".8"/>
      <rect x="10"  y="1"  width="2.5" height="12" rx=".8"/>
    </svg>
  )
};

const PAGES = [
  { id: "dashboard", label: "Dashboard",  Icon: Icons.dashboard },
  { id: "capture",   label: "Capture",    Icon: Icons.capture },
  { id: "ideas",     label: "Portefeuille", Icon: Icons.ideas },
  { id: "stats",     label: "Statistiques", Icon: Icons.stats }
];

/* ── Constantes de formulaires ────────────────────────────────── */
const EMPTY_CREATE_FORM = {
  title: "", description: "", domain: "OTHER",
  source_type: "INTUITION", tags: "", source_context: ""
};

const EMPTY_FILTERS = {
  status: "", domain: "", tags: "", stale: false,
  revisit_before: "", sort: "last_activity", order: "desc"
};

const EMPTY_TRANSITION_FORM = {
  to_status: "", comment: "", reason_code: "", revisit_at: ""
};

/* ══════════════════════════════════════════════════════════════ */
function App() {
  const [page, setPage] = useState("dashboard");
  const [ideas, setIdeas] = useState([]);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [events, setEvents] = useState([]);
  const [graph, setGraph] = useState({ links: [] });
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState(false);
  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);
  const [updateForm, setUpdateForm] = useState(null);
  const [transitionForm, setTransitionForm] = useState(EMPTY_TRANSITION_FORM);
  const [transitionOpen, setTransitionOpen] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => { void refreshIdeas(); }, [filters]);

  useEffect(() => {
    if (!selectedIdeaId) {
      setSelectedIdea(null); setEvents([]); setGraph({ links: [] }); setUpdateForm(null);
      return;
    }
    void refreshIdeaDetail(selectedIdeaId);
  }, [selectedIdeaId]);

  const dashboard = useMemo(() => buildDashboard(ideas), [ideas]);
  const allowedTransitions = selectedIdea ? ALLOWED_TRANSITIONS[selectedIdea.current_status] || [] : [];

  async function refreshIdeas(overrides = {}) {
    setLoadingList(true); setError("");
    const sm = overrides.searchMode ?? searchMode;
    const sq = overrides.searchQuery ?? searchQuery;
    const ef = overrides.filters ?? filters;
    try {
      const data = sm && sq.trim()
        ? await searchIdeas(sq.trim())
        : await listIdeas({
            status: ef.status || undefined, domain: ef.domain || undefined,
            tags: ef.tags || undefined, stale: ef.stale || undefined,
            revisit_before: ef.revisit_before || undefined,
            sort: ef.sort, order: ef.order
          });
      setIdeas(data);
      if (data.length === 0) setSelectedIdeaId(null);
      else if (!selectedIdeaId || !data.some((i) => i.id === selectedIdeaId))
        setSelectedIdeaId(data[0].id);
    } catch (e) { setError(e.message); }
    finally { setLoadingList(false); }
  }

  async function refreshIdeaDetail(ideaId) {
    setLoadingDetail(true); setError("");
    try {
      const [idea, timeline, graphData] = await Promise.all([
        getIdea(ideaId), getIdeaEvents(ideaId), getIdeaGraph(ideaId)
      ]);
      setSelectedIdea(idea);
      setEvents(timeline);
      setGraph(graphData);
      setUpdateForm({
        title: idea.title, description: idea.description || "",
        domain: idea.domain, tags: (idea.tags || []).join(", "),
        source_type: idea.source_type, source_context: idea.source_context || "",
        confidence_level: idea.confidence_level ?? "",
        estimated_value: idea.estimated_value ?? "",
        estimated_effort: idea.estimated_effort ?? "",
        next_action: idea.next_action || "",
        revisit_at: toInputDateTime(idea.revisit_at)
      });
      setTransitionForm({
        to_status: (ALLOWED_TRANSITIONS[idea.current_status] || [])[0] || "",
        comment: "", reason_code: "", revisit_at: ""
      });
    } catch (e) { setError(e.message); }
    finally { setLoadingDetail(false); }
  }

  async function handleCreate(event) {
    event.preventDefault(); setError(""); setSuccessMessage("");
    try {
      const payload = {
        title: createForm.title, description: createForm.description || null,
        domain: createForm.domain, source_type: createForm.source_type,
        tags: serializeTags(createForm.tags), source_context: createForm.source_context || null
      };
      const created = await createIdea(payload);
      setCreateForm(EMPTY_CREATE_FORM);
      setSuccessMessage("Idée capturée avec succès.");
      setSearchMode(false); setSearchQuery("");
      await refreshIdeas({ searchMode: false, searchQuery: "" });
      setSelectedIdeaId(created.id);
      setPage("ideas");
    } catch (e) { setError(e.message); }
  }

  async function handleUpdate(event) {
    event.preventDefault();
    if (!selectedIdea || !updateForm) return;
    setError(""); setSuccessMessage("");
    try {
      await updateIdea(selectedIdea.id, {
        title: updateForm.title, description: updateForm.description || null,
        domain: updateForm.domain, tags: serializeTags(updateForm.tags),
        source_type: updateForm.source_type, source_context: updateForm.source_context || null,
        confidence_level: toNullableNumber(updateForm.confidence_level),
        estimated_value: toNullableNumber(updateForm.estimated_value),
        estimated_effort: toNullableNumber(updateForm.estimated_effort),
        next_action: updateForm.next_action || null,
        revisit_at: fromInputDateTime(updateForm.revisit_at)
      });
      setSuccessMessage("Idée mise à jour.");
      await refreshIdeas();
      await refreshIdeaDetail(selectedIdea.id);
    } catch (e) { setError(e.message); }
  }

  async function handleTransition(event) {
    event.preventDefault();
    if (!selectedIdea) return;
    setError(""); setSuccessMessage("");
    try {
      await transitionIdea(selectedIdea.id, {
        to_status: transitionForm.to_status,
        comment: transitionForm.comment,
        reason_code: transitionForm.reason_code || null,
        revisit_at: fromInputDateTime(transitionForm.revisit_at)
      });
      setTransitionOpen(false);
      setSuccessMessage("Transition appliquée.");
      await refreshIdeas();
      await refreshIdeaDetail(selectedIdea.id);
    } catch (e) { setError(e.message); }
  }

  async function handleArchive() {
    if (!selectedIdea) return;
    setError(""); setSuccessMessage("");
    try {
      await archiveIdea(selectedIdea.id);
      setSuccessMessage("Idée archivée.");
      await refreshIdeas();
    } catch (e) { setError(e.message); }
  }

  async function handleSearchSubmit(event) {
    event.preventDefault();
    const nextSearchMode = Boolean(searchQuery.trim());
    setSearchMode(nextSearchMode);
    await refreshIdeas({ searchMode: nextSearchMode, searchQuery });
    setPage("ideas");
  }

  async function handleResetSearch() {
    setSearchMode(false); setSearchQuery("");
    await refreshIdeas({ searchMode: false, searchQuery: "" });
  }

  const pageTitle = {
    dashboard: "Vue pilotage",
    capture:   "Capture rapide",
    ideas:     searchMode ? "Recherche" : "Portefeuille d'idées",
    stats:     "Statistiques"
  }[page];

  const pageSubtitle = {
    dashboard: "Repérez les idées à relancer, les signaux de stagnation et les zones actives.",
    capture:   "Un espace dédié à la saisie rapide, sans bruit ni surcharge décisionnelle.",
    ideas:     "Filtres, recherche, lecture détaillée et actions métier concentrées dans une vue de suivi.",
    stats:     "Vue analytique du portefeuille : tendances de statut, domaine et dynamique."
  }[page];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark"><Icons.brand /></div>
          <div>
            <strong>Idea Tracker</strong>
            <span>Lifecycle manager</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {PAGES.map((item) => (
            <button
              key={item.id} type="button"
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <span className="nav-icon"><item.Icon /></span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-card">
            <span className="sidebar-card-label">Portefeuille</span>
            <strong>{ideas.length} idées</strong>
            <p>{dashboard.sleepingCount} en veille · {dashboard.staleCount} stagnantes</p>
          </div>
          <button type="button" className="sidebar-primary" onClick={() => setPage("capture")}>
            + Nouvelle idée
          </button>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Idea Lifecycle Tracker</span>
            <h1>{pageTitle}</h1>
            <p>{pageSubtitle}</p>
          </div>
          <div className="topbar-actions">
            <div className="topbar-stat">
              <span>Actives</span>
              <strong>{ideas.length}</strong>
            </div>
            <div className="topbar-stat">
              <span>À relancer</span>
              <strong>{dashboard.revisitSoonCount}</strong>
            </div>
          </div>
        </header>

        {(error || successMessage) && (
          <div className={`flash ${error ? "flash-error" : "flash-success"}`}>
            {error || successMessage}
          </div>
        )}

        <main className="page-content">
          {page === "dashboard" && <DashboardPage dashboard={dashboard} ideas={ideas} setPage={setPage} />}
          {page === "capture" && (
            <CapturePage
              createForm={createForm} setCreateForm={setCreateForm}
              handleCreate={handleCreate} recentIdeas={ideas.slice(0, 5)}
            />
          )}
          {page === "ideas" && (
            <IdeasPage
              ideas={ideas} filters={filters} setFilters={setFilters}
              loadingList={loadingList} selectedIdeaId={selectedIdeaId}
              setSelectedIdeaId={setSelectedIdeaId} searchQuery={searchQuery}
              setSearchQuery={setSearchQuery} searchMode={searchMode}
              handleSearchSubmit={handleSearchSubmit} handleResetSearch={handleResetSearch}
              selectedIdea={selectedIdea} updateForm={updateForm} setUpdateForm={setUpdateForm}
              handleUpdate={handleUpdate} loadingDetail={loadingDetail}
              events={events} graph={graph} allowedTransitions={allowedTransitions}
              setTransitionOpen={setTransitionOpen} handleArchive={handleArchive}
            />
          )}
          {page === "stats" && <StatsPage dashboard={dashboard} ideas={ideas} />}
        </main>
      </div>

      {transitionOpen && selectedIdea && (
        <TransitionModal
          selectedIdea={selectedIdea} allowedTransitions={allowedTransitions}
          transitionForm={transitionForm} setTransitionForm={setTransitionForm}
          onClose={() => setTransitionOpen(false)} onSubmit={handleTransition}
        />
      )}
    </div>
  );
}

/* ── Dashboard ────────────────────────────────────────────────── */
function DashboardPage({ dashboard, ideas, setPage }) {
  const maxStatus = Math.max(1, ...dashboard.statusDistribution.map(([, c]) => c));

  // « Points chauds » : idées vraiment urgentes (stagnantes, à revisiter, ou actives)
  const hotIdeas = ideas
    .filter((i) => {
      const isActive = ["GERME", "EXPLORATION", "POC"].includes(i.current_status);
      const isStale  = new Date(i.updated_at).getTime() <= Date.now() - 30 * 24 * 60 * 60 * 1000;
      const needsRevisit = i.revisit_at && new Date(i.revisit_at).getTime() <= Date.now() + 7 * 24 * 60 * 60 * 1000;
      return isActive || isStale || needsRevisit;
    })
    .slice(0, 6);

  return (
    <div className="page-stack">
      <section className="kpi-grid">
        <MetricCard label="Créées cette semaine"  value={dashboard.createdThisWeek}      tone="warm" />
        <MetricCard label="Stagnantes"            value={dashboard.staleCount}           tone="cool" />
        <MetricCard label="Transmises ce mois"    value={dashboard.transmittedThisMonth} tone="sage" />
        <MetricCard label="Révision sous 7 j"     value={dashboard.revisitSoonCount}     tone="alert" />
      </section>

      <section className="split-grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Points chauds</h2>
              <p>Idées actives, stagnantes ou à relancer bientôt.</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => setPage("ideas")}>
              Tout voir
            </button>
          </div>
          <div className="focus-list">
            {hotIdeas.length === 0 && (
              <div className="empty-state">
                <h3>Aucun point chaud</h3>
                <p>Toutes vos idées actives sont bien suivies.</p>
              </div>
            )}
            {hotIdeas.map((idea) => (
              <article key={idea.id} className="focus-card">
                <div className="idea-card-top">
                  <span className={`status-pill status-${idea.current_status.toLowerCase()}`}>
                    {statusLabel(idea.current_status)}
                  </span>
                  <span className="idea-domain">{idea.domain}</span>
                </div>
                <strong>{idea.title}</strong>
                <p>{idea.next_action || idea.description || "Aucune action explicite."}</p>
                <small style={{ color: "var(--muted)", fontSize: ".8rem" }}>{relativeStaleText(idea.updated_at)}</small>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Par statut</h2>
              <p>Lecture rapide du portefeuille courant.</p>
            </div>
          </div>
          <div className="distribution">
            {dashboard.statusDistribution.map(([status, count]) => (
              <div key={status} className="distribution-row">
                <label>{statusLabel(status)}</label>
                <div className="distribution-track">
                  <div className="distribution-fill" style={{ width: `${(count / maxStatus) * 100}%` }} />
                </div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}

/* ── Capture ──────────────────────────────────────────────────── */
function CapturePage({ createForm, setCreateForm, handleCreate, recentIdeas }) {
  return (
    <div className="capture-layout">
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Nouvelle idée</h2>
            <p>Épuré pour maximiser la vitesse de saisie.</p>
          </div>
        </div>
        <form className="stack-form" onSubmit={handleCreate}>
          <label>
            <span>Titre</span>
            <input
              required value={createForm.title}
              onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
              placeholder="Ex. Radar d'arbitrage IA pour l'architecture"
            />
          </label>

          <details className="capture-details">
            <summary>Enrichissement optionnel</summary>
            <div className="grid-two">
              <label>
                <span>Domaine</span>
                <select value={createForm.domain} onChange={(e) => setCreateForm({ ...createForm, domain: e.target.value })}>
                  {DOMAIN_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </label>
              <label>
                <span>Source</span>
                <select value={createForm.source_type} onChange={(e) => setCreateForm({ ...createForm, source_type: e.target.value })}>
                  {SOURCE_TYPE_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </label>
            </div>
            <label>
              <span>Description</span>
              <textarea rows="4" value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })} />
            </label>
            <label>
              <span>Tags</span>
              <input value={createForm.tags} placeholder="llm, infra, décision"
                onChange={(e) => setCreateForm({ ...createForm, tags: e.target.value })} />
            </label>
            <label>
              <span>Contexte source</span>
              <textarea rows="3" value={createForm.source_context}
                onChange={(e) => setCreateForm({ ...createForm, source_context: e.target.value })} />
            </label>
          </details>

          <button className="primary-button" type="submit">Capturer l'idée</button>
        </form>
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Dernières captures</h2>
            <p>Rappel compact pour rester dans le contexte récent.</p>
          </div>
        </div>
        <div className="focus-list">
          {recentIdeas.map((idea) => (
            <article key={idea.id} className="focus-card compact">
              <strong>{idea.title}</strong>
              <div className="idea-card-top">
                <span className={`status-pill status-${idea.current_status.toLowerCase()}`}>
                  {statusLabel(idea.current_status)}
                </span>
                <span className="idea-domain">{formatDate(idea.created_at)}</span>
              </div>
              <p>{idea.description || "Capture concise."}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

/* ── Ideas ────────────────────────────────────────────────────── */
function IdeasPage(props) {
  const {
    ideas, filters, setFilters, loadingList, selectedIdeaId, setSelectedIdeaId,
    searchQuery, setSearchQuery, searchMode, handleSearchSubmit, handleResetSearch,
    selectedIdea, updateForm, setUpdateForm, handleUpdate, loadingDetail,
    events, graph, allowedTransitions, setTransitionOpen, handleArchive
  } = props;

  const [detailTab, setDetailTab] = useState("edit");

  useEffect(() => { setDetailTab("edit"); }, [selectedIdeaId]);

  return (
    <div className="ideas-layout">
      {/* ── Liste ── */}
      <section className="panel list-panel">
        <div className="section-head">
          <div>
            <h2>{searchMode ? "Résultats" : "Portefeuille"}</h2>
            <p>Recherche, filtres et signaux faibles.</p>
          </div>
          <span className="section-count">{loadingList ? "…" : `${ideas.length} idées`}</span>
        </div>

        <form className="search-toolbar" onSubmit={handleSearchSubmit}>
          <input value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher dans titres, descriptions et timeline" />
          <button className="primary-button" type="submit">Chercher</button>
          {searchMode && (
            <button className="secondary-button" type="button" onClick={handleResetSearch}>Reset</button>
          )}
        </form>

        <div className="filter-grid">
          <label>
            <span>Statut</span>
            <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
              <option value="">Tous</option>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}
            </select>
          </label>
          <label>
            <span>Domaine</span>
            <select value={filters.domain} onChange={(e) => setFilters({ ...filters, domain: e.target.value })}>
              <option value="">Tous</option>
              {DOMAIN_OPTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>
          <label>
            <span>Tags</span>
            <input value={filters.tags} placeholder="llm, infra"
              onChange={(e) => setFilters({ ...filters, tags: e.target.value })} />
          </label>
          <label>
            <span>Révision avant</span>
            <input type="date" value={filters.revisit_before}
              onChange={(e) => setFilters({ ...filters, revisit_before: e.target.value })} />
          </label>
          <label>
            <span>Tri</span>
            <select value={filters.sort} onChange={(e) => setFilters({ ...filters, sort: e.target.value })}>
              {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
          <label>
            <span>Ordre</span>
            <select value={filters.order} onChange={(e) => setFilters({ ...filters, order: e.target.value })}>
              {ORDER_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
        </div>

        <label className="checkbox-row">
          <input type="checkbox" checked={filters.stale}
            onChange={(e) => setFilters({ ...filters, stale: e.target.checked })} />
          <span>Uniquement stagnantes (&gt; 30 j)</span>
        </label>

        <div className="idea-list">
          {ideas.map((idea) => (
            <button key={idea.id} type="button"
              className={`idea-card ${selectedIdeaId === idea.id ? "selected" : ""}`}
              onClick={() => setSelectedIdeaId(idea.id)}
            >
              <div className="idea-card-top">
                <span className={`status-pill status-${idea.current_status.toLowerCase()}`}>
                  {statusLabel(idea.current_status)}
                </span>
                <span className="idea-domain">{idea.domain}</span>
              </div>
              <strong>{idea.title}</strong>
              <p>{idea.description || "Aucune description."}</p>
              <div className="tag-row">
                {(idea.tags || []).map((tag) => <span key={tag} className="tag-chip">#{tag}</span>)}
              </div>
              <div className="idea-card-bottom">
                <span>{relativeStaleText(idea.updated_at)}</span>
                {idea.revisit_at && <span>Révision : {formatDate(idea.revisit_at)}</span>}
              </div>
            </button>
          ))}
          {!loadingList && ideas.length === 0 && (
            <div className="empty-state">
              <h3>Aucune idée visible</h3>
              <p>Ajustez les filtres ou relancez une recherche plus large.</p>
            </div>
          )}
        </div>
      </section>

      {/* ── Détail ── */}
      <section className="panel detail-panel">
        {loadingDetail && <div className="empty-state">Chargement de la fiche idée…</div>}

        {!loadingDetail && !selectedIdea && (
          <div className="empty-state">
            <h3>Sélectionnez une idée</h3>
            <p>Le détail complet s'affiche ici dans cette colonne dédiée.</p>
          </div>
        )}

        {!loadingDetail && selectedIdea && updateForm && (
          <>
            {/* En-tête */}
            <div className="detail-header">
              <div>
                <span className={`status-pill status-${selectedIdea.current_status.toLowerCase()}`}>
                  {statusLabel(selectedIdea.current_status)}
                </span>
                <h2>{selectedIdea.title}</h2>
                <p>Créée le {formatDateTime(selectedIdea.created_at)} · Mise à jour le {formatDateTime(selectedIdea.updated_at)}</p>
              </div>
              <div className="detail-actions">
                {allowedTransitions.length > 0 && (
                  <button className="primary-button" type="button" onClick={() => setTransitionOpen(true)}>
                    Faire évoluer
                  </button>
                )}
                {!selectedIdea.archived && (
                  <button className="danger-button" type="button" onClick={handleArchive}>Archiver</button>
                )}
              </div>
            </div>

            {/* Onglets */}
            <div className="detail-tabs">
              <button className={`tab-btn ${detailTab === "edit"     ? "active" : ""}`} type="button" onClick={() => setDetailTab("edit")}>Fiche</button>
              <button className={`tab-btn ${detailTab === "timeline" ? "active" : ""}`} type="button" onClick={() => setDetailTab("timeline")}>
                Timeline{events.length > 0 ? ` (${events.length})` : ""}
              </button>
              <button className={`tab-btn ${detailTab === "links"    ? "active" : ""}`} type="button" onClick={() => setDetailTab("links")}>
                Liens{graph.links.length > 0 ? ` (${graph.links.length})` : ""}
              </button>
            </div>

            {/* Onglet : Fiche */}
            {detailTab === "edit" && (
              <form className="stack-form tab-content" onSubmit={handleUpdate}>
                <div className="grid-two">
                  <label>
                    <span>Titre</span>
                    <input value={updateForm.title}
                      onChange={(e) => setUpdateForm({ ...updateForm, title: e.target.value })} />
                  </label>
                  <label>
                    <span>Domaine</span>
                    <select value={updateForm.domain}
                      onChange={(e) => setUpdateForm({ ...updateForm, domain: e.target.value })}>
                      {DOMAIN_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </label>
                </div>

                <label>
                  <span>Description</span>
                  <textarea rows="4" value={updateForm.description}
                    onChange={(e) => setUpdateForm({ ...updateForm, description: e.target.value })} />
                </label>

                <div className="grid-two">
                  <label>
                    <span>Source</span>
                    <select value={updateForm.source_type}
                      onChange={(e) => setUpdateForm({ ...updateForm, source_type: e.target.value })}>
                      {SOURCE_TYPE_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Tags</span>
                    <input value={updateForm.tags}
                      onChange={(e) => setUpdateForm({ ...updateForm, tags: e.target.value })} />
                  </label>
                </div>

                <label>
                  <span>Contexte source</span>
                  <textarea rows="3" value={updateForm.source_context}
                    onChange={(e) => setUpdateForm({ ...updateForm, source_context: e.target.value })} />
                </label>

                <div className="scores-row">
                  <ScoreField label="Confiance"  value={updateForm.confidence_level}
                    onChange={(v) => setUpdateForm({ ...updateForm, confidence_level: v })} />
                  <ScoreField label="Valeur"     value={updateForm.estimated_value}
                    onChange={(v) => setUpdateForm({ ...updateForm, estimated_value: v })} />
                  <ScoreField label="Effort"     value={updateForm.estimated_effort}
                    onChange={(v) => setUpdateForm({ ...updateForm, estimated_effort: v })} />
                </div>

                <label>
                  <span>Prochaine action</span>
                  <textarea rows="2" value={updateForm.next_action}
                    onChange={(e) => setUpdateForm({ ...updateForm, next_action: e.target.value })} />
                </label>

                <label>
                  <span>À revoir le</span>
                  <input type="datetime-local" value={updateForm.revisit_at}
                    onChange={(e) => setUpdateForm({ ...updateForm, revisit_at: e.target.value })} />
                </label>

                <button className="primary-button" type="submit">Enregistrer</button>
              </form>
            )}

            {/* Onglet : Timeline */}
            {detailTab === "timeline" && (
              <div className="tab-content">
                {events.length === 0 && <div className="mini-empty">Aucun événement enregistré.</div>}
                <div className="timeline">
                  {events.map((event) => (
                    <article key={event.id} className="timeline-item">
                      <div className="timeline-marker" />
                      <div>
                        <strong>{event.event_type}</strong>
                        <p>
                          {event.from_status && `${statusLabel(event.from_status)} → `}
                          {event.to_status ? statusLabel(event.to_status) : "Mise à jour"}
                        </p>
                        {event.comment    && <p>{event.comment}</p>}
                        {event.reason_code && <p>Code raison : {event.reason_code}</p>}
                        <small>{formatDateTime(event.created_at)}</small>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {/* Onglet : Liens */}
            {detailTab === "links" && (
              <div className="tab-content">
                {graph.links.length === 0 && <div className="mini-empty">Aucun lien explicite pour cette idée.</div>}
                <div className="link-list">
                  {graph.links.map((link) => (
                    <article key={link.id} className="link-card">
                      <span className="direction-chip">{link.direction}</span>
                      <strong>{link.target.title}</strong>
                      <p>{link.link_type}</p>
                      <small style={{ color: "var(--muted)", fontSize: ".8rem" }}>
                        {statusLabel(link.target.current_status)}
                        {link.target.archived ? " · archivée" : ""}
                      </small>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

/* ── Stats ────────────────────────────────────────────────────── */
function StatsPage({ dashboard, ideas }) {
  const byDomain = DOMAIN_OPTIONS.map((domain) => [
    domain, ideas.filter((i) => i.domain === domain).length
  ]).filter(([, count]) => count > 0);

  const maxStatus = Math.max(1, ...dashboard.statusDistribution.map(([, c]) => c));
  const maxDomain = Math.max(1, ...byDomain.map(([, c]) => c));

  return (
    <div className="page-stack">
      <section className="kpi-grid">
        <MetricCard label="En veille"           value={dashboard.sleepingCount}    tone="sage" />
        <MetricCard label="Stagnantes"          value={dashboard.staleCount}       tone="cool" />
        <MetricCard label="Révision sous 7 j"   value={dashboard.revisitSoonCount} tone="warm" />
        <MetricCard label="Actives"             value={ideas.length}               tone="alert" />
      </section>

      <section className="split-grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Par statut</h2>
              <p>Répartition actuelle du cycle de vie.</p>
            </div>
          </div>
          <div className="distribution">
            {dashboard.statusDistribution.map(([status, count]) => (
              <div key={status} className="distribution-row">
                <label>{statusLabel(status)}</label>
                <div className="distribution-track">
                  <div className="distribution-fill" style={{ width: `${(count / maxStatus) * 100}%` }} />
                </div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Par domaine</h2>
              <p>Vue analytique du portefeuille.</p>
            </div>
          </div>
          <div className="distribution">
            {byDomain.map(([domain, count]) => (
              <div key={domain} className="distribution-row">
                <label>{domain}</label>
                <div className="distribution-track">
                  <div className="distribution-fill" style={{ width: `${(count / maxDomain) * 100}%` }} />
                </div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}

/* ── Modal de transition ──────────────────────────────────────── */
function TransitionModal({ selectedIdea, allowedTransitions, transitionForm, setTransitionForm, onClose, onSubmit }) {
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="section-head">
          <div>
            <h2>Faire évoluer l'idée</h2>
            <p>Statut actuel : <strong>{statusLabel(selectedIdea.current_status)}</strong></p>
          </div>
        </div>

        <form className="stack-form" onSubmit={onSubmit}>
          <label>
            <span>Statut cible</span>
            <select value={transitionForm.to_status} required
              onChange={(e) => setTransitionForm({ ...transitionForm, to_status: e.target.value, reason_code: "", revisit_at: "" })}>
              <option value="">Sélectionner…</option>
              {allowedTransitions.map((s) => (
                <option key={s} value={s}>{statusLabel(s)}</option>
              ))}
            </select>
          </label>

          <label>
            <span>Commentaire</span>
            <textarea rows="4" value={transitionForm.comment}
              onChange={(e) => setTransitionForm({ ...transitionForm, comment: e.target.value })} />
          </label>

          {(transitionForm.to_status === "EN_VEILLE" || transitionForm.to_status === "ABANDONNE") && (
            <label>
              <span>Code raison</span>
              <select value={transitionForm.reason_code}
                onChange={(e) => setTransitionForm({ ...transitionForm, reason_code: e.target.value })}>
                <option value="">Sélectionner…</option>
                {(REASON_CODES[transitionForm.to_status] || []).map((code) => (
                  <option key={code} value={code}>{code}</option>
                ))}
              </select>
            </label>
          )}

          {transitionForm.to_status === "EN_VEILLE" && (
            <label>
              <span>À revoir le</span>
              <input type="datetime-local" value={transitionForm.revisit_at}
                onChange={(e) => setTransitionForm({ ...transitionForm, revisit_at: e.target.value })} />
            </label>
          )}

          <div className="modal-actions">
            <button className="secondary-button" type="button" onClick={onClose}>Annuler</button>
            <button className="primary-button" type="submit">Appliquer</button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Composants utilitaires ───────────────────────────────────── */
function MetricCard({ label, value, tone }) {
  return (
    <article className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ScoreField({ label, value, onChange }) {
  const current = Number(value) || 0;
  return (
    <div className="score-field">
      <span className="score-label">{label}</span>
      <div className="score-pips">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n} type="button"
            className={`score-pip ${current >= n ? "filled" : ""}`}
            onClick={() => onChange(current === n ? "" : String(n))}
            title={`${n}/5`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ── Helpers ──────────────────────────────────────────────────── */
function buildDashboard(ideas) {
  const now = Date.now();
  const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
  const thirtyDaysAgo = now - 30 * 24 * 60 * 60 * 1000;
  const d = new Date();

  const statusDistribution = STATUS_OPTIONS.map((status) => [
    status, ideas.filter((i) => i.current_status === status).length
  ]).filter(([, count]) => count > 0);

  return {
    createdThisWeek: ideas.filter((i) => new Date(i.created_at).getTime() >= weekAgo).length,
    staleCount:      ideas.filter((i) => new Date(i.updated_at).getTime() <= thirtyDaysAgo).length,
    sleepingCount:   ideas.filter((i) => i.current_status === "EN_VEILLE").length,
    revisitSoonCount: ideas.filter((i) => {
      if (!i.revisit_at) return false;
      return new Date(i.revisit_at).getTime() <= now + 7 * 24 * 60 * 60 * 1000;
    }).length,
    transmittedThisMonth: ideas.filter((i) => {
      const u = new Date(i.updated_at);
      return i.current_status === "TRANSMIS" && u.getMonth() === d.getMonth() && u.getFullYear() === d.getFullYear();
    }).length,
    statusDistribution
  };
}

function toNullableNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  return Number(value);
}

export default App;
