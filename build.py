#!/usr/bin/env python3
"""Génère le site statique ARGH avec le balisage exact du renderer WordPress 1.5.0.

Port fidèle de publication/argh/renderer/argh-renderer.php : mêmes classes, même
ordre, mêmes quatre variantes dans le DOM. Le CSS et le JS sont ceux du plugin,
copiés sans modification ; c'est donc le même rendu, servi en statique.
"""
import json, html, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "entities"
TAXONOMY = ROOT / "data" / "taxonomy.json"
ACTIVITY = ROOT / "data" / "activity.json"
VERSION = "1.6.1"
PLURAL = {"dossier": "dossiers", "project": "projects", "pattern": "patterns"}
PLACE_ILLUSTRATIONS = {
    "objectifs-instructions": "/assets/illustrations/category-objectives-instructions-320.jpg",
    "dependances-externes": "/assets/illustrations/category-external-dependencies-320.jpg",
    "entrees-declencheurs": "/assets/illustrations/category-inputs-triggers-320.jpg",
    "donnees-memoire-etat": "/assets/illustrations/category-data-memory-state-320.jpg",
    "configuration-environnement": "/assets/illustrations/category-configuration-environment-320.jpg",
    "isolation-concurrence": "/assets/illustrations/category-isolation-concurrency-320.jpg",
    "roles-orchestration": "/assets/illustrations/category-roles-orchestration-320.jpg",
    "outils-infrastructure": "/assets/illustrations/category-tools-infrastructure-320.jpg",
    "execution-cycle-vie": "/assets/illustrations/category-execution-lifecycle-320.jpg",
    "validation-preuves": "/assets/illustrations/category-validation-evidence-320.jpg",
    "publication-resultat": "/assets/illustrations/category-publication-outcome-320.jpg",
    "couts-quotas": "/assets/illustrations/category-costs-quotas-320.jpg",
    "annulation-recuperation": "/assets/illustrations/category-cancellation-recovery-320.jpg",
    "historique-tracabilite": "/assets/illustrations/category-history-traceability-320.jpg",
}

def esc(s): return html.escape(s or "", quote=True)

