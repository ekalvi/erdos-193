# Production deployment

The visualization is a stateless site deployed through the reusable q5m node
hosting contract in [`q5m-ai/homelab`](https://github.com/q5m-ai/homelab/issues/18).
This repository owns the image, Compose metadata, health check, and trusted
release workflow. The homelab repository owns runner installation, node policy,
activation/rollback, reboot recovery, and Docker ingress enforcement.

## YAML adoption: prepared, not activated

**Merge hold:** homelab PR [#105](https://github.com/q5m-ai/homelab/pull/105)
merged at `26885afa4b2665c694a57a8451ec1bb66a8f7a1a`. This application change
follows its [production-adoption contract](https://github.com/q5m-ai/homelab/blob/26885afa4b2665c694a57a8451ec1bb66a8f7a1a/node/PRODUCTION-ADOPTION.md).
A merged platform PR is not rollout or live-acceptance confirmation. **Do not
merge this workflow, deploy, or adopt the binding until the coordinated handoff.**
No runtime installation, binding adoption, route change or release activation is
performed by preparing this PR.

Required handoff, in order:

1. Homelab confirms matching CLI/runtime rollout (1.5.0 production interface),
   prerequisites and synthetic live acceptance on the authorized release host.
2. Operators confirm the actual existing app/runner/tunnel owner, active and
   rollback releases, boot owner, source policy, fixed port `8193`, and public
   `/.q5m-release` baseline. YAML references only `production.binding: erdos-193`;
   host and route authority belong to protected operator policy, not a dev node.
3. Freeze/drain competing legacy CI releases. Review the operator's exact adoption
   plan and obtain **separate explicit adoption approval** before publishing the
   protected binding. Adoption is not a CI step and is not authorized by this PR.
4. Only after rollout/live-acceptance confirmation and coordinated binding
   adoption, explicitly approve merging the YAML workflow. Its first trusted
   `main` release uses the existing Nginx/Compose image, port `8193`, and
   `erdos-193.q5m.ai` tunnel. No parallel legacy writer may remain enabled.
5. Verify the exact public merge SHA and representative site paths. Keep the
   previous immutable release and rollback eligibility; do not rewrite history.

## Placement and routes

**Current release placement (checked September 8, 2026):** `q5m-n03`, using
repository runner `erdos-193-n03` with label `erdos-193-deploy`. The latest
successful main release, Actions run `34145901306`, deployed on that runner;
`erdos-193-n01` was registered but offline. These observations must be refreshed
before adoption; they are not an instruction to move production. The protected
binding enforces placement. YAML ownership reuses the existing hardened Compose
engine; the Nginx image, port `8193`, and canonical `erdos-193.q5m.ai` tunnel are
retained, not reprovisioned.
The cutover details below are historical evidence, not current placement.

Retired origin (verified 2026-08-21):

- host: `q5m-dev`;
- retained checkout: `/Users/erik/code/erdos-193`;
- former process: PM2 `math193-viz`, Python `http.server` on port `8193`;
- retirement result: process deleted, saved PM2 startup state updated, and the
  old port stopped after explicit approval. The checkout and logs were retained.

Historical placement (verified 2026-08-21):

- node: `q5m-n02.localdomain` (current NPM-reachable address `10.1.1.31`);
- app: `erdos-193`;
- repository-scoped runner: `erdos-193-n02`;
- runner label: `erdos-193-deploy`;
- Docker-published port: `8193`, admitted only from Nginx Proxy Manager;
- local release identity: `http://127.0.0.1:8193/.q5m-release` on the node.

Nginx Proxy Manager terminates public TLS. Proxy host ID `20` serves the
canonical `erdos-193.q5m.ai` route from `10.1.1.31:8193`. Deprecated NPM proxy
hosts `14` (`erdos-193.q5m.io`) and `19` (`erdos.q5m.io`) were deleted by
explicit operator request after cutover. Their remaining Cloudflare DNS cleanup,
the proposed `erdos.q5m.ai` hostname, certificate/canonical changes, and redirect
decision remain owned by issue #12.

The old PM2 origin was retained through cutover, public reversal, reboot proof,
and stabilization, then retired after explicit approval. Local image/state
rollback on `q5m-n02` is now the application rollback path; the old Mac is no
longer a live origin.

## Verified acceptance evidence

The initial production cutover used exact merged commit
`a68aa2276213112b94eaf6473a27dae835086c97`. GitHub Actions run
[`32443889384`](https://github.com/ekalvi/erdos-193/actions/runs/32443889384)
passed the hosted image gate and then deployed that exact commit on
`erdos-193-n02`. Pull request run `32443847484` passed the hosted gate while the
self-hosted deploy job was skipped.

Additional checks completed 2026-08-21:

- an intentionally unhealthy candidate `8d4fcbc64f34` failed Compose health and
  automatically restored healthy bootstrap release `02003133d4df`;
- a healthy local rollback round trip selected `02003133d4df`, then restored
  merged release `a68aa2276213`, with both health gates passing;
- after the supervised `q5m-n02` reboot at `14:37Z`, systemd recreated the exact
  merged release without a manual container start; the app was healthy by
  `14:37:51Z`, and the repository runner was online/listening by `14:37:45Z`;
- NPM reached `/.q5m-release` from its approved source while an ordinary client
  timed out against direct port `8193` before and after reboot;
- canonical public cutover returned the exact commit and all documented site
  paths returned `200`; NPM then reversed to `10.1.1.211` (root `200`, release
  marker `404`) and returned to `10.1.1.31`, where exact-release proof passed;
- `main` now requires the hosted `Container contract` check, up-to-date pull
  request branches, conversation resolution, and no force-push/deletion; the
  `production` Environment admits only `main`;
- after operator approval, PM2 `math193-viz` was removed from the running and
  saved process lists on `q5m-dev`; port `8193` stopped while the canonical
  public exact release and all documented paths continued to pass.

Every later trusted `main` push deploys and reports its own exact merge commit,
so use the current owner's status and the public `/.q5m-release` response for
current identity rather than treating the initial cutover SHA as a floating
version. After adoption, status is `q5m-lab project production status --binding
erdos-193 --json`; do not invoke legacy mutating status.

## Release path

`.github/workflows/deploy-production.yml` validates image build/runtime on a
GitHub-hosted runner for pull requests, trusted `main` pushes, and manual
dispatches. Its deployment job can target the self-hosted runner only for a
push or dispatch whose ref is exactly `main`. The workflow has read-only
repository permissions, production concurrency, a protected Environment hook,
and a repository/branch/event guard. Pull-request code never reaches the
self-hosted runner.

The workflow checks out exact `GITHUB_SHA` without retaining GitHub credentials.
On the existing authorized runner, with a clean exact checkout and canonical
HTTPS Git remote, it uses the YAML production entry point (not a validation shim
followed by an independent legacy deployment):

```sh
q5m-lab project production plan --revision "$GITHUB_SHA" --json
q5m-lab project production deploy --revision "$GITHUB_SHA" --json
q5m-lab project production status --binding erdos-193 --json
```

Plan failure prevents deploy. The logical binding selects and enforces the
approved source, host, existing route, exact release-marker health and rollback
contract. No node override, implicit adoption, missing-tool fallback, or direct
`q5m-app` writer is permitted. Status is read-only and runs even after failure;
it is not recovery. Local activation can succeed before public verification
fails, so a failed job must not be described as automatic rollback.

The node archives that exact commit, validates `q5m/app.env` and
`q5m/compose.yaml`, builds `q5m/erdos-193:<full-commit>`, waits for container
health, and changes boot state only after success. The previous healthy release
is retained for local rollback.

The image serves committed `viz/` and `results/` assets (the latter at `/family/`),
subject to `.dockerignore`. The optional `build/q5m-site` review output and LAN
server are not production inputs. Merging the hosting-only PR therefore does
not include locally uncommitted six-vector pages or scripts.

`q5m.yaml` declares `production: {binding: erdos-193}` and the Compose release's
health path `/.q5m-release`. Its `development` and `build` sections remain
separate; production never starts `q5m/serve_site.py` or serves the review build.
The old isolated `project deploy --environment production` is not this interface
and must not be used to create another owner. Explicit operator adoption changes
ownership; trusted `main` pushes then activate releases after the container gate.
The application workflow creates no DNS, tunnel, port, volume or binding.

`/.q5m-release` reports the exact full commit built into the image; `/healthz` is the container health endpoint.
There are no application secrets or mutable volumes. The required empty
machine-local root is still created with standard metadata:

```sh
sudo install -d -o root -g q5m -m 0750 /etc/q5m/apps/erdos-193
```

## Release rollback after YAML adoption

Release rollback uses the same protected binding and preserved release history:

```sh
q5m-lab project production rollback --binding erdos-193 --json
q5m-lab project production status --binding erdos-193 --json
```

This selects an application release, not a previous infrastructure owner. A lost
client or public-health failure is not permission to resubmit: record the returned
operation unit and inspect that exact unit/journal and app state first. Recovery,
when explicitly approved, uses `q5m-lab project production recover --binding
erdos-193 --json`. Never bypass the writer fence with an old binary or Docker.

Undoing adoption is a separate operator-approved handoff: freeze the YAML writer,
review the binding installer's `plan-release`, and use `release-owner` with its
exact approved plan. Only afterward may legacy CI be re-enabled. This does not
choose a release, downgrade tools or delete the route. There is no generic
production down/purge operation in this contract.

## Historical operations (pre-adoption only)

The remaining commands record the earlier legacy lifecycle and migrations.
**Do not execute them against an adopted binding.** Current adoption, rollback,
recovery and ownership reversal follow the contract and sections above. Host
moves, reboot tests and retirement require their own explicit authorization.

### Bootstrap and normal operations

Follow `node/HOSTING.md` in the homelab repository to install `q5m-app`, the
firewall watcher, and a repository-scoped runner. Bootstrap the first release
from a trusted checkout before enabling reboot recovery:

```sh
release=$(git rev-parse refs/heads/main^{commit})
sudo -u q5m /usr/local/bin/q5m-app \
  deploy-checkout erdos-193 "$PWD" "$release"
sudo systemctl enable --now q5m-app@erdos-193.service
```

Normal releases are Actions-driven. Operator checks and local rollback are:

```sh
q5m-app status erdos-193
q5m-app rollback erdos-193
systemctl status q5m-app@erdos-193.service
q5m-runner status erdos-193-n02
```

A second `rollback` returns to the release that was active before the first
rollback, provided both health gates pass.

## Cutover and reversal

The completed migration used this sequence while PM2 `math193-viz` remained
available for controlled reversal:

1. Record the old NPM origin and both public response baselines.
2. Deploy exact `main` to `q5m-n02`; verify `q5m-app status` and that
   `/.q5m-release` equals the full release.
3. From NPM, verify `http://10.1.1.31:8193/healthz` and representative site
   assets. The NPM container does not currently resolve `.localdomain`, so use
   the recorded current placement address rather than silently assuming node
   DNS works there. From an ordinary LAN client, verify direct port `8193` is
   blocked.
4. Change only the NPM origin to `10.1.1.31:8193`; do not change DNS,
   hostnames, certificate, or canonical content in this step.
5. Verify `/`, `proof.html`, `learn.html`, `walk3d.html`, `progress.html`,
   `demo.html`, `erdos-193-gaussian-proof.pdf`, `robots.txt`, and `sitemap.xml` over the
   canonical public hostname.
6. Reverse NPM to `q5m-dev:8193` once and repeat the baseline. Then return it to
   `q5m-n02:8193` and repeat the replacement checks.
7. Keep the old PM2 origin during stabilization. Remove it only after explicit
   approval and a final exact-release/public baseline.

That old-origin reversal path was retired on 2026-08-21. For a current
application failure, use the recorded local `q5m-app rollback erdos-193` state;
do not point NPM at the stopped Mac or repair a failure by deleting release
state.

## Failed candidate and reboot tests

Use a reviewed commit that intentionally fails its container health check,
then deploy it through the same interface. The command must fail and
`q5m-app status erdos-193` must still report the previous healthy commit. Revert
the test commit through Git; never edit a staged release in place.

After a healthy deployment and with public NPM still reversible, arrange a
supervised node reboot. After reconnecting:

```sh
systemctl is-active q5m-app@erdos-193.service
q5m-app status erdos-193
curl -fsS http://127.0.0.1:8193/.q5m-release
```

No manual `docker start` is permitted.

## Moving to another standard node

Prepare the second node from the same homelab contract, create the empty
`/etc/q5m/apps/erdos-193` root, and install a repository runner with a unique
node-specific name but the same `erdos-193-deploy` label. Disable the old runner
before enabling the new one so a workflow cannot select placement
nondeterministically. Deploy the same full commit, verify NPM-only ingress, then
change and reverse the NPM origin exactly as above. No file in `q5m/` changes
for a move from `q5m-n02` to `q5m-n01`.

## Retirement

The old Mac origin was retired on 2026-08-21 after route reversal,
stabilization, and explicit approval:

```sh
pm2 delete math193-viz
pm2 save
```

Post-retirement verification found no running or saved `math193-viz`, no
listener on old port `8193`, an intact `/Users/erik/code/erdos-193` checkout,
and unchanged canonical exact-release/public health.

Future removal of the active node placement remains a separate operation:

1. remove runner `erdos-193-n02` with `sudo q5m-runner remove` and an expiring
   GitHub removal token;
2. disable `q5m-app@erdos-193`, remove its ingress declaration, and reload the
   q5m Docker firewall as documented in homelab `node/HOSTING.md`;
3. treat deletion of retained releases/images, the old checkout, or logs as a
   separate irreversible cleanup requiring explicit approval.
