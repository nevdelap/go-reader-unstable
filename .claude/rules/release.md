# Release Process

This project has two deployment targets with distinct purposes:

## `push_unstable`

- **Target**: `origin` (<https://nevdelap.github.io/go-reader-unstable/>)
- **Purpose**: Push to unstable build for testing and preview
- **When to use**: After any change that needs to be deployed to the unstable environment
- **What it does**: Forces a push of HEAD:main to origin, triggering a GitHub Pages build

## `tag_and_push`

- **Target**: `prod` (<https://nevdelap.github.io/go-reader/>)
- **Purpose**: Create a release and deploy to production
- **When to use**: Only when the user explicitly requests a production release
- **What it does**: Runs lint, creates a git tag, and pushes to prod remote

## Important Rules

**Claude MUST NEVER run `tag_and_push` without being explicitly told to do so.**

Even when explicitly instructed to run `tag_and_push`, Claude MUST ask for confirmation first:

```text
User: Release this
Claude: I can create a production release by running `tag_and_push`. This will:
- Run lint checks
- Create a git tag (vX.Y.Z)
- Push to the prod remote (nevdelap.github.io/go-reader/)

Shall I proceed?
```

Only after the user confirms should Claude run `just tag_and_push`.
