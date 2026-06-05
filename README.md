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
- **Dictionary size setting** — choose ultra-compact (~1.7 MB) or full (~7.7 MB, default) English
  dictionary data depending on the device and level of detail you want
- **Light and dark modes** — follows your system preference, or can be set
  manually
- **Mobile-friendly** — works on phones and tablets
- **Welcome overlay** — introduction for first-time visitors
- **Free and open source** — no sign-up, no server-side text processing, no ads

Google Analytics is used for basic usage stats, such as country-level visitor
counts, and is skipped when browser Do Not Track is enabled.

## How it works

- **Tokenization** — [kuromoji.js](https://github.com/takuyaa/kuromoji.js), a
  pure JavaScript Japanese morphological analyzer
- **Dictionary lookups** — [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html),
  the Electronic Dictionary Research and Development Group's Japanese-English
  dictionary, bundled in ultra-compact (~1.7 MB) and full (~7.7 MB) English
  lookup files with cache-busting URLs (`?v=23` parameter)

See [docs/architecture.md](docs/architecture.md) for a detailed breakdown.

## Licenses

- App code: [MIT](LICENSE)
- Dictionary data: [CC BY-SA 4.0](LICENSE-JMDICT) — © Electronic Dictionary
  Research and Development Group
- kuromoji.js: browser build from the [kuromoji npm
  package](https://www.npmjs.com/package/kuromoji), [Apache
  2.0](LICENSE-KUROMOJI) — [NOTICE.md](NOTICE.md) is included from the package
  as required by Apache 2.0, though it covers mecab-ipadic dictionary data, not
  kuromoji
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
just install-hooks  # install git hooks
just serve          # serve locally and open in browser
just format         # format Markdown
just lint           # format then lint
just test           # run tests
just build-dict     # refresh source if needed and rebuild JMdict lookup files
just push_unstable  # push to unstable (go-reader-unstable) for preview
just tag_and_push   # lint, tag the release, and push to prod (go-reader)
```

## Maintaining the repository

Periodically update the dictionary in compliance with its license and rewrite
history to keep the repo lean.

Install `git-filter-repo` if not already installed using your package manager,
e.g.:

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

The script checks for a new JMdict release, downloads it if one is available,
rebuilds the dictionary files, rewrites git history to remove old dictionary
blobs, and prompts before force-pushing.

Note: GitHub will also periodically run its own garbage collection on the server
side, which helps over time, but won't rewrite history to remove old blobs —
that requires the steps above.
