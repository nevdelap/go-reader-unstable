# 語 Reader — Japanese Reader For Learners

A free Japanese reading tool for advanced learners. Type or paste Japanese text
and tap or click any morpheme to instantly see its hiragana reading and English
meaning. Look up kanji, vocabulary, and grammar while reading native Japanese
content.

<img src="phone-image.png" width="400" alt="語 Reader on mobile"><br>
*語 Reader on mobile.*

<img src="og-image.png" alt="語 Reader on desktop"><br>
*語 Reader on desktop.*

Japanese text processing runs in your browser — no account, no server-side text
analysis, **no AI**. The site does load Google Analytics for basic page usage
stats; your reading text is not sent to it by the app.

**[https://nevdelap.github.io/go-reader/](https://nevdelap.github.io/go-reader/)**

## Features

- **Instant morpheme lookup** — tap or click any morpheme in Japanese text to
  see its reading and English definition
- **Hiragana readings** — see how any morpheme is pronounced
- **Browser-local reading** — once the app and dictionaries are loaded, lookups
  run locally in your browser and may keep working from the browser cache
- **Dictionary size setting** — choose ultra-compact or full dictionary data
  depending on the device and level of detail you want
- **Light and dark modes** — follows your system preference, or can be set
  manually
- **Mobile-friendly** — works on phones and tablets
- **Welcome overlay** — introduction for first-time visitors
- **Free and open source** — no sign-up, no server-side text processing, no ads

Google Analytics is used for basic usage stats, such as country-level visitor
counts, and is skipped when browser Do Not Track is enabled.

## How it works

- **Tokenization** — [kuromoji-wasm](kuromoji-wasm/), a Rust/WebAssembly port
  using [Lindera](https://github.com/lindera/lindera) with the IPAdic dictionary,
  compiled ahead of time so the browser receives a ready-to-run binary with no
  parse step
- **Dictionary lookups** — [jmdict-wasm](jmdict-wasm/), a Rust/WebAssembly
  binary with [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) compiled in
  at build time; lookups are binary searches over static bytes with zero
  initialization cost

See [docs/architecture.md](docs/architecture.md) for a detailed breakdown.

## Licenses

- App code: [MIT](LICENSE)
- Dictionary data: [CC BY-SA 4.0](LICENSE-JMDICT) — © Electronic Dictionary
  Research and Development Group
- Lindera/IPAdic: [Apache 2.0](LICENSE-KUROMOJI) — [NOTICE.md](NOTICE.md)
- Lucide icons: [ISC](LICENSE-LUCIDE)
- Fonts: Inter ([SIL Open Font License 1.1](LICENSE-INTER)) and Noto Sans JP
  ([SIL Open Font License 1.1](LICENSE-NOTO-SANS-JP))

## Two repositories

This project uses two GitHub repositories for deployment:

- **[go-reader](https://github.com/nevdelap/go-reader)** — production, served at
  <https://nevdelap.github.io/go-reader/>. Only receives tagged releases.
- **[go-reader-unstable](https://github.com/nevdelap/go-reader-unstable)** —
  unstable/preview, served at <https://nevdelap.github.io/go-reader-unstable/>.
  Receives every push for testing before a production release.

GitHub Pages serves one site per repository, so hosting both versions on
GitHub Pages requires two repositories — otherwise they would be in a single
repo. As a result, branches are not used; the main branch of go-reader-unstable
just receives all dev changes. Issues should be posted to the
[go-reader](https://github.com/nevdelap/go-reader) repository.

## Local development

```bash
just install-hooks       # install git hooks
just serve               # serve locally and open in browser
just format              # format Markdown
just lint                # format then lint
just test                # run JS and Python tests
just test-wasm           # run Rust tests for the WASM tokenizer
just build-dict          # download JMdict source and rebuild JSON lookup files
just build-wasm          # rebuild kuromoji WASM tokenizer
just build-jmdict-wasm   # rebuild both JMdict WASM binaries and compress them
just compress-wasm       # pre-compress WASM binaries for local serving
just setup-wasm-dict     # one-time: compile Lindera IPAdic dictionary (after cloning)
just push_unstable       # push to unstable (go-reader-unstable) for preview
just tag_and_push        # lint, tag the release, and push to prod (go-reader)
```

### First-time setup after cloning

The compiled WASM binaries are committed to `pkg/` and served directly by
GitHub Pages, so a fresh clone can be served immediately with `just serve`.

To rebuild the WASM binaries from source:

```bash
just setup-wasm-dict     # compile Lindera IPAdic (one-time, takes a few minutes)
just build-dict          # download JMdict source and build JSON files
just build-wasm          # rebuild kuromoji WASM
just build-jmdict-wasm   # rebuild jmdict WASM (reads build/ JSON files)
```

## Maintaining the repository

### Updating the dictionary

Periodically update the dictionary in compliance with its license. The update
script checks for a new JMdict release, downloads it, rebuilds the JSON lookup
files, rewrites git history to remove old large blobs, and prompts before
force-pushing.

Install `git-filter-repo` if not already installed:

```bash
# Linux (Debian/Ubuntu)
sudo apt install git-filter-repo

# macOS
brew install git-filter-repo
```

Then run:

```bash
scripts/update_jmdict_and_compact_repo.sh
```

After the script completes, rebuild the jmdict WASM binaries and commit them:

```bash
just build-jmdict-wasm
git add pkg/jmdict_full_wasm_bg.wasm.gz pkg/jmdict_ultra_wasm_bg.wasm.gz pkg/jmdict_full_wasm.js pkg/jmdict_ultra_wasm.js
git commit -m "Rebuild jmdict WASM with updated dictionary."
```

### Large binary files in git history

The following files are committed to the repo and accumulate in git history
when updated. The update script rewrites history to remove old
`build/jmdict-*.json.gz` blobs. Old `pkg/*.wasm.gz` blobs from WASM rebuilds
should also be pruned periodically using `git filter-repo`.

| Path                                 | Why committed               | Size    |
| ------------------------------------ | --------------------------- | ------- |
| `build/jmdict-full.json.gz`          | build input for jmdict-wasm | ~7.7 MB |
| `build/jmdict-ultra-compact.json.gz` | build input for jmdict-wasm | ~1.7 MB |
| `pkg/jmdict_full_wasm_bg.wasm.gz`    | served by GitHub Pages      | ~13 MB  |
| `pkg/jmdict_ultra_wasm_bg.wasm.gz`   | served by GitHub Pages      | ~3.5 MB |
| `pkg/kuromoji_wasm_bg.wasm.gz`       | served by GitHub Pages      | ~5 MB   |

Note: GitHub will also periodically run its own garbage collection on the server
side, which helps over time, but won't rewrite history to remove old blobs —
that requires the steps above.
