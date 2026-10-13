# PART B — Docker Intermediate {: .part }

Containers thaniya irundha useless — avanga pesanum (networking), data save pannanum (volumes), ellathaiyum orey command-la start pannanum (Compose). Indha part mudinja namma full stack local-a run aagum.

# Docker Networking

<span class="level intermediate">Intermediate</span>

## Container-ku sontha network stack

Ovvoru container-kum thani **network namespace** — sontha IP, sontha `localhost`, sontha ports. Adhanala:

!!! danger "No.1 Beginner Mistake: localhost"
    Django container-la `DB_HOST=localhost` vecha — adhu **Django container-oda localhost**, Postgres container illa! Connection refused. Container-kulla `localhost` = andha container mattum. Vera container-a reach panna **service/container name** use pannunga (`DB_HOST=db`).

## Network drivers

| Driver | Use case |
|---|---|
| `bridge` (default) | Single host-la containers. Virtual switch (`docker0`/`br-xxx`) |
| `host` | Container host network-ae use pannum — isolation illa, NAT illa (Linux mattum) |
| `none` | Network-e illa |
| `overlay` | Multi-host (Docker Swarm) |
| `macvlan` | Container-ku physical network-la real MAC/IP |

## Default bridge vs User-defined bridge

Idhu dhaan mukkiyamaana difference:

| | Default `bridge` | User-defined bridge (Compose create pannradhu) |
|---|---|---|
| DNS by container name | ❌ Illa (IP mattum) | ✅ Built-in DNS (127.0.0.11) |
| Isolation | Ellam containers orey network | Network-wise isolate |
| Connect/disconnect live | ❌ | ✅ `docker network connect` |

Real output — namma Django stack-la:

```text
$ docker network ls
NAME                   DRIVER
bridge                 bridge          ← default
django-stack_default   bridge          ← Compose auto-create (project name + _default)
dotnet-stack_default   bridge

$ docker exec django-stack-frontend-1 getent hosts backend db
172.18.0.3        backend  backend
172.18.0.2        db  db

$ docker exec django-stack-frontend-1 cat /etc/resolv.conf | grep nameserver
nameserver 127.0.0.11                  ← Docker embedded DNS server

$ docker run --rm alpine:3.20 getent hosts django-stack-backend-1
(nothing — default bridge-la DNS illa)
```

## Port publishing

```text
         Host (unga laptop)                     Container network (172.18.0.0/16)
  ┌──────────────────────────────┐        ┌──────────────────────────────────────┐
  │ localhost:3000 ──iptables────┼──DNAT─►│ frontend 172.18.0.4:80               │
  │                              │        │    │ http://backend:8000 (DNS)       │
  │ (8000, 5432 publish pannala  │        │    ▼                                 │
  │  → host-la irundhu reach     │        │ backend 172.18.0.3:8000              │
  │  panna mudiyaadhu ✅ secure) │        │    │ db:5432                         │
  └──────────────────────────────┘        │    ▼                                 │
                                          │ db 172.18.0.2:5432                   │
                                          └──────────────────────────────────────┘
```

- `ports: "3000:80"` → host 3000 → container 80. Docker iptables NAT rules create pannum.
- `EXPOSE`-um, ports publish pannaadha containers-um network-kulla mattum reachable.
- Namma compose-la **frontend mattum** publish — backend, DB veliya theriyaadhu. Production-la idhe principle.

!!! warning "0.0.0.0 vs 127.0.0.1"
    `"3000:80"` = `0.0.0.0:3000` — unga laptop-oda ellam network interfaces-la open (cafe WiFi-la irukka vera per access pannalaam!). Local mattum venum na: `"127.0.0.1:3000:80"`. Also, app container-kulla `127.0.0.1`-la listen pannina veliya irundhu reach aagaadhu — adhanala gunicorn `--bind 0.0.0.0:8000`.

!!! lab "Try Pannunga — manual network"
    ```bash
    docker network create labnet
    docker run -d --name pg --network labnet -e POSTGRES_PASSWORD=pw postgres:17-alpine
    docker run --rm --network labnet postgres:17-alpine pg_isready -h pg
    # pg:5432 - accepting connections     ← name-la DNS resolve aachu
    docker run --rm postgres:17-alpine pg_isready -h pg
    # pg:5432 - no response               ← default bridge, DNS illa
    docker rm -f pg && docker network rm labnet
    ```

# Volumes & Data Persistence

<span class="level intermediate">Intermediate</span>

## Container filesystem = ephemeral

Image layers **read-only**. Container start aagumbodhu mela oru **thin writable layer** add aagum (OverlayFS). Container delete → writable layer delete → data gone.

