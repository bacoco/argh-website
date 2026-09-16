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
VERSION = "1.5.0"
PLURAL = {"dossier": "dossiers", "project": "projects", "pattern": "patterns"}

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
        nav("/dossiers/", "dossiers", "Dossiers", section),
        nav("/patterns/", "patterns", '<span class="nav-en">Patterns</span><span class="nav-fr">Motifs</span>', section),
        nav("/projects/", "projects", '<span class="nav-en">Projects</span><span class="nav-fr">Projets</span>', section),
        nav("/atlas/", "atlas", "Atlas", section),
        nav("/about/", "about", '<span class="nav-en">About</span><span class="nav-fr">À propos</span>', section),
    ]))
    return ('<header class="argh-top"><div class="argh-topin">'
      '<a class="argh-brand" href="/" aria-label="ARGH">'
      '<img src="/assets/logo.png" alt="ARGH — Agent Reliability &amp; Guard for Harnesses" loading="eager"></a>'
      '<nav class="argh-nav">' + n + '</nav>'
      '<div class="argh-controls">'
      '<div class="argh-toggle argh-reader">'
      '<button type="button" data-reader="simple"><span class="nav-en">Kitchen</span><span class="nav-fr">Cuisine</span></button>'
      '<button type="button" data-reader="expert"><span class="nav-en">Technical</span><span class="nav-fr">Technique</span></button></div>'
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
        chips.append('<a class="argh-chip" href="/projects/%s/">%s</a>' % (esc(sanitize_title(name)), esc(name)))
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

LATEST_N = 12
TOP_PATTERNS_N = 12

def entry_date(e):
    """Date éditoriale d'une entrée : celle de la source qui l'a fait découvrir.

    `published_at` est la seule autorité. `updated_at` est un tampon de migration
    — il ne vaut que comme ordre de repli, et n'est jamais affiché comme une date.
    """
    return e.get("published_at")

def sort_key(e):
    return (entry_date(e) or e.get("updated_at") or "", e.get("slug") or "")

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
    "fr": {"cuisine": "Ce qui casse quand la brigade n\u2019est plus humaine",
           "expert": "D\u00e9faillances de harnais, \u00e9tablies et document\u00e9es"},
    "en": {"kitchen": "What breaks when the brigade is no longer human",
           "expert": "Harness failures, established and documented"}}

HOME_DECK = {
    "fr": {"cuisine": "Un bon cuisinier ne suffit pas. Il faut encore que les commandes "
                      "arrivent, que les postes soient tenus, et que quelqu\u2019un regarde "
                      "l\u2019assiette avant qu\u2019elle parte. On raconte ici ce qui a rat\u00e9 dans "
                      "ces cuisines-l\u00e0, et ce qu\u2019il fallait faire \u00e0 la place.",
           "expert": "ARGH documente les d\u00e9faillances op\u00e9rationnelles des harnais "
                     "d\u2019agents : ce qui a \u00e9t\u00e9 reproduit, ce qui a \u00e9t\u00e9 corrig\u00e9, ce qui reste "
                     "ouvert. Chaque dossier nomme son \u00e9tat de preuve."},
    "en": {"kitchen": "A good cook is not enough. The orders still have to arrive, the "
                      "stations have to be held, and someone has to look at the plate "
                      "before it leaves. This is what went wrong in those kitchens, and "
                      "what should have been done instead.",
           "expert": "ARGH documents operational failures in agent harnesses: what was "
                     "reproduced, what was fixed, what remains open. Every dossier names "
                     "its evidence state."}}

HOME_LATEST = {
    "fr": {"cuisine": "Ce qui vient d\u2019arriver", "expert": "Derni\u00e8res entr\u00e9es"},
    "en": {"kitchen": "What just came in", "expert": "Latest entries"}}

HOME_RECURRING = {
    "fr": {"cuisine": "Les m\u00eames rat\u00e9s, d\u2019une cuisine \u00e0 l\u2019autre",
           "expert": "Motifs r\u00e9currents"},
    "en": {"kitchen": "The same mistakes, kitchen after kitchen",
           "expert": "Recurring patterns"}}

