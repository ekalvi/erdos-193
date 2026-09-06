# Unpublished g85 to six-coordinate explainer

This directory is outside the production Docker build's `viz/` and `results/`
roots. Nothing here was published publicly. The page labels the six-dimensional
result as a draft awaiting independent review and distinguishes proof from
finite illustration. No analytics or external runtime assets are loaded.

## View offline

Copy `standalone.html` to your computer and open it in a browser. It is a
self-contained HTML file with the same controls, no network requirement, and no
server requirement. Its optional reading links navigate to public sources only
when clicked.

Regenerate after editing the modular sources:

```sh
node design/unit-step-explainer/build.mjs
```

## Managed LAN preview

The root `q5m.yaml` declares a static development preview of `public/`, which
contains only the generated `index.html`. No production hostname is declared.
The initial missing-manifest blocker was resolved at the user's request.

From the repository root:

```sh
q5m-lab inspect --json
q5m-lab validate --json
q5m-lab dev --json
```

Use the exact URL, instance ID, and cleanup command returned by the managed
lifecycle. No fixed port, ad hoc server, or public-hosting fallback is provided.
`noindex` is not access control; LAN-only exposure comes from the hosting contract.

## Contents

- `index.html`, `app.mjs`, `model.mjs`: dependency-free modular source.
- `standalone.html`: generated offline distribution.
- `public/index.html`: identical generated distribution for managed LAN hosting.
- `test.mjs`: exact integer-model checks, including all 523,776 pairs of the
  1,024-vertex prefix, T(P)=Q, carry changes, an independent substitution
  generator, and all 15 merger witnesses. Finite checks do not prove infinity.
- `browser-test.mjs`: desktop/mobile/control/offline smoke test. Uses Playwright
  request interception for the modular page, not a listening server. Screenshots
  go under the ignored `.checkpoint-unit-step-explainer/` directory.

Run the arithmetic checks:

```sh
node design/unit-step-explainer/test.mjs
```

With Playwright and its browser dependencies available, run the browser checks
using one or two cores:

```sh
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
  node design/unit-step-explainer/browser-test.mjs
```

In this session Chromium's missing libraries were downloaded and unpacked only
under `/tmp/unit-step-browser-libs/`, without modifying system packages. The
browser test ran with that local library directory and CPU affinity `0,1`.
Desktop, 390-pixel mobile width, playback, stepping, invalid triples, mergers,
endpoint readouts, and offline-file loading passed without page errors.

Related mathematical consequences and their limitations are documented in
`design/UNIT-STEP-CONSEQUENCES.md`.
