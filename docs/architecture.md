# 語 Reader — Architecture

A static Japanese reader. No server-side text processing — tokenization and
dictionary lookups run in WASM in the browser. Deploys anywhere static
(currently GitHub Pages).

## Files

| File/Dir                                    | Purpose                                                                                                               |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `index.html`                                | Entire app — HTML, CSS, and JavaScript                                                                                |
| `javascript/kuromoji_shim.js`               | Drop-in for `window.kuromoji`; queues calls until WASM is ready                                                       |
| `javascript/jmdict_shim.js`                 | Sets `window.jmdictReady` (a Promise) once jmdict WASM is initialised                                                 |
| `javascript/japanese-ranges.js`             | Unicode ranges used by `stripNonJapanese()`                                                                           |
| `kuromoji-wasm/`                            | Rust crate: Lindera tokenizer compiled to WASM                                                                        |
| `jmdict-wasm/`                              | Rust crate: JMdict compiled in at build time; binary search at lookup time                                            |
| `pkg/`                                      | WASM binaries (`.wasm.gz`), JS glue (`.js`), and package metadata — committed                                         |
| `build/`                                    | Generated JMdict JSON lookup files (committed); zip source (gitignored)                                               |
| `scripts/compact_jmdict.py`                 | Build script: preprocesses full JMdict JSON into browser lookup files                                                 |
| `scripts/download_jmdict_source.py`         | Build script: downloads latest JMdict release zip to `build/`                                                         |
| `scripts/update_jmdict_and_compact_repo.sh` | Maintenance: checks for a new JMdict release, rewrites git history to remove old blobs, and rebuilds dictionary files |
| `scripts/local_serve.py`                    | Local dev server with correct MIME types and cache headers                                                            |
| `manifest.json` / `favicon.svg`             | PWA manifest and icon                                                                                                 |

______________________________________________________________________

## Libraries

