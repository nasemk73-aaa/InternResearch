# OWL Places — notes for AI agents

## Name and identity

The tool is called **OWL Places**. OWL stands for **O**penStreetMap **W**ikidata **L**ink.
The public URL is https://osm.wikidata.link/. Do not refer to it as "OSM Wikidata Matcher"
or "OSM ↔ Wikidata" — those are the old names.

## Design system

### Colour palette

| Name         | Hex       | Usage |
|--------------|-----------|-------|
| Navy         | `#1a2035` | Hero background, navbar, dark UI surfaces |
| Navy light   | `#232c47` | Navbar dropdown background |
| Amber        | `#c8973e` | Primary accent: OWL letters, buttons, active links, borders |
| Amber bright | `#dba94e` | Amber hover state |
| Cream        | `#e8dcc8` | Text on dark backgrounds |
| Cream muted  | `rgba(232,220,200,.55)` | Secondary text on dark backgrounds |
| Paper        | `#f5f3ee` | Light section backgrounds (steps, cards) |

The amber and navy pairing is inspired by old cartographic map ink on dark paper — consistent
with the mapping/geo nature of the tool.

### Typography

Both fonts are loaded from Google Fonts in `base.html` and therefore available on every page.

- **Lora** (serif, weights 600/700 + italic 400) — headings, titles, the place name in search
  results. Gives the tool a reference-book / atlas character.
- **DM Mono** (monospace, weights 400/500) — step numbers, meta pills, button labels, badges,
  elapsed timestamps in the matcher UI. Reinforces the technical/data nature of the tool.

Do not introduce other typefaces without good reason.

### Navbar

The Bootstrap `bg-primary` class is overridden globally in `matcher/static/css/style.css`.
All templates that use `class="navbar ... bg-primary"` automatically get the OWL palette —
do not add inline styles to navbars. The brand link in `navbar.html` wraps "OWL" in
`<span class="brand-owl">` so it renders in amber while "Places" stays cream.

### Key UI patterns

**Buttons** — three established styles used in search results and elsewhere:
- `.btn-run` — amber fill, navy text. Primary CTA (e.g. "Run matcher").
- `.btn-view` — navy fill, cream text. For viewing existing results.
- `.btn-browse` — amber outline. Secondary action (e.g. "Browse subdivisions").

**Status / left-border cards** — result cards use a 4px left border to communicate state
at a glance: amber = actionable, green (`#28a745`) = already matched, grey = unavailable.

**Meta pills** — small monospace tags (`.meta-pill`) for structured metadata like OSM type,
area, or category. Use `.pill-type` for the amber-tinted variant.

**Stage tracker** — the matcher progress sidebar (`matcher.html` + `ws.js`) uses a four-stage
pipeline UI: pending (grey circle), active (spinning blue border), done (green filled tick).

### Owl motif

The home page (`index.html`) includes a small inline SVG owl mark above the title. It is
amber-coloured with large round eyes and ear tufts. Keep it small (≤48px) and tasteful —
it is a brand mark, not a mascot. Do not add it to other pages.

## Template structure

- `base.html` — root layout; includes Google Fonts, Bootstrap 4, Fork Awesome, `style.css`.
- `navbar.html` — defines `navbar_inner()` and `navbar()` macros used by all pages.
- `index.html` — home page; extends `base.html`; overrides `{% block style %}` and
  `{% block content %}`.
- `results_page.html` — search results page; extends `base.html`; includes
  `search_results.html` for the card list.
- `matcher.html` — standalone full-screen layout (does not extend `base.html`); uses its
  own navbar and the map + sidebar layout.

## Frontend libraries (available, no CDN needed)

All served from `matcher/static/`:

- **Bootstrap 4** — `bootstrap4/`
- **Fork Awesome** — `fork-awesome/` (icon set; use `<i class="fa fa-*">`)
- **Leaflet** — `leaflet/` (maps)
- **jQuery** — `jquery/`
