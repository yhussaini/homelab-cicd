# homelab-cicd

A CI/CD pipeline for a 3-node kubeadm Kubernetes homelab (RHEL 8, VMware Workstation, Calico),
built with **GitHub Actions** (CI) and **Flux** GitOps (CD).

```
git push ──► GitHub Actions ──────────────────────────────────────────┐
              1. test   : site checks + container smoke test           │
              2. build  : docker build → ghcr.io/<owner>/demo-app:sha-xxxxxxx
              3. deploy : commit the new tag into k8s/demo-app/deployment.yaml
                                                                     ▼
                         Flux (inside the cluster) polls the repo every minute,
                         applies k8s/demo-app → rolling update, zero downtime
```

The cluster is never reachable from the internet: Flux *pulls* from GitHub, so no public IP,
port forwarding or kubeconfig in CI is needed.

## Layout

| Path | What |
|---|---|
| `app/` | Static site: `site/index.html` (AD CS certificate tracker, sample data only), `nginx.conf`, `Dockerfile` (nginx-unprivileged), `tests/` |
| `k8s/demo-app/` | Namespace, Deployment (2 replicas, probes, non-root, read-only FS), NodePort Service `:30090` |
| `clusters/homelab/` | Flux config: `flux-sync.yaml` (watch this repo), `flux-system/` (Flux itself), `demo-app.yaml` |
| `.github/workflows/ci.yaml` | The pipeline |

## Cluster

| Node | IP | Role |
|---|---|---|
| k8smaster | 192.168.0.17 | control plane |
| k8sworker1 | 192.168.0.16 | worker |
| k8sworker2 | 192.168.0.19 | worker |

## Setup steps

### 1. Create the GitHub repo
github.com → **New repository** → name `homelab-cicd` → **Public** → do *not* add a README/license → Create.

### 2. Push this folder (Windows, Git Bash / PowerShell in this folder)
```bash
git remote add origin https://github.com/<your-user>/homelab-cicd.git
git push -u origin main
```
Git opens a browser window to sign in the first time.

### 3. Watch the first pipeline run
GitHub → repo → **Actions**. `test → build → deploy` should go green. The deploy job adds a commit
`deploy: demo-app ghcr.io/...:sha-xxxxxxx`.

### 4. Check the image is public
The image carries an `org.opencontainers.image.source` label pointing at this public repo, so GHCR links it
to the repo and it inherits public visibility. Nothing to do. If the cluster gets `ImagePullBackOff` with
`unauthorized`, set it by hand: profile → **Packages** → `demo-app` → **Package settings** → Change visibility → Public.

### 5. Install Flux (k8smaster, one time)
The repo is public, so Flux needs **no GitHub token** and no `flux` CLI. Two `kubectl` commands do it:
```bash
B=https://raw.githubusercontent.com/yhussaini/homelab-cicd/main/clusters/homelab
kubectl apply -f $B/flux-system/gotk-components.yaml
kubectl -n flux-system rollout status deploy --timeout=300s
kubectl apply -f $B/flux-sync.yaml
```
- `flux-system/gotk-components.yaml` is the official Flux **v2.4.0** `install.yaml`, trimmed to the two
  controllers this repo needs (source-controller, kustomize-controller). The full install with 6 controllers
  overloaded the 3.6 GB master: the API server restarted halfway through the apply.
- `flux-sync.yaml` points Flux at this repo. From then on Flux applies everything in `clusters/homelab`,
  including its own components, so Flux upgrades are also done through Git.

**Why v2.4.0:** this cluster runs Kubernetes 1.29. Flux v2.4.0 is the newest release that supports 1.29
(its table: 1.29, 1.30, 1.31). v2.5+ needs 1.30+, and the current v2.10 needs 1.35+.
After upgrading Kubernetes, upgrade Flux too.

### 6. Check
```bash
kubectl -n flux-system get gitrepositories,kustomizations   # READY True
kubectl -n demo get pods -o wide
```
Open http://192.168.0.16:30090 (any node IP works).

### 7. Try the pipeline
Edit `app/site/index.html` (e.g. change the `<h1>` text), commit, push. In about 2–3 minutes the page shows
the new text and the new `sha-` version, with no manual `kubectl`.

## Rollback
`git revert` the `deploy:` commit (or the app change) and push. Flux applies the previous image.

## Useful commands
```bash
flux get all -A
flux reconcile kustomization demo-app --with-source   # sync now instead of waiting 1 min
flux logs --level=error
kubectl -n demo rollout history deploy/demo-app
```