```text
  ┌───────────────────────────────┐
  │ Container writable layer      │ ← container delete aana POIDUM
  ├───────────────────────────────┤
  │ Image layer: COPY . .         │ ┐
  │ Image layer: pip install      │ │ read-only, ella containers-um share
  │ Image layer: python:3.12-slim │ ┘
  └───────────────────────────────┘
       + /var/lib/postgresql/data  ──mount──►  Volume (container-ku veliya, persist aagum)
```

## 3 types of mounts

| Type | Syntax | Data enga | Use case |
|---|---|---|---|
| **Named volume** | `pgdata:/var/lib/postgresql/data` | Docker manage (`/var/lib/docker/volumes/`) | DB data, production |
| **Bind mount** | `./src:/app` | Host-la specific folder | Development (hot reload) |
| **tmpfs** | `--tmpfs /tmp` | RAM mattum | Temp files, secrets |

```text
$ docker volume ls | grep stack
django-stack_django-db-data
dotnet-stack_dotnet-db-data

$ docker volume inspect django-stack_django-db-data --format '{{.Mountpoint}}'
/var/lib/docker/volumes/django-stack_django-db-data/_data
```

!!! tip "Development-la bind mount"
    Code maathina ovvoru thadavaiyum rebuild venaam na:
    ```yaml
    backend:
      volumes:
        - ./django-backend:/app
      command: ["python", "manage.py", "runserver", "0.0.0.0:8000"]
    ```
    Host-la file save → container-la udane theriyum → runserver auto-reload. Production-la bind mount **use panna koodadhu** — image-la code irukkanum (immutable artifact).

!!! lab "Try Pannunga — persistence prove pannunga"
    ```bash
    make django-up
    curl -X POST localhost:3000/api/tasks -H 'Content-Type: application/json' -d '{"title":"persist aaguma?"}'
    docker compose -f compose.django.yaml down        # containers delete, volume irukkum
    make django-up
    curl localhost:3000/api/tasks                     # task innum irukku ✅
    docker compose -f compose.django.yaml down -v     # -v = volumes-um delete ⚠️
    make django-up
    curl localhost:3000/api/tasks                     # []  — data gone
    ```

## Volume backup

```bash
# Volume-a tar file-a backup (temporary alpine container use panni)
docker run --rm -v django-stack_django-db-data:/data -v "$PWD":/backup alpine:3.20 \
  tar czf /backup/pgdata.tgz -C /data .
```

DB-ku file-level copy-a vida **logical dump** better (consistent):
`docker compose -f compose.django.yaml exec db pg_dump -U tasks tasks > backup.sql`

# Docker Compose — Full Stack Orey Command-la

<span class="level intermediate">Intermediate</span>

4 containers, 1 network, 1 volume, env vars, startup order — ellathaiyum `docker run` commands-a type panna paithiyam pidikkum. **Compose** = YAML-la declare pannu, `docker compose up` pannu.

## compose.django.yaml — full file

<!-- include: compose.django.yaml -->

## Line by line

**`name: django-stack`** — Project name. Containers `django-stack-backend-1`, network `django-stack_default`, volume `django-stack_django-db-data`. Rendu compose files orey folder-la irukkradhaala, name kudukkala na rendum orey project-a treat aagi conflict aagum.

**`x-django-backend: &django-backend`** — `x-` prefix = Compose ignore pannum (extension field). `&django-backend` = YAML **anchor**. `<<: *django-backend` = andha block-a inga **merge** pannu. `migrate`-um `backend`-um same image + env share pannudhu — DRY.

**`image:` + `build:` rendum** — Build panni indha name/tag-la save pannum. Kubernetes-la adhe tag use pannuvom.

**`db` service:**

- `postgres:17-alpine` — specific major version pin. `postgres:latest` vecha oru naal 17 → 18 aagi data format incompatible-a crash aagum.
- `POSTGRES_*` env — official image first start-la user/DB create pannum.
- `healthcheck` — `pg_isready` 5s-ku oru thadava. 10 times fail → unhealthy.

**`migrate` service — one-shot container:**
`command:` CMD-a override → `python manage.py migrate`. Run aagi **exit 0** aagum. Kubernetes Job-oda Compose version idhu.

**`depends_on` with conditions** — idhu dhaan startup order:

```text
  db ──(service_healthy)──► migrate ──(service_completed_successfully)──► backend ──(service_healthy)──► frontend
  pg_isready pass               exit code 0                            /api/ready 200
```

| Condition | Wait pannradhu |
|---|---|
| `service_started` (default) | Container start aana podhum (app ready-a illa naalum) |
| `service_healthy` | Healthcheck pass aaganum |
| `service_completed_successfully` | Container exit code 0-la mudiyanum |

!!! warning "depends_on ≠ app ready"
    Plain `depends_on: [db]` = db **container start** aana udane backend start. Postgres ready aaga 2-3 sec aagum — andha gap-la backend connect fail → crash. Adhanala `condition: service_healthy` + healthcheck.

