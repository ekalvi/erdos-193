# Static site templates

Edit **`site/pages/*.html`**, not the generated `viz/*.html` files. Shared markup lives in `site/partials/`:

- `head.html`: encoding and viewport
- `icons.html`: favicon and Apple touch links
- `fonts.html`, `stylesheet.html`, `mathjax.html`: shared optional dependencies
- `header.html`: brand and navigation, with the current page marked automatically

Pages opt into partials using `{{ include header }}` (or another partial name). Titles, descriptions, canonical URLs, research-only robots directives, styles, scripts, and content remain page-specific. Research-only pages retain their separate layout without the public navigation.

Run with Node.js 22 or newer, with no packages to install:

```sh
node site/build.mjs          # regenerate tracked viz/*.html
node site/build.mjs --check  # fail if generated pages are stale
node --test site/build.test.mjs
```

Commit templates and generated HTML together. Outputs remain tracked because research checks and chronology tooling read `viz/*.html` directly. Builds are deterministic, only replace changed files, and use atomic writes; rerunning completes an interrupted build. CI checks freshness before deployment. Nginx still serves plain HTML, with no runtime includes, JavaScript header loading, or URL changes. Templates are outside `viz/` and are not shipped in the image.

The root `favicon.svg` is separately used by Paseo's project-icon discovery; keep its artwork synchronized with `viz/favicon.svg` when changing branding.
