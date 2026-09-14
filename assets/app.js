const copy = {
  fr: {
    navDossiers: "Dossiers", navAtlas: "Atlas", eyebrow: "Intelligence publique · Harnais d’agents",
    metricDossiers: "dossiers publics", metricPrimitives: "primitives de contrôle",
    metricSources: "source privée exposée", edition: "Projection statique",
    fieldNotes: "Incidents → mécanismes → leçons", dossiersTitle: "Dossiers",
    searchLabel: "Rechercher un dossier", searchPlaceholder: "Rechercher…",
    controlPlane: "Plan de contrôle", atlasTitle: "Atlas", all: "Tous",
    results: count => `${count} dossier${count > 1 ? "s" : ""}`,
    open: "Lire le mécanisme", mechanism: "Mécanisme", response: "Réponse", lesson: "Leçon",
    footer: "publie des conclusions éditoriales, jamais sa provenance privée.",
    loadError: "La projection publique ne peut pas être chargée."
  },
  en: {
    navDossiers: "Cases", navAtlas: "Atlas", eyebrow: "Public intelligence · Agent harnesses",
    metricDossiers: "public cases", metricPrimitives: "control primitives",
    metricSources: "private sources exposed", edition: "Static projection",
    fieldNotes: "Incidents → mechanisms → lessons", dossiersTitle: "Cases",
    searchLabel: "Search cases", searchPlaceholder: "Search…",
    controlPlane: "Control plane", atlasTitle: "Atlas", all: "All",
    results: count => `${count} case${count > 1 ? "s" : ""}`,
    open: "Read the mechanism", mechanism: "Mechanism", response: "Response", lesson: "Lesson",
    footer: "publishes editorial conclusions, never its private provenance.",
    loadError: "The public projection could not be loaded."
  }
};

const savedLanguage = localStorage.getItem("argh-language");
const state = { lang: ["fr", "en"].includes(savedLanguage) ? savedLanguage : "fr", category: "all", query: "", dossiers: [], intel: null, meta: null };
const $ = selector => document.querySelector(selector);

function text(key) { return copy[state.lang][key]; }
function localized(item, key) { return item[`${key}_${state.lang}`] || item[key] || ""; }
function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function renderCopy() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-copy]").forEach(node => { node.textContent = text(node.dataset.copy); });
  $("#search").placeholder = text("searchPlaceholder");
  $("#language").textContent = state.lang === "fr" ? "EN" : "FR";
  $("#language").setAttribute("aria-label", state.lang === "fr" ? "Afficher le site en anglais" : "Show the site in French");
  document.title = state.lang === "fr" ? "ARGH — Atlas des harnais d’agents" : "ARGH — Agent harness atlas";
}

function renderHero() {
  $("#headline").textContent = state.intel.headline[state.lang];
  $("#deck").textContent = state.intel.headline[`deck_${state.lang}`];
  $("#dossier-count").textContent = state.dossiers.length;
  $("#atlas-count").textContent = state.intel.atlas.length;
  $("#edition-date").textContent = new Intl.DateTimeFormat(state.lang, { dateStyle: "long" }).format(new Date(state.meta.generated_at));
}

function renderCategories() {
  const root = $("#categories");
  const categories = ["all", ...new Set(state.dossiers.map(item => item.category).sort())];
  root.replaceChildren(...categories.map(category => {
    const button = el("button", "", category === "all" ? text("all") : category);
    button.type = "button";
    button.setAttribute("aria-pressed", String(state.category === category));
    button.addEventListener("click", () => { state.category = category; renderCategories(); renderDossiers(); });
    return button;
  }));
}

function dossierCard(item) {
  const card = el("article", "dossier");
  card.append(el("div", "dossier-meta", `${item.category} · ${item.projects.join(" / ")}`));
  card.append(el("h3", "", localized(item, "title")));
  card.append(el("p", "", localized(item, "summary")));
  const details = el("details");
  details.append(el("summary", "", text("open")));
  [["mechanism", "mechanism"], ["response", "response"], ["lesson", "lesson"]].forEach(([key, label]) => {
    const paragraph = el("p", key === "lesson" ? "lesson" : "");
    const strong = el("strong", "", `${text(label)}. `);
    paragraph.append(strong, document.createTextNode(localized(item, key)));
    details.append(paragraph);
  });
  card.append(details);
  return card;
}

function renderDossiers() {
  const needle = state.query.toLocaleLowerCase(state.lang);
  const filtered = state.dossiers.filter(item => {
    const inCategory = state.category === "all" || item.category === state.category;
    const haystack = [localized(item, "title"), localized(item, "summary"), item.category, ...item.projects, ...item.patterns].join(" ").toLocaleLowerCase(state.lang);
    return inCategory && haystack.includes(needle);
  });
  $("#results").textContent = text("results")(filtered.length);
  $("#dossier-grid").replaceChildren(...filtered.map(dossierCard));
}

function renderAtlas() {
  $("#atlas-grid").replaceChildren(...state.intel.atlas.map((item, index) => {
    const card = el("article", "atlas-card");
    card.append(el("div", "index", String(index + 1).padStart(2, "0")));
    card.append(el("h3", "", item.primitive));
    card.append(el("p", "", item[`why_${state.lang}`]));
    return card;
  }));
}

function render() { renderCopy(); renderHero(); renderCategories(); renderDossiers(); renderAtlas(); }

$("#language").addEventListener("click", () => {
  state.lang = state.lang === "fr" ? "en" : "fr";
  localStorage.setItem("argh-language", state.lang);
  render();
});
$("#search").addEventListener("input", event => { state.query = event.target.value.trim(); renderDossiers(); });

Promise.all([
  fetch("data/dossiers-v1.json").then(response => response.ok ? response.json() : Promise.reject()),
  fetch("data/public-intelligence.json").then(response => response.ok ? response.json() : Promise.reject()),
  fetch("data/meta.json").then(response => response.ok ? response.json() : Promise.reject())
]).then(([dossiers, intel, meta]) => {
  state.dossiers = dossiers.dossiers;
  state.intel = intel;
  state.meta = meta;
  render();
}).catch(() => { $("#headline").textContent = text("loadError"); });