def home(store):
    """L'accueil est fabriqu\u00e9 depuis le magasin d'entit\u00e9s, comme toute autre page.

    Il n'utilise que des classes d\u00e9finies par renderer.css : une page servie avec
    un vocabulaire que la feuille ignore ne masque rien et ne met rien en forme.
    """
    ds = sorted([e for e in store["items"] if e.get("type") == "dossier"],
                key=sort_key, reverse=True)
    ps = [e for e in store["items"] if e.get("type") == "pattern"]
    pr = [e for e in store["items"] if e.get("type") == "project"]

    counts = {}
    for e in ds:
        for m in (e.get("relationships") or {}).get("patterns", []):
            counts[m] = counts.get(m, 0) + 1
    top = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:TOP_PATTERNS_N]

    body = ('<div class="argh-site argh-index" data-argh-renderer="%s">%s'
            '<main class="argh-wrap">'
            '<section class="argh-index-hero"><div class="argh-kicker">ARGH</div>%s%s</section>'
            '<div class="argh-atlas-stats">'
            '<div class="argh-stat"><b>%d</b><span>Dossiers</span></div>'
            '<div class="argh-stat"><b>%d</b><span><span class="nav-fr">Motifs</span>'
            '<span class="nav-en">Patterns</span></span></div>'
            '<div class="argh-stat"><b>%d</b><span><span class="nav-fr">Projets</span>'
            '<span class="nav-en">Projects</span></span></div></div>'
            % (VERSION, header("home"), quad(HOME_TITLE, "h1"),
               quad(HOME_DECK, "p", "argh-standfirst"), len(ds), len(ps), len(pr)))

    body += '<section class="argh-section">%s<div class="argh-index-grid">%s</div></section>' % (
        section_head(HOME_LATEST), "".join(card(e) for e in ds[:LATEST_N]))

    cards = ""
    for slug, n in top:
        e = store["patterns"].get(slug)
        if not e: continue
        h = slot_of(e, "hero")
        cards += ('<a class="argh-index-card" href="%s">'
                  '<div class="argh-card-meta"><span class="argh-count">%d</span></div>%s</a>'
                  % (esc(e["route"]), n, quad(h["heading"], "h2")))
    body += '<section class="argh-section">%s<div class="argh-index-grid">%s</div></section>' % (
        section_head(HOME_RECURRING), cards)

    body += FOOT + "</main></div>"
    return page("ARGH \u2014 Pannes, correctifs et le\u00e7ons des harnais IA", body,
                "Intelligence ind\u00e9pendante sur les harnais d'agents : pannes v\u00e9rifi\u00e9es, "
                "m\u00e9canismes et le\u00e7ons.")

def about(store):
    blk = (ROOT / "recovered" / "about.html").read_text(encoding="utf-8")
    body = ('<div class="argh-site" data-argh-renderer="%s">%s'
            '<main class="argh-wrap">%s</main>%s</div>' % (VERSION, header("about"), blk, FOOT))
    return page("À propos — ARGH", body, "Ce qu'est ARGH et comment ses dossiers sont établis.")

def main():
    idx = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    store = {"items": [], "by_route": {}, "patterns": {}}
    for rel in sorted(idx["entries"]):
        e = json.loads((DATA / rel).read_text(encoding="utf-8"))
        store["items"].append(e); store["by_route"][e["route"]] = e
        if e["type"] == "pattern": store["patterns"][e["slug"]] = e
    n = 0
    for e in store["items"]:
        out = ROOT / PLURAL[e["type"]] / e["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(detail(e, store), encoding="utf-8"); n += 1
    for t in ("dossier", "project", "pattern"):
        (ROOT / PLURAL[t] / "index.html").write_text(index(t, store), encoding="utf-8")
    (ROOT / "atlas").mkdir(exist_ok=True)
    (ROOT / "atlas" / "index.html").write_text(atlas(store), encoding="utf-8")
    (ROOT / "index.html").write_text(home(store), encoding="utf-8")
    (ROOT / "about").mkdir(exist_ok=True)
    (ROOT / "about" / "index.html").write_text(about(store), encoding="utf-8")
    (ROOT / "404.html").write_text(page("404 — ARGH",
        '<div class="argh-site">%s<main class="argh-wrap"><article class="argh-article">'
        '<h1>404</h1><p class="argh-standfirst">Cette page n’existe pas.</p>'
        '<div class="argh-chips"><a class="argh-chip" href="/dossiers/">Dossiers</a>'
        '<a class="argh-chip" href="/patterns/">Motifs</a><a class="argh-chip" href="/projects/">Projets</a></div>'
        '</article>%s</main></div>' % (header(), FOOT)), encoding="utf-8")
    print("  %d pages d'entité + 3 index + atlas + accueil + 404" % n)

if __name__ == "__main__":
    main()