**`backend` healthcheck** — slim image-la `curl` illa, Python irukku → `urllib` use panni `/api/ready` call. Image-la enna tool irukko adha use pannunga.

**`restart: unless-stopped`** — crash aana auto restart; neenga manual-a stop pannina mattum restart illa.

## compose.dotnet.yaml — differences mattum

<!-- include: compose.dotnet.yaml -->

- **`command: ["--init-db"]`** — ENTRYPOINT `dotnet TaskApi.dll` irukkradhaala, command = arguments → `dotnet TaskApi.dll --init-db`.
- **`ConnectionStrings__Default`** — .NET nested config.
- **Backend healthcheck illa** — aspnet image-la curl/wget/python edhuvum illa. Option: Dockerfile-la curl install (image size + attack surface ↑), or app-la `--healthcheck` mode ezhudhalaam. K8s-la idhu problem illa — **kubelet thaane HTTP probe pannum**, image-la tool thevai illa.
- **Port 3001** — rendu stacks orey nerathula run pannalaam.

## Compose commands

```bash
docker compose -f compose.django.yaml up -d --build   # build + background start
docker compose -f compose.django.yaml ps -a           # status (exited one-shots-um)
docker compose -f compose.django.yaml logs -f backend # one service logs follow
docker compose -f compose.django.yaml exec db psql -U tasks   # running container-la command
docker compose -f compose.django.yaml run --rm migrate        # one-off run
docker compose -f compose.django.yaml config          # merged final YAML (anchors resolve aagi)
docker compose -f compose.django.yaml down            # stop + remove (volume irukkum)
docker compose -f compose.django.yaml down -v         # volume-um delete
docker compose -f compose.django.yaml up -d --scale backend=3   # 3 backend containers
```

Real status output:

```text
$ docker compose -f compose.django.yaml ps -a --format '{{.Name}}\t{{.Status}}\t{{.Ports}}'
django-stack-backend-1    Up 7 minutes (healthy)     8000/tcp
django-stack-db-1         Up 13 minutes (healthy)    5432/tcp
django-stack-frontend-1   Up 6 minutes               0.0.0.0:3000->80/tcp
django-stack-migrate-1    Exited (0) 7 minutes ago
```

`migrate` `Exited (0)` — expected ✅. Exit code 1 aana `docker compose logs migrate` paarunga.

!!! tip "Long -f flag type panna kashtama?"
    `export COMPOSE_FILE=compose.django.yaml` panna `-f` venaam. Or file-a `compose.yaml` nu rename pannunga (default name). Namma project-la rendu stack irukkradhaala explicit names.

!!! interview "Interview Point: Compose production-ku use pannalaama?"
    Single server, chinna apps-ku — aamaa, neraya per use panraanga. Aana Compose-la **illadha** vishayangal: multi-host scheduling, node fail aana vera node-la reschedule, built-in rolling updates with health gating, autoscaling, declarative self-healing (reconciliation). Idhellam venum na **Kubernetes** (or ECS, Nomad). Compose = local dev + simple deploys. Part D-la Compose → K8s mapping paapom.

# Configuration & Secrets in Docker

<span class="level intermediate">Intermediate</span>

## Config inject panna vazhigal

| Method | Example | Note |
|---|---|---|
| `-e` / `environment:` | `DB_HOST: db` | Simple, visible in `docker inspect` |
| `--env-file` / `env_file:` | `env_file: .env` | `.env` git-la commit panna koodadhu |
| Compose `.env` (auto) | `${POSTGRES_PASSWORD}` in YAML | Variable substitution YAML-la |
| Mounted file | `-v ./config.json:/app/config.json:ro` | Complex config |
| Docker/Compose secrets | `secrets:` → `/run/secrets/name` | File-a mount, env-la theriyaadhu |

## ARG vs ENV

```dockerfile
ARG APP_VERSION=dev          # build time mattum:  docker build --build-arg APP_VERSION=1.2
ENV APP_VERSION=$APP_VERSION # runtime-ku venum na ENV-ku copy
```

!!! danger "Secrets ARG-la anuppa koodadhu"
    `--build-arg NPM_TOKEN=xxx` → `docker history`-la theriyum! Build time secret venum na BuildKit secret mount:
    ```dockerfile
    RUN --mount=type=secret,id=npm_token NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
    ```
    `docker build --secret id=npm_token,src=./token.txt .` — layer-la save aagaadhu.

## Namma project-la passwords

Compose files-la `tasks-password` plain-a irukku — **local learning-ku mattum OK**. Real project-la:

```yaml
# compose.yaml
environment:
  DB_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD set pannunga}   # .env or shell-la irundhu; illana error
```

```bash
# .env  (gitignore-la!)
DB_PASSWORD=super-secret
```

Kubernetes-la Secrets object (Part D) — adhuvum base64 mattum, encryption illa nu paapom.
