# Task Board — Django & .NET Full Stack on Docker + Kubernetes

Docker & Kubernetes-a deep-a kathukka oru real project. Same Task Board app **rendu backend**-la
(Django 5.2 & .NET 10) — same REST API, orey nginx frontend, PostgreSQL 17.

📘 Full guide (Tanglish, beginner → advanced): `../Docker-Kubernetes-Fullstack-Tanglish.pdf`

## Quick start

```bash
# Docker Compose
make django-up        # http://localhost:3000
make dotnet-up        # http://localhost:3001
make django-down / make dotnet-down

# Kubernetes (minikube)
make k8s-start        # minikube + ingress + metrics-server addons
make k8s-load         # images build panni minikube-kulla load
make k8s-deploy       # kubectl apply -k k8s/ + jobs/rollouts wait
make k8s-hosts        # /etc/hosts-la add panna vendiya line
make k8s-status
make k8s-delete       # ⚠️ namespace + PVC (data) delete
```

Browser: `http://django.taskapp.local`, `http://dotnet.taskapp.local`
(/etc/hosts illama: `curl -H "Host: django.taskapp.local" http://$(minikube ip)/api/health`)

## Structure

| Path | Enna |
|---|---|
| `django-backend/` | Django API, gunicorn, non-root Dockerfile |
| `dotnet-backend/` | .NET 10 Minimal API + EF Core, multi-stage Dockerfile, `--init-db` mode |
| `frontend/` | nginx + plain JS; `BACKEND_URL` env-la backend choose (nginx template) |
| `compose.*.yaml` | Rendu stacks — healthchecks, one-shot migrate/init services |
| `k8s/` | Namespace, Postgres StatefulSet, Jobs, Deployments, Services, HPA, Ingress (Kustomize) |
| `k8s/extras/` | NetworkPolicy (Calico/Cilium CNI venum) |
| `docs/` | PDF source — `chapters/*.md` → `build_pdf.py` → PDF |

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | Liveness — `{status, backend, hostname}` |
| GET | `/api/ready` | Readiness — DB check, 503 if down |
| GET/POST | `/api/tasks` | List / create `{"title": "..."}` |
| PATCH/DELETE | `/api/tasks/{id}` | Update `{"done": true}` / delete |

## PDF rebuild

```bash
pip install markdown pygments pymdown-extensions
make pdf              # Google Chrome/Chromium venum
```

Code blocks `<!-- include: path -->` moolama project files-la irundhu direct-a varum — code maathina PDF rebuild pannunga.
