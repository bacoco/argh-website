const ui = {
  fr: {
    dossier: ["Dossiers", "Incidents, mécanismes, réponses et leçons reliés."],
    project: ["Projets", "La trajectoire publique de chaque système, réunie sans provenance privée."],
    pattern: ["Motifs", "Les mêmes formes de panne et de contrôle, expliquées à deux niveaux de lecture."],
    atlas: ["Atlas", "Les motifs publics qui relient les dossiers et les projets."],
    dossiers: "Dossiers", projects: "Projets", patterns: "Motifs", atlasNav: "Atlas",
    search: "Rechercher…", loading: "Chargement du magasin public…", open: "Lire le dossier",
    entries: count => `${count} entrée${count > 1 ? "s" : ""}`,
    error: "Le magasin public ne peut pas être chargé."
  },
  en: {
    dossier: ["Cases", "Connected incidents, mechanisms, responses and lessons."],
    project: ["Projects", "Each system’s public trajectory, without private provenance."],
    pattern: ["Patterns", "Recurring failure and control shapes, explained at two reading levels."],
    atlas: ["Atlas", "The public patterns connecting cases and projects."],
    dossiers: "Cases", projects: "Projects", patterns: "Patterns", atlasNav: "Atlas",
    search: "Search…", loading: "Loading the public store…", open: "Read the case",
    entries: count => `${count} entr${count === 1 ? "y" : "ies"}`,
    error: "The public store could not be loaded."
  }
};

const body = document.body;
const requestedType = body.dataset.type || "dossier";
const entityType = requestedType === "atlas" ? "pattern" : requestedType;
const dataRoot = body.dataset.dataRoot || "data";
const allowedLanguages = ["fr", "en"];
const allowedViews = ["simple", "expert"];
const query = new URLSearchParams(location.search);

function stored(key) {
  try { return localStorage.getItem(key); } catch (_) { return null; }
}

function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (_) { /* storage is optional */ }
}

function selected(allowed, requested, remembered, fallback) {
  if (allowed.includes(requested)) return requested;
  if (allowed.includes(remembered)) return remembered;
  return fallback;
}

const state = {
  lang: selected(allowedLanguages, query.get("lang"), stored("argh-language"), "fr"),
  view: selected(allowedViews, query.get("view"), stored("argh-reader"), "simple"),
  search: "",
  entities: []
};

const $ = selector => document.querySelector(selector);

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function modeName() {
  if (state.view === "expert") return "expert";
  return state.lang === "fr" ? "cuisine" : "kitchen";
}

function authored(quad) {
  return quad?.[state.lang]?.[modeName()] || "";
}

function setQuery() {
  const url = new URL(location.href);
  url.searchParams.set("lang", state.lang);
  url.searchParams.set("view", state.view);
  history.replaceState(history.state, "", url.pathname + url.search + url.hash);
  document.querySelectorAll("nav a").forEach(link => {
    const target = new URL(link.href, location.href);
    target.searchParams.set("lang", state.lang);
    target.searchParams.set("view", state.view);
    link.href = target.pathname + target.search;
  });
}

function renderChrome() {
  const copy = ui[state.lang];
  const page = copy[requestedType];
  document.documentElement.lang = state.lang;
  document.title = `ARGH — ${page[0]}`;
  $("#headline").textContent = page[0];
  $("#deck").textContent = page[1];
  $("#search").placeholder = copy.search;
  $("#nav-dossiers").textContent = copy.dossiers;
  $("#nav-projects").textContent = copy.projects;
  $("#nav-patterns").textContent = copy.patterns;
  $("#nav-atlas").textContent = copy.atlasNav;
  document.querySelectorAll("[data-lang]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.lang === state.lang));
  });
  document.querySelectorAll("[data-view]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.view === state.view));
  });
  $("#mode-label").textContent = state.lang === "fr"
    ? (state.view === "simple" ? "Cuisine" : "Technique")
    : (state.view === "simple" ? "Kitchen" : "Technical");
  setQuery();
}

function entityCard(entity) {
  const hero = entity.slots.find(slot => slot.id === "hero");
  const card = node("article", "dossier");
  const relationNames = [...entity.relationships.projects, ...entity.relationships.patterns];
  card.append(node("div", "dossier-meta", relationNames.slice(0, 5).join(" · ") || entity.type));
  card.append(node("h2", "", authored(hero.heading)));
  hero.body.forEach(paragraph => card.append(node("p", "summary", authored(paragraph))));

  const remaining = entity.slots.filter(slot => slot.id !== "hero");
  if (remaining.length) {
    const details = node("details");
    details.append(node("summary", "", ui[state.lang].open));
    remaining.forEach(slot => {
      const section = node("section", "entity-slot");
      section.append(node("h3", "", authored(slot.heading)));
      slot.body.forEach(paragraph => section.append(node("p", "", authored(paragraph))));
      details.append(section);
    });
    card.append(details);
  }
  return card;
}

function renderEntities() {
  const needle = state.search.toLocaleLowerCase(state.lang);
  const filtered = state.entities.filter(entity => {
    if (!needle) return true;
    const text = entity.slots.flatMap(slot => [
      authored(slot.heading), ...slot.body.map(authored)
    ]).concat(entity.relationships.projects, entity.relationships.patterns).join(" ");
    return text.toLocaleLowerCase(state.lang).includes(needle);
  });
  $("#results").textContent = ui[state.lang].entries(filtered.length);
  $("#entity-grid").replaceChildren(...filtered.map(entityCard));
}

function render() {
  renderChrome();
  renderEntities();
}

document.querySelectorAll("[data-lang]").forEach(button => button.addEventListener("click", () => {
  state.lang = button.dataset.lang;
  remember("argh-language", state.lang);
  render();
}));

document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {
  state.view = button.dataset.view;
  remember("argh-reader", state.view);
  render();
}));

$("#search").addEventListener("input", event => {
  state.search = event.target.value.trim();
  renderEntities();
});

async function loadEntities() {
  const indexResponse = await fetch(`${dataRoot}/entities/index.json`);
  if (!indexResponse.ok) throw new Error("index unavailable");
  const index = await indexResponse.json();
  const prefix = `${entityType}s/`;
  const paths = Object.keys(index.entries).filter(path => path.startsWith(prefix));
  const entities = await Promise.all(paths.map(async path => {
    const response = await fetch(`${dataRoot}/entities/${path}`);
    if (!response.ok) throw new Error(`entity unavailable: ${path}`);
    return response.json();
  }));
  state.entities = entities.sort((left, right) => left.slug.localeCompare(right.slug));
  render();
}

renderChrome();
$("#results").textContent = ui[state.lang].loading;
loadEntities().catch(() => { $("#results").textContent = ui[state.lang].error; });
