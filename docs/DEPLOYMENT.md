# Production deployment

The visualization is a stateless site deployed through the reusable q5m node
hosting contract in [`q5m-ai/homelab`](https://github.com/q5m-ai/homelab/issues/18).
This repository owns the image, Compose metadata, health check, and trusted
release workflow. The homelab repository owns runner installation, node policy,
activation/rollback, reboot recovery, and Docker ingress enforcement.

## Placement and routes

Current origin retained for route rollback (verified 2026-08-21):

- host: `q5m-dev`;
- checkout: `/Users/erik/code/erdos-193`;
- process: PM2 `math193-viz`;
- command: Python `http.server` serving `viz/` on `0.0.0.0:8193`.

Current placement (verified 2026-08-21):

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

The old PM2 origin remains healthy but is no longer selected by NPM. Keep it as
the explicit stabilization rollback target until retirement is separately
approved.

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
  `production` Environment admits only `main`.

Every later trusted `main` push deploys and reports its own exact merge commit,
so use `q5m-app status erdos-193` and the public `/.q5m-release` response for
current identity rather than treating the initial cutover SHA as a floating
version.

## Release path

`.github/workflows/deploy-production.yml` validates image build/runtime on a
GitHub-hosted runner for pull requests, trusted `main` pushes, and manual
dispatches. Its deployment job can target the self-hosted runner only for a
push or dispatch whose ref is exactly `main`. The workflow has read-only
repository permissions, production concurrency, a protected Environment hook,
and a repository/branch/event guard. Pull-request code never reaches the
self-hosted runner.

The workflow checks out exact `GITHUB_SHA` without retaining GitHub credentials
and runs:

```sh
q5m-app deploy-checkout erdos-193 "$GITHUB_WORKSPACE" "$GITHUB_SHA"
q5m-app status erdos-193
```

The node archives that exact commit, validates `q5m/app.env` and
`q5m/compose.yaml`, builds `q5m/erdos-193:<full-commit>`, waits for container
health, and changes boot state only after success. The previous healthy release
is retained for local rollback.

The image serves only committed `viz/` files. `/.q5m-release` reports the exact
full commit built into the image; `/healthz` is the container health endpoint.
There are no application secrets or mutable volumes. The required empty
machine-local root is still created with standard metadata:

```sh
sudo install -d -o root -g q5m -m 0750 /etc/q5m/apps/erdos-193
```

## Bootstrap and normal operations

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

Keep PM2 `math193-viz` and its checkout unchanged until replacement, public
reversal, and the agreed stabilization gate pass.

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
5. Verify `/`, `proof-steps.html`, `theorem.html`, `walk3d.html`,
   `hilbert-colors.html`, `progress.html`, `hilbert-proof.pdf`, `robots.txt`,
   and `sitemap.xml` over the canonical public hostname.
6. Reverse NPM to `q5m-dev:8193` once and repeat the baseline. Then return it to
   `q5m-n02:8193` and repeat the replacement checks.
7. Keep the old PM2 origin during stabilization. Removing it is a separate
   approved retirement action.

If replacement checks fail, route NPM back to `q5m-dev:8193`; do not repair a
public failure by deleting release state or the old checkout.

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

Only after route reversal and stabilization are accepted:

1. remove the old PM2 `math193-viz` startup entry while retaining the checkout
   for the agreed rollback period;
2. for a node runner removal, use `sudo q5m-runner remove erdos-193-n02` and an
   expiring GitHub removal token;
3. for app removal, disable `q5m-app@erdos-193`, remove its ingress declaration,
   and reload the q5m Docker firewall as documented in homelab
   `node/HOSTING.md`;
4. treat deletion of retained releases/images as a separate irreversible
   cleanup requiring explicit approval.