- **[kuromoji-wasm](../kuromoji-wasm/)** — Rust/WASM port of Japanese
  morphological analysis using
  [Lindera](https://github.com/lindera/lindera) with the IPAdic dictionary
  bundled into the WASM binary. Compiled ahead of time so the browser receives
  a ready-to-run binary with no parse step.
- **[jmdict-wasm](../jmdict-wasm/)** — Rust/WASM binary with JMdict compiled
  in at build time. The dictionary is stored as a sorted binary index embedded
  in the WASM data section; lookups are binary searches with zero
  initialisation cost.
- **[JMdict](https://www.edrdg.org/jmdict/j_jmdict.html)** — Japanese-English
  dictionary from EDRDG. Pre-processed by `compact_jmdict.py` into two gzipped
  JSON lookup tables (`build/jmdict-full.json.gz` and
  `build/jmdict-ultra-compact.json.gz`) which are compiled into the WASM
  binary at build time.
- **[Lucide](https://lucide.dev/)** — ISC-licensed icon set. The sun and moon
  icons are inlined as SVG in `index.html` for the theme toggle; no external
  dependency.

______________________________________________________________________

## Analytics

Google Analytics (gtag.js, ID `G-G7TXQ86GYJ`) is used for page view tracking.
The script is loaded conditionally — skipped entirely when
`navigator.doNotTrack === "1"` or `window.doNotTrack === "1"`.

______________________________________________________________________

## Data Flow

```text
User pastes text
       │
       ▼  (300ms debounce)
stripNonJapanese()          — strips Latin, numbers, and non-Japanese punctuation
       │
       ▼
kuromoji.tokenize()         — kuromoji_shim.js forwards to kuromoji-wasm (Lindera)
                              produces morpheme tokens: surface_form, reading,
                              basic_form, pos, pos_detail_1
       │
       ▼
renderTokens()              — builds clickable <span> elements (display: inline)
                              content morphemes: foreground color
                              grammar/particles: muted color
       │
       ▼  (tap or click)
openPanel()                 — bottom panel shows:
                              • surface form + hiragana reading
                              • part of speech (mapped JP → EN)
                              • English gloss(es) from jmdict-wasm (up to two
                                results, joined with ;)
```

______________________________________________________________________

## Dictionary Build

The source JMdict English JSON is large, so `scripts/compact_jmdict.py` reduces
it to flat maps containing only what the app needs:

```json
{ "word": {"p": ["n", ...], "g": [["gloss1", "gloss2", ...], ...]}, ... }
```

- `build/jmdict-ultra-compact.json.gz` (~1.7 MB gzipped) keeps entries marked
  common by JMdict priority data plus grammar-related entries used for
  particle/auxiliary disambiguation, with all English senses for each kept entry.
- `build/jmdict-full.json.gz` (~7.7 MB gzipped) is the default. It keeps all
  English entries and every English sense.
- `g` is a list of gloss groups — one inner list per JMdict entry; groups are
  displayed joined with `,` within a group and `;` between groups
- On key collision (multiple entries share the same kanji/kana form), the common
  entry wins over an uncommon entry; entries of equal priority are merged
  (glosses appended as a new group, POS tags combined)
- Outputs are written atomically to avoid leaving corrupt gzip files if
  generation is interrupted.

These JSON files are compiled into the jmdict-wasm WASM binary at build time
by `jmdict-wasm/build.rs`. The build script sorts entries by key bytes and
writes a binary index (`jmdict.bin`) embedded via `include_bytes!`. At lookup
time, `src/lib.rs` performs a binary search over the index and deserialises the
matched entry with `postcard`.

Run `just build-dict` to regenerate the JSON, then `just build-jmdict-wasm` to
rebuild the WASM. See [Maintaining the repository](../README.md#maintaining-the-repository)
in the README.

______________________________________________________________________

## Dictionary Loading

At startup, the kuromoji and jmdict WASM modules load in parallel. Each shim
fetches its `.wasm.gz` file from `pkg/`, pipes the response body through a
`DecompressionStream('gzip')`, and passes the decompressed bytes to the
wasm-bindgen init function.

```text
javascript/kuromoji_shim.js  →  fetch pkg/kuromoji_wasm_bg.wasm.gz
                                 DecompressionStream('gzip')
                                 mod.default({ module_or_path: Response })
                                 window.kuromoji.builder().build() calls flushed

javascript/jmdict_shim.js    →  fetch pkg/jmdict_{ultra,full}_wasm_bg.wasm.gz
                                 DecompressionStream('gzip')
                                 mod.default({ module_or_path: Response })
                                 window.jmdictReady resolved
```

`index.html` awaits `window.jmdictReady` and sets `jmdict` to a JS `Proxy`
that calls `mod.lookup(word)` on every property access. The `has` trap makes
`word in jmdict` work correctly.

The dictionary mode (`ultra` / `full`) is stored in `localStorage` as
`dictionaryMode`. Unrecognised values fall back to `full`. Changes apply after
reload.

Up to 5 retry attempts with increasing delays (2 s, 4 s, 6 s…) if either load
fails.

______________________________________________________________________

## Lookup Logic

When a token is tapped or clicked, `lookupWord(surface_form, basic_form)` tries:

1. `basic_form` — the dictionary/base form (e.g. `食べる`), skipped if it equals
   `surface_form` or `*`
2. `surface_form` — the exact text as it appears (e.g. `食べました`)
3. **Godan imperative fallback** — if both lookups fail and the surface form
   ends in a Japanese e-row kana (え, け, げ, せ, て, ね, べ, め, れ), the final kana
   is replaced with its corresponding u-row kana (う, く, ぐ, す, つ, ぬ, ぶ, む, る)
   to derive the dictionary form (e.g. `払え` → `払う`). This corrects a kuromoji
   misanalysis where godan imperatives are tagged as potential-form verbs
   (e.g. `払え` gets `basic_form: 払える`), whose potential form is not in the
   selected dictionary. The ぬ mapping is included but the fallback is rarely
   reached since 死ね has its own dictionary entry as an interjection.

Both results from steps 1–2 are returned when found, joined with a semicolon and
space. This handles conjugated verbs and adjectives, and surfaces homograph
disambiguation (e.g. `ある` returns both the verb and the existential senses).
If neither is found in JMdict, the display falls back to the `basic_form` string
from kuromoji.

Katakana readings from kuromoji are converted to hiragana for display
(`toHiragana()`).

### Particle and Auxiliary Verb Glosses (`pg` field)

Words that function as particles or auxiliary verbs often have a primary JMdict
entry that describes their non-grammatical meaning (e.g., て as a quoting
particle, って). To ensure correct glosses in grammar contexts, the generated
dictionary includes a `pg` field containing glosses from grammar-related senses:

- **Source senses**: JMdict entries tagged as particle (`prt`), expression
  (`exp`), or auxiliary (`aux`, `aux-v`, `aux-adj`)
- **Usage**: `lookupParticle()` returns `pg` for grammar tokens; falls back to
  `g[0]` (first gloss group) if `pg` is absent

### Competing Senses (`pg2` field)

Some particles have multiple common senses where neither is clearly "primary."
For て and で:

- The **common** JMdict entry describes the quoting sense (って)
- The **conjunctive** sense (and/then, as in 食べて) is in a separate entry

Both are needed in context. The dictionary stores the conjunctive glosses in
`pg2`, and `lookupParticle()` selects between them based on kuromoji's
`pos_detail_1`:

```javascript
if (token.pos_detail_1 === '接続助詞' && entry.pg2) {
    return entry.pg2.slice(0, 3).join(', ');
}
```

This is currently the only case requiring `pg2`; other particles use `pg`
directly.

### Grammar POS Sets

Two separate sets define "grammar" for different purposes:

| Location            | Set                                         | Purpose                                  |
| ------------------- | ------------------------------------------- | ---------------------------------------- |
| `compact_jmdict.py` | `{'prt', 'exp', 'aux', 'aux-v', 'aux-adj'}` | Selects which JMdict senses go into `pg` |
| `index.html`        | `['助詞', '助動詞', '記号', ...]`           | Determines which tokens get gray styling |

These map between different tag systems (JMdict English tags vs kuromoji
Japanese tags) and are not duplicated — they serve different roles in the
pipeline.

______________________________________________________________________

## UI Details

- **Token rendering** — tokens use `display: inline` so letter-spacing and glyph
  metrics behave consistently with the textarea input
- **Token area rebuild** — on re-tokenization, the token area DOM node is
  replaced with a clone to avoid accumulating event listeners
- **Panel height tracking** — a `ResizeObserver` keeps `--panel-height` in sync
  so the token area scrolls far enough to keep the active token visible above
  the bottom panel
- **Input buttons** — "Clear" clears the textarea, "Clear Up" clears from cursor
  to top, "Paste" reads from the clipboard (falls back to an error message on
  permission denial), "Copy URL" / "Share" (icon on mobile) encodes the current
  input as a compressed URL fragment and copies it to the clipboard (or invokes
  the native share sheet on touch devices), "E.G." loads a sample text; all
  return focus to the textarea
- **Help button** — a "?" button in the header reopens the welcome overlay
- **Settings button** — a cog button in the header opens dictionary mode
  settings. The mode can be ultra-compact or full, and applies after
  reload.
- **Keyboard shortcuts** — see dedicated section below
- **Input deduplication** — if the raw input hasn't changed since last
  tokenization, rendering is skipped
- **Debounce** — 300ms after last keypress before `analyze()` fires
- **Grammar classification** — particles (`助詞`), auxiliary verbs (`助動詞`),
  symbols, punctuation, whitespace, and filler (`フィラー`) tokens are styled
  gray and show their POS label rather than a dictionary lookup
- **Vertical reading mode** — a toggle button in the legend bar switches the
  token area between horizontal (default) and `writing-mode: vertical-rl`
  (top-to-bottom, right-to-left columns). The button label reflects the action
  to take: "Read top to bottom" when horizontal, "Read left to right" when
  vertical. On entering vertical mode the scroll position is snapped to
  `scrollLeft = scrollWidth` so the first column (rightmost) is visible
  immediately.
- **Light/dark theme** — a toggle button in the header switches between light
  (default) and dark themes using CSS custom properties on `:root`. An inline
  `<script>` in `<head>` applies the saved theme before first paint to avoid a
  flash.
- **Dim grammar toggle** — a toggle button in the legend bar switches between
  dimmed grammar tokens (default, `--text-grammar` color) and uniform coloring.
  The button label reflects the current state: "Dim grammar" / "Undim grammar".
  Preference is stored in `localStorage` (`dimGrammar`).
- **Persistence** — theme choice, dictionary mode, reading direction,
  dim-grammar preference, welcome overlay dismissal, raw textarea input, and the
  selected morpheme are all stored in `localStorage` and restored on load. The
  selected morpheme is tied to the raw textarea value and cleared as soon as the
  textarea is edited.

______________________________________________________________________

## Keyboard Shortcuts

| Shortcut | Action                                        |
| -------- | --------------------------------------------- |
| `Ctrl+K` | Clear the textarea                            |
| `Ctrl+V` | Paste from clipboard (Clear and paste button) |
| `Alt+D`  | Toggle reading direction                      |
| `Escape` | Close welcome overlay or word details panel   |
| `?`      | Open help (welcome overlay)                   |

Shortcuts are blocked when focus is in the textarea (except Ctrl+V, which is
handled natively).

______________________________________________________________________

## Welcome Overlay

A modal dialog shown on first visit to introduce the app to new users:

- **Auto-show** — Appears 500ms after page load on first visit
- **Dismiss options**:
  - "GOT IT" button closes for this session
  - "Don't show again" checkbox saves preference to `localStorage` and prevents
    auto-show on future visits
- **Help button** — The "?" button in the header reopens the overlay at any time
- **Focus management** — When opening, focus moves to the "GOT IT" button; when
  closing, focus returns to the triggering element
- **Escape key** — Closes the overlay
- **Click outside** — Clicking the backdrop (dark area outside the dialog)
  closes the overlay
- **Persistence** — `localStorage.getItem('welcomeDismissed')` tracks whether
  the user has chosen to hide the overlay

The overlay content explains that the app is for advanced learners, that it uses
local dictionary lookups (no AI), and covers basic usage (tap or click
morphemes, grammar dimming toggle, keyboard shortcuts, browser-local
processing).

______________________________________________________________________

## URL Sharing

The "Copy URL" / "Share" button encodes the textarea content into the URL
fragment (`#t=<encoded>`):

1. The text is UTF-8 encoded and compressed with
   `CompressionStream('deflate-raw')`.
2. The compressed bytes are base64-encoded using URL-safe characters (`-` for
   `+`, `_` for `/`, no `=` padding).
3. The resulting URL is copied to the clipboard or passed to `navigator.share()`
   on touch devices.

On load (and on `hashchange`), `loadFromHash()` reverses the process — URL-safe
base64 → `DecompressionStream('deflate-raw')` → UTF-8 text — and populates the
textarea.

______________________________________________________________________

## Deployment

The app is fully static. The compiled WASM binaries are committed to `pkg/` as
pre-gzip-compressed `.wasm.gz` files. GitHub Pages serves them as raw bytes;
the shims fetch and decompress client-side via `DecompressionStream('gzip')`.

Fonts are vendored in `fonts/`. A fresh clone can be served immediately with
`just serve` — no build step required for day-to-day development.