def sanitize_title(name):
    """Équivalent de sanitize_title() de WordPress, pour les libellés de projet."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def quad(q, tag="span", cls=""):
    q = q or {}
    fr, en = q.get("fr") or {}, q.get("en") or {}
    modes = [("fr-cuisine", fr.get("cuisine", "")),
             ("fr-specialist", fr.get("expert", fr.get("specialist", ""))),
             ("en-kitchen", en.get("kitchen", "")),
             ("en-specialist", en.get("expert", en.get("specialist", "")))]
    out = '<%s class="argh-q%s">' % (tag, (" " + esc(cls)) if cls else "")
    for mode, text in modes:
        out += '<span class="argh-mode argh-%s">%s</span>' % (mode, esc(text))
    return out + "</%s>" % tag

def nav(href, section, body, current):
    cur = ' aria-current="page"' if current == section else ""
    return '<a href="%s"%s>%s</a>' % (esc(href), cur, body)

def header(section=""):
    n = ("".join([
        nav("/", "home", '<span class="nav-en">Home</span><span class="nav-fr">Accueil</span>', section),
        nav("/dossiers/", "dossiers", "Dossiers", section),
        nav("/patterns/", "patterns", '<span class="nav-en">Patterns</span><span class="nav-fr">Motifs</span>', section),
        nav("/projects/", "projects", '<span class="nav-en">Projects</span><span class="nav-fr">Projets</span>', section),
        nav("/atlas/", "atlas", "Atlas", section),
        nav("/glossary/", "glossary", '<span class="nav-en">Glossary</span><span class="nav-fr">Glossaire</span>', section),
        nav("/about/", "about", '<span class="nav-en">About</span><span class="nav-fr">À propos</span>', section),
    ]))
    return ('<header class="argh-top"><div class="argh-topin">'
      '<a class="argh-brand" href="/" aria-label="ARGH">'
      '<img src="/assets/logo-imagine.png" alt="ARGH — Agent Reliability &amp; Guard for Harnesses" loading="eager"></a>'
      '<nav class="argh-nav">' + n + '</nav>'
      '<div class="argh-controls">'
      '<div class="argh-toggle argh-reader">'
      '<button type="button" data-reader="simple"><span class="nav-en">Kitchen</span><span class="nav-fr">Cuisine</span></button>'
      '<button type="button" data-reader="expert"><span class="nav-en">Expert</span><span class="nav-fr">Expert</span></button></div>'
      '<div class="argh-toggle argh-lang">'
      '<button type="button" data-lang="en">EN</button>'
      '<button type="button" data-lang="fr">FR</button></div></div></div></header>')

FOOT = ('<footer class="argh-foot"><span>ARGH — Agent Reliability &amp; Guard for Harnesses</span>'
        '<a href="https://github.com/bacoco/argh-website">GitHub</a></footer>')

def page(title, body, desc=""):
    return ("<!doctype html>\n<html lang=\"fr-FR\">\n<head>\n"
      '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
      '<title>%s</title>\n<meta name="description" content="%s">\n'
      '<link rel="icon" href="/assets/logo.png">\n'
      '<link rel="stylesheet" href="/assets/renderer.css?v=%s">\n'
      '<script src="/assets/renderer.js?v=%s" defer></script>\n</head>\n'
      '<body class="argh-fr argh-reader-simple argh-rendered-page">\n%s\n</body>\n</html>\n'
      % (esc(title), esc(desc), VERSION, VERSION, body))

def slot_of(e, sid):
    for s in e.get("slots", []):
        if s.get("id") == sid: return s
    return None

def pattern_heading(slug, store):
    e = store["patterns"].get(slug)
    h = slot_of(e, "hero") if e else None
    return h.get("heading") if h else None

def relationships(e, store):
    r = e.get("relationships") or {}
    chips = []
    for name in r.get("projects", []):
        href = "/projects/%s/" % esc(sanitize_title(name))
        # Source attribution belongs to Expert. Cuisine/Kitchen receives the
        # self-contained scene and must not expose the originating product.
        for mode in ("fr-specialist", "en-specialist"):
            chips.append('<a class="argh-chip argh-mode argh-%s" href="%s">%s</a>'
                         % (mode, href, esc(name)))
    for slug in r.get("patterns", []):
        h = pattern_heading(slug, store)
        if not h: continue
        chips.append('<a class="argh-chip" href="/patterns/%s/">%s</a>' % (esc(slug), quad(h, "span", "argh-chip-label")))
    return '<div class="argh-chips">%s</div>' % "".join(chips) if chips else ""

def context(t):
    q = {"dossier": ("Dossier", "Dossier"), "project": ("Projet", "Project"),
         "pattern": ("Motif", "Pattern")}.get(t, ("ARGH", "ARGH"))
    return '<div class="argh-context"><span class="nav-fr">%s</span><span class="nav-en">%s</span></div>' % q

def render_slot(s):
    out = '<section class="argh-section argh-kind-%s">%s' % (esc(s.get("kind", "section")), quad(s.get("heading"), "h2"))
    for p in s.get("body", []): out += quad(p, "p")
    return out + "</section>"

def related(e, store):
    rels = (e.get("relationships") or {}).get("dossiers") or []
    if not rels: return ""
    out = ('<section class="argh-related"><div class="argh-section-head"><h2>'
           '<span class="nav-en">Related dossiers</span><span class="nav-fr">Dossiers associés</span>'
           '</h2></div><div class="argh-related-grid">')
    for slug in rels[:36]:
        x = store["by_route"].get("/dossiers/%s/" % slug)
        if not x: continue
        h = slot_of(x, "hero")
        out += '<a class="argh-related-card" href="%s">%s</a>' % (esc(x["route"]), quad(h["heading"], "h3", "argh-related-title"))
    return out + "</div></section>"

def detail(e, store):
    h = slot_of(e, "hero")
    body = ('<div class="argh-site" data-argh-renderer="%s" data-argh-route="%s">%s'
            '<main class="argh-wrap"><article class="argh-article">%s%s%s%s'
            % (VERSION, esc(e["route"]), header(PLURAL[e["type"]]), context(e["type"]),
               quad(h["heading"], "h1"), quad((h.get("body") or [{}])[0], "p", "argh-standfirst"),
               relationships(e, store)))
    for s in e.get("slots", []):
        if s.get("id") != "hero": body += render_slot(s)
    if e.get("type") != "dossier": body += related(e, store)
    body += "</article>" + FOOT + "</main></div>"
    title = (h["heading"]["fr"]["cuisine"] or e["slug"]) + " — ARGH"
    desc = ((h.get("body") or [{}])[0].get("fr", {}) or {}).get("expert", "")
    return page(title, body, desc[:180])

def index(t, store):
    items = sorted([e for e in store["items"] if e.get("type") == t], key=lambda e: e["slug"])
    label = {"dossier": ("Dossiers", "Dossiers"), "project": ("Projets", "Projects"),
             "pattern": ("Motifs", "Patterns")}[t]
    body = ('<div class="argh-site argh-index" data-argh-renderer="%s">%s'
            '<main class="argh-wrap"><section class="argh-index-hero"><div class="argh-kicker">ARGH</div>'
            '<h1><span class="nav-fr">%s</span><span class="nav-en">%s</span></h1>'
            '<div class="argh-index-count">%d <span class="nav-fr">entrées</span><span class="nav-en">entries</span></div>'
            '</section><section class="argh-index-grid">'
            % (VERSION, header(PLURAL[t]), label[0], label[1], len(items)))
    for e in items:
        h = slot_of(e, "hero")
        body += ('<a class="argh-index-card" href="%s">%s%s</a>'
                 % (esc(e["route"]), quad(h["heading"], "h2"),
                    quad((h.get("body") or [{}])[0], "p", "argh-card-summary")))
    body += "</section>" + FOOT + "</main></div>"
    return page("%s — ARGH" % label[0], body, "%d %s publiés par ARGH." % (len(items), label[0].lower()))

def atlas(store):
    ds = [e for e in store["items"] if e.get("type") == "dossier"]
    pc, mc = {}, {}
    for e in ds:
        for p in (e.get("relationships") or {}).get("projects", []): pc[p] = pc.get(p, 0) + 1
        for m in (e.get("relationships") or {}).get("patterns", []): mc[m] = mc.get(m, 0) + 1
    ps = [k for k, _ in sorted(pc.items(), key=lambda x: -x[1])][:8]
    ms = [k for k, _ in sorted(mc.items(), key=lambda x: -x[1])][:16]
    title = {"fr": {"cuisine": "Mêmes postes. Des garanties différentes.", "expert": "Mêmes primitives. Garanties différentes."},
             "en": {"kitchen": "Same stations. Different guarantees.", "expert": "Same primitives. Different guarantees."}}
    deck = {"fr": {"cuisine": "Cette carte montre où les mêmes problèmes reviennent d’une cuisine à l’autre.",
                   "expert": "L’Atlas est dérivé du graphe public complet des entités ARGH."},
            "en": {"kitchen": "This map shows where the same problems recur across different kitchens.",
                   "expert": "The Atlas is derived from the complete public ARGH entity graph."}}
    body = ('<div class="argh-site argh-atlas" data-argh-renderer="%s">%s'
            '<main class="argh-wrap"><section class="argh-index-hero"><div class="argh-kicker">Atlas</div>%s%s</section>'
            '<div class="argh-atlas-stats"><div class="argh-stat"><b>%d</b><span>Dossiers</span></div>'
            '<div class="argh-stat"><b>%d</b><span><span class="nav-fr">Projets</span><span class="nav-en">Projects</span></span></div>'
            '<div class="argh-stat"><b>%d</b><span><span class="nav-fr">Motifs</span><span class="nav-en">Patterns</span></span></div></div>'
            '<section class="argh-section"><div class="argh-atlas-wrap"><table class="argh-atlas-table"><thead><tr>'
            '<th><span class="nav-fr">Motif</span><span class="nav-en">Pattern</span></th>'
            % (VERSION, header("atlas"), quad(title, "h1"), quad(deck, "p", "argh-standfirst"), len(ds), len(pc), len(mc)))
    for p in ps: body += "<th>%s</th>" % esc(p)
    body += "</tr></thead><tbody>"
    for m in ms:
        h = pattern_heading(m, store)
        if not h: continue
        body += "<tr><td>%s</td>" % quad(h)
        for p in ps:
            n = sum(1 for e in ds
                    if p in ((e.get("relationships") or {}).get("projects") or [])
                    and m in ((e.get("relationships") or {}).get("patterns") or []))
            body += "<td>%s</td>" % ('<span class="argh-count">%d</span>' % n if n else "—")
        body += "</tr>"
    body += "</tbody></table></div></section>" + FOOT + "</main></div>"
    return page("Atlas — ARGH", body, "Carte des motifs récurrents entre projets.")

LATEST_N = 6

def entry_date(e):
    """Return the documented incident date only when it is evidence-backed."""
    return e.get("event_date") if e.get("date_basis") == "incident" else None

def sort_key(e):
    return (e.get("event_date") or "", e.get("updated_at") or "", e.get("slug") or "")

def card(e):
    h = slot_of(e, "hero")
    d = entry_date(e)
    meta = ('<div class="argh-card-meta"><time datetime="%s">%s</time></div>'
            % (esc(d), esc(d[:10]))) if d else ""
    return ('<a class="argh-index-card" href="%s">%s%s%s</a>'
            % (esc(e["route"]), meta, quad(h["heading"], "h2"),
               quad((h.get("body") or [{}])[0], "p", "argh-card-summary")))

def section_head(q):
    return '<div class="argh-section-head">%s</div>' % quad(q, "h2")

HOME_TITLE = {
    "fr": {"cuisine": "Comment les harnais d’agents travaillent, se trompent et s’améliorent.",
           "expert": "État des lieux et post-mortems des harnais d’agents."},
    "en": {"kitchen": "How agent harnesses work, make mistakes and improve.",
           "expert": "Agent harness landscape and post-mortems."}}

HOME_DECK = {
    "fr": {"cuisine": "ARGH observe l’usine à harnais. Chaque fiche raconte un incident réel comme un service de cuisine : ce qui s’est passé, ce que le raté a provoqué et comment le voir venir.",
           "expert": "ARGH cartographie les harnais d’agents. Chaque dossier documente un incident réel, ses preuves, son mécanisme, son impact et ses signaux précurseurs."},
    "en": {"kitchen": "ARGH watches the harness factory. Each card tells a real incident as a kitchen service: what happened, what the mistake caused and how to see it coming.",
           "expert": "ARGH maps agent harnesses. Each dossier documents a real incident, its evidence, mechanism, impact and leading signals."}}

HOME_IDENTITY_TITLE = {
    "fr": {"cuisine": "Ce que rassemble ARGH", "expert": "Ce que documente ARGH"},
    "en": {"kitchen": "What ARGH brings together", "expert": "What ARGH documents"}}

HOME_IDENTITY = [
    {"fr": {"cuisine": "Les harnais qui existent aujourd’hui", "expert": "La cartographie des harnais existants"},
     "en": {"kitchen": "The harnesses that exist today", "expert": "The current harness landscape"}},
    {"fr": {"cuisine": "Les erreurs rencontrées pendant le service", "expert": "Les incidents et mécanismes de défaillance"},
     "en": {"kitchen": "Mistakes encountered during service", "expert": "Incidents and failure mechanisms"}},
    {"fr": {"cuisine": "Les post-mortems qui expliquent pourquoi", "expert": "Les post-mortems fondés sur les preuves"},
     "en": {"kitchen": "Post-mortems that explain why", "expert": "Evidence-based post-mortems"}},
    {"fr": {"cuisine": "Les signes à surveiller avant la prochaine panne", "expert": "Les axes de surveillance et signaux précurseurs"},
     "en": {"kitchen": "Signs to watch before the next failure", "expert": "Monitoring axes and leading signals"}},
]

HOME_LATEST = {
    "fr": {"cuisine": "Ce qui vient d’arriver", "expert": "Incidents nouveaux ou mis à jour"},
    "en": {"kitchen": "What just came in", "expert": "New or updated incidents"}}

HOME_LATEST_DECK = {
    "fr": {"cuisine": "Toute nouvelle histoire apparaît ici, même si la cuisine ne sait pas encore où la ranger.",
           "expert": "Tout nouvel incident apparaît ici, y compris lorsqu’aucun concept existant ne permet encore de le classer."},
    "en": {"kitchen": "Every new story appears here, even when the kitchen does not yet know where it belongs.",
           "expert": "Every new incident appears here, including when no existing concept can classify it yet."}}

HOME_MAP = {
    "fr": {"cuisine": "Explorer toute la cuisine", "expert": "Explorer tout le cycle"},
    "en": {"kitchen": "Explore the whole kitchen", "expert": "Explore the whole lifecycle"}}

HOME_MAP_DECK = {
    "fr": {"cuisine": "Toutes les fiches sont rangées du menu au cahier de la maison.",
           "expert": "Tous les dossiers sont classés de la définition à la traçabilité."},
    "en": {"kitchen": "Every card is arranged from the menu to the house notebook.",
           "expert": "Every dossier is classified from definition to traceability."}}

UNCLASSIFIED = {
    "fr": {"cuisine": "Sujets à ranger", "expert": "Incidents non classés"},
    "en": {"kitchen": "Stories to put away", "expert": "Unclassified incidents"}}

STATUS = {
    "new": {
        "fr": {"cuisine": "Nouvelle fiche", "expert": "Nouvel incident"},
        "en": {"kitchen": "New card", "expert": "New incident"}},
    "updated": {
        "fr": {"cuisine": "Fiche enrichie", "expert": "Dossier mis à jour"},
        "en": {"kitchen": "Expanded card", "expert": "Updated dossier"}},
    "recent": {
        "fr": {"cuisine": "À découvrir", "expert": "Incident récent"},
        "en": {"kitchen": "Discover", "expert": "Recent incident"}},
    "unclassified": {
        "fr": {"cuisine": "À ranger", "expert": "Incident non classé"},
        "en": {"kitchen": "To put away", "expert": "Unclassified incident"}},
}

UNCLASSIFIED_PLACE = {
    "fr": {"cuisine": "Visible dès son arrivée", "expert": "Taxonomie à réviser"},
    "en": {"kitchen": "Visible as soon as it arrives", "expert": "Taxonomy review required"}}

def latest_dossiers(store):
    """Return real activity first, then fill the initial baseline with recent incidents."""
    selected, seen = [], set()
    for event in store["activity"]:
        e = store["by_rel"].get(event["entity_path"])
        if not e or e.get("type") != "dossier" or e["slug"] in seen:
            continue
        selected.append((e, event["kind"]))
        seen.add(e["slug"])
        if len(selected) == LATEST_N:
            return selected
    dossiers = sorted(
        [e for e in store["items"] if e.get("type") == "dossier"],
        key=sort_key,
        reverse=True,
    )
    for e in dossiers:
        if e["slug"] in seen:
            continue
        selected.append((e, "recent"))
        seen.add(e["slug"])
        if len(selected) == LATEST_N:
            break
    return selected


def update_card(e, kind, store):
    h = slot_of(e, "hero")
    place_id = store["assignments"].get(e["slug"])
    place = store["place_by_id"].get(place_id)
    unclassified = place is None
    status = STATUS["unclassified" if unclassified else kind]
    location = place["label"] if place else UNCLASSIFIED_PLACE
    classes = "argh-update-card" + (" argh-unclassified" if unclassified else "")
    return ('<a class="%s" href="%s">%s%s%s%s</a>'
            % (classes, esc(e["route"]), quad(status, "span", "argh-update-status"),
               quad(location, "span", "argh-update-place"),
               quad(h["heading"], "h3"),
               quad((h.get("body") or [{}])[0], "p")))


def place_card(place, number, store):
    dossiers = store["dossiers_by_place"].get(place["id"], [])
    illustration = PLACE_ILLUSTRATIONS.get(place["id"])
    classes = "argh-place-card" + (" argh-place-card-illustrated" if illustration else "")
    picture = (
        '<picture class="argh-place-card-picture"><img src="%s" width="320" height="213" '
        'alt="" aria-hidden="true" loading="lazy" decoding="async"></picture>' % esc(illustration)
        if illustration else ""
    )
    count = {
        "fr": {"cuisine": "%d fiche%s" % (len(dossiers), "s" if len(dossiers) != 1 else ""),
               "expert": "%d dossier%s" % (len(dossiers), "s" if len(dossiers) != 1 else "")},
        "en": {"kitchen": "%d card%s" % (len(dossiers), "s" if len(dossiers) != 1 else ""),
               "expert": "%d dossier%s" % (len(dossiers), "s" if len(dossiers) != 1 else "")},
    }
    return ('<a class="%s" data-number="%02d" href="/places/%s/">'
            '<span class="argh-place-number">%02d</span>%s%s%s%s</a>'
            % (classes, number, esc(place["id"]), number, picture, quad(place["label"], "h3"),
               quad(place["description"], "p"), quad(count, "span", "argh-place-count")))


def place_page(place, store):
    items = store["dossiers_by_place"].get(place["id"], [])
    illustration = PLACE_ILLUSTRATIONS.get(place["id"])
    hero_class = " argh-place-hero-illustrated" if illustration else ""
    picture = (
        '<picture class="argh-place-hero-illustration"><img src="%s" width="320" height="213" '
        'alt="" aria-hidden="true" decoding="async"></picture>' % esc(illustration)
        if illustration else ""
    )
    body = ('<div class="argh-site argh-index" data-argh-renderer="%s">%s'
            '<main class="argh-wrap"><section class="argh-index-hero%s"><div class="argh-place-hero-copy">'
            '<div class="argh-kicker"><a href="/">ARGH</a> · <span class="nav-fr">Carte</span><span class="nav-en">Map</span></div>'
            '%s%s%s<div class="argh-index-count">%d <span class="nav-fr">dossiers</span><span class="nav-en">dossiers</span></div>'
            '</div>%s</section><section class="argh-index-grid">%s</section>%s</main></div>'
            % (VERSION, header("home"), hero_class, quad(place["label"], "h1"),
               quad(place["description"], "p", "argh-standfirst"),
               quad(place["meaning"], "p", "argh-place-meaning"), len(items), picture,
               "".join(card(e) for e in items), FOOT))
    return page("%s — ARGH" % place["label"]["fr"]["expert"], body,
                place["description"]["fr"]["expert"])


def home(store):
    body = ('<div class="argh-site argh-index" data-argh-renderer="%s">%s'
            '<main class="argh-wrap">'
            '<section class="argh-home-hero"><div class="argh-home-intro"><div class="argh-kicker">ARGH — Agent Reliability &amp; Guard for Harnesses</div>%s%s</div>'
            '<picture class="argh-home-illustration">'
            '<source srcset="/assets/illustrations/kitchen-system-home-480.jpg 480w, '
            '/assets/illustrations/kitchen-system-home-960.jpg 960w" '
            'sizes="(max-width:700px) calc(100vw - 34px), (max-width:920px) 42vw, 260px">'
            '<img src="/assets/illustrations/kitchen-system-home-480.jpg" width="480" height="320" '
            'alt="" aria-hidden="true" decoding="async" fetchpriority="high"></picture>'
            '<aside class="argh-home-identity">%s<ul>%s</ul></aside></section>'
            % (VERSION, header("home"), quad(HOME_TITLE, "h1"),
               quad(HOME_DECK, "p", "argh-standfirst"), quad(HOME_IDENTITY_TITLE, "strong"),
               "".join(quad(item, "li") for item in HOME_IDENTITY)))

    body += ('<section class="argh-updates"><div class="argh-updates-head"><div>%s</div>%s</div>'
             '<div class="argh-update-grid">%s</div></section>'
             % (quad(HOME_LATEST, "h2"), quad(HOME_LATEST_DECK, "p"),
                "".join(update_card(e, kind, store) for e, kind in latest_dossiers(store))))

    if store["unclassified"]:
        body += ('<section class="argh-unclassified-section">%s<div class="argh-update-grid">%s</div></section>'
                 % (section_head(UNCLASSIFIED),
                    "".join(update_card(e, "recent", store) for e in store["unclassified"])))

    body += ('<section class="argh-map"><div class="argh-map-intro">%s%s</div>'
             % (quad(HOME_MAP, "h2"), quad(HOME_MAP_DECK, "p")))
    number = 1
    for phase in store["phases"]:
        body += '<div class="argh-phase-head">%s%s</div><div class="argh-place-grid">' % (
            quad(phase["label"], "h3"), quad(phase["description"], "p"))
        for place in [p for p in store["places"] if p["phase"] == phase["id"]]:
            body += place_card(place, number, store)
            number += 1
        body += "</div>"
    body += "</section>"

    body += FOOT + "</main></div>"
    return page("ARGH — État des lieux et post-mortems des harnais d’agents", body,
                "État des lieux, incidents, post-mortems et signaux à surveiller pour les harnais d’agents.")

def about(store):
    blk = (ROOT / "recovered" / "about.html").read_text(encoding="utf-8")
    body = ('<div class="argh-site" data-argh-renderer="%s">%s'
            '<main class="argh-wrap">%s</main>%s</div>' % (VERSION, header("about"), blk, FOOT))
    return page("À propos — ARGH", body, "Ce qu'est ARGH et comment ses dossiers sont établis.")


def glossary_column(place, reader):
    fr_key, en_key = ("cuisine", "kitchen") if reader == "kitchen" else ("expert", "expert")
    label = place["label"]
    description = place["description"]
    meaning = place["meaning"]
    heading = "Cuisine" if reader == "kitchen" else "Expert"
    return ('<article class="argh-glossary-column argh-glossary-%s">'
            '<div class="argh-glossary-reader">%s</div>'
            '<h3><span class="nav-fr">%s</span><span class="nav-en">%s</span></h3>'
            '<p class="argh-glossary-summary"><span class="nav-fr">%s</span><span class="nav-en">%s</span></p>'
            '<p><span class="nav-fr">%s</span><span class="nav-en">%s</span></p></article>'
            % (reader, heading, esc(label["fr"][fr_key]), esc(label["en"][en_key]),
               esc(description["fr"][fr_key]), esc(description["en"][en_key]),
               esc(meaning["fr"][fr_key]), esc(meaning["en"][en_key])))


def glossary(store):
    entries = []
    for number, place in enumerate(store["places"], 1):
        illustration = PLACE_ILLUSTRATIONS[place["id"]]
        picture = ('<picture class="argh-glossary-picture"><img src="%s" width="320" height="213" '
                   'alt="" aria-hidden="true" loading="lazy" decoding="async"></picture>'
                   % esc(illustration))
        entries.append(
            '<section class="argh-glossary-entry" id="%s">'
            '<div class="argh-glossary-entry-head"><div class="argh-glossary-marker"><span>%02d</span>%s</div>'
            '<a href="/places/%s/"><span class="nav-fr">Voir les dossiers</span>'
            '<span class="nav-en">View dossiers</span></a></div>'
            '<div class="argh-glossary-pair">%s%s</div></section>'
            % (esc(place["id"]), number, picture, esc(place["id"]),
               glossary_column(place, "kitchen"), glossary_column(place, "expert"))
        )
    body = ('<div class="argh-site argh-index" data-argh-renderer="%s">%s'
            '<main class="argh-wrap"><section class="argh-index-hero argh-glossary-hero">'
            '<div class="argh-kicker">ARGH</div>'
            '<h1><span class="nav-fr">Glossaire Cuisine ↔ Expert</span>'
            '<span class="nav-en">Kitchen ↔ Expert glossary</span></h1>'
            '<p class="argh-standfirst"><span class="nav-fr">Chaque catégorie est expliquée côte à côte : '
            'l’image de cuisine à gauche, sa signification technique exacte à droite.</span>'
            '<span class="nav-en">Every category is explained side by side: the kitchen image on the left, '
            'its exact technical meaning on the right.</span></p></section>%s%s</main></div>'
            % (VERSION, header("glossary"), "".join(entries), FOOT))
    return page("Glossaire — ARGH", body, "Correspondance entre les catégories Cuisine et Expert d’ARGH.")


def load_navigation(store):
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    if taxonomy.get("schema") != "argh/public-navigation/v1":
        raise ValueError("wrong public navigation schema")
    phases, places = taxonomy.get("phases"), taxonomy.get("places")
    assignments = taxonomy.get("assignments")
    if not isinstance(phases, list) or not isinstance(places, list) or not isinstance(assignments, dict):
        raise ValueError("public navigation must contain phases, places and assignments")
    phase_ids = [phase.get("id") for phase in phases]
    place_ids = [place.get("id") for place in places]
    if len(set(phase_ids)) != len(phase_ids) or len(set(place_ids)) != len(place_ids):
        raise ValueError("duplicate public navigation id")
    if any(place.get("phase") not in phase_ids for place in places):
        raise ValueError("public navigation place references an unknown phase")
    if any(place_id not in place_ids for place_id in assignments.values()):
        raise ValueError("public navigation assignment references an unknown place")

    dossiers = {e["slug"]: e for e in store["items"] if e.get("type") == "dossier"}
    dossiers_by_place = {place_id: [] for place_id in place_ids}
    for slug, place_id in assignments.items():
        if slug in dossiers:
            dossiers_by_place[place_id].append(dossiers[slug])
    for items in dossiers_by_place.values():
        items.sort(key=sort_key, reverse=True)

    activity = json.loads(ACTIVITY.read_text(encoding="utf-8"))
    if activity.get("schema") != "argh/public-activity/v1" or not isinstance(activity.get("events"), list):
        raise ValueError("wrong public activity schema")

    store.update({
        "phases": phases,
        "places": places,
        "place_by_id": {place["id"]: place for place in places},
        "assignments": assignments,
        "dossiers_by_place": dossiers_by_place,
        "unclassified": sorted(
            [entity for slug, entity in dossiers.items() if slug not in assignments],
            key=sort_key,
            reverse=True,
        ),
        "activity": activity["events"],
    })


def main():
    idx = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    store = {"items": [], "by_route": {}, "by_rel": {}, "patterns": {}}
    for rel in sorted(idx["entries"]):
        e = json.loads((DATA / rel).read_text(encoding="utf-8"))
        store["items"].append(e); store["by_route"][e["route"]] = e; store["by_rel"][rel] = e
        if e["type"] == "pattern": store["patterns"][e["slug"]] = e
    load_navigation(store)
    # Generated entity routes mirror the complete store. Remove stale routes before
    # rendering so a deleted entity cannot survive on GitHub Pages.
    for plural in PLURAL.values():
        shutil.rmtree(ROOT / plural, ignore_errors=True)
        (ROOT / plural).mkdir()
    n = 0
    for e in store["items"]:
        out = ROOT / PLURAL[e["type"]] / e["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(detail(e, store), encoding="utf-8"); n += 1
    for t in ("dossier", "project", "pattern"):
        (ROOT / PLURAL[t] / "index.html").write_text(index(t, store), encoding="utf-8")
    shutil.rmtree(ROOT / "places", ignore_errors=True)
    (ROOT / "places").mkdir()
    for place in store["places"]:
        out = ROOT / "places" / place["id"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(place_page(place, store), encoding="utf-8")
    (ROOT / "atlas").mkdir(exist_ok=True)
    (ROOT / "atlas" / "index.html").write_text(atlas(store), encoding="utf-8")
    (ROOT / "index.html").write_text(home(store), encoding="utf-8")
    (ROOT / "about").mkdir(exist_ok=True)
    (ROOT / "about" / "index.html").write_text(about(store), encoding="utf-8")
    (ROOT / "glossary").mkdir(exist_ok=True)
    (ROOT / "glossary" / "index.html").write_text(glossary(store), encoding="utf-8")
    (ROOT / "404.html").write_text(page("404 — ARGH",
        '<div class="argh-site">%s<main class="argh-wrap"><article class="argh-article">'
        '<h1>404</h1><p class="argh-standfirst">Cette page n’existe pas.</p>'
        '<div class="argh-chips"><a class="argh-chip" href="/dossiers/">Dossiers</a>'
        '<a class="argh-chip" href="/patterns/">Motifs</a><a class="argh-chip" href="/projects/">Projets</a></div>'
        '</article>%s</main></div>' % (header(), FOOT)), encoding="utf-8")
    print("  %d pages d'entité + %d endroits + 3 index + atlas + glossaire + accueil + 404" %
          (n, len(store["places"])))

if __name__ == "__main__":
    main()
