# PART A — Docker Basics {: .part }

Container-na enna, image-na enna, Dockerfile eppadi ezhudhuradhu, namma Django & .NET apps-a eppadi pack panrom. Beginner level — aana "ulla enna nadakkudhu" skip panna maattom.

# Container-na Enna?

<span class="level beginner">Beginner</span>

## Problem: "En machine-la work aagudhe!"

Neenga oru Django app ezhudhureenga. Unga laptop-la Python 3.12, Django 5.2, PostgreSQL 17 irukku. Team-mate laptop-la Python 3.9. Server-la Python 3.10, vera OpenSSL version. Result?

- "Enakku work aagudhu, unakku aagala na un problem" 😤
- Production deploy-la mattum crash
- New developer join panna setup panna 2 naal

**Root cause:** App mattum ship panrom — adhu depend panra *environment* (OS libraries, runtime version, config) ship panrathilla.

**Container solution:** App + adhoda runtime + libraries + config — ellathaiyum **oru package (image)**-a pack panni, endha machine-la Docker irundhaalum **exact-a same maadhiri** run pannalaam.

## VM vs Container

```text
        Virtual Machines                          Containers
 ┌────────┐ ┌────────┐ ┌────────┐       ┌────────┐ ┌────────┐ ┌────────┐
 │ App A  │ │ App B  │ │ App C  │       │ App A  │ │ App B  │ │ App C  │
 │ Libs   │ │ Libs   │ │ Libs   │       │ Libs   │ │ Libs   │ │ Libs   │
 │Guest OS│ │Guest OS│ │Guest OS│       └────────┘ └────────┘ └────────┘
 └────────┘ └────────┘ └────────┘       ┌──────────────────────────────┐
 ┌──────────────────────────────┐       │  Container Runtime (Docker)  │
 │  Hypervisor (VMware/KVM)     │       ├──────────────────────────────┤
 ├──────────────────────────────┤       │  Host OS (Linux kernel)      │
 │  Host OS / Hardware          │       ├──────────────────────────────┤
 └──────────────────────────────┘       │  Hardware                    │
                                        └──────────────────────────────┘
```

| | Virtual Machine | Container |
|---|---|---|
| Isolation | Full OS (own kernel) | Process-level (host kernel share) |
| Size | GBs | MBs (namma frontend: 73.6MB) |
| Boot time | Minutes | Milliseconds – seconds |
| Density | Oru server-la 10–20 VMs | Oru server-la 100s of containers |
| Security boundary | Strong (hypervisor) | Weaker (same kernel) |

!!! interview "Interview Point: Container = lightweight VM ah?"
    **Illa.** Container oru *isolated process* — host kernel-a share pannum. Linux kernel features **namespaces** (enna paakalaam — PID, network, filesystem isolation) and **cgroups** (evlo use pannalaam — CPU, memory limit) use panni isolation kudukkudhu. Container-kulla thani kernel illa. Adhanala dhaan Linux host-la Windows container run panna mudiyaadhu, and Mac/Windows-la Docker Desktop ulla oru chinna Linux VM run pannudhu. Part C-la idha hands-on-a paapom.

## 3 Core Concepts — Image, Container, Registry

**Image** = read-only template. App + dependencies + filesystem snapshot. Class maadhiri.
**Container** = image-oda running instance. Object maadhiri. Orey image-la irundhu 10 containers start pannalaam.
**Registry** = images store panra place. Docker Hub, GitHub Container Registry (ghcr.io), AWS ECR, Azure ACR.

```text
  Dockerfile ──docker build──► Image ──docker run──► Container (running process)
                                 │  ▲
                     docker push │  │ docker pull
                                 ▼  │
                              Registry (Docker Hub / ECR / GHCR)
```

Programming analogy:

| Docker | Programming |
|---|---|
| Dockerfile | Source code |
| `docker build` | Compile |
| Image | Compiled binary / Class |
| `docker run` | Execute / `new Object()` |
| Container | Running process / Object instance |
| Registry | npm / PyPI / NuGet repository |

## Docker Architecture

`docker` command type pannumbodhu enna nadakkudhu?

```text
 docker CLI ──REST API──► dockerd (Docker daemon) ──gRPC──► containerd ──► containerd-shim ──► runc
 (unga terminal)   via /var/run/docker.sock     (image pull,     (container        (OCI runtime:
                                                  network,        lifecycle)        namespaces +
                                                  volumes, build)                   cgroups setup
                                                                                    panni process start)
```

- **docker CLI** — client mattum. Adhu edhuvum run pannadhu, daemon-ku request anuppum.
- **dockerd** — main daemon. Build, network, volume management.
- **containerd** — container lifecycle manage pannum (CNCF project). **Kubernetes-um idha dhaan use pannudhu** (Docker illama).
- **runc** — actual-a Linux kernel-kitta pesi container process create pannum. OCI (Open Container Initiative) standard follow pannum.

!!! interview "Interview Point: Kubernetes Docker-a remove pannidichaa?"
    Kubernetes 1.24-la **dockershim** remove aachu — adhaavadhu kubelet Docker daemon-oda direct-a pesuradhu nirthiduchu. Ippo kubelet **CRI** (Container Runtime Interface) moolama containerd or CRI-O-oda pesum. Aana **Docker build panna images OCI standard** — adhanala adhe images Kubernetes-la perfect-a run aagum. Docker as a *build tool* still standard; as a *K8s runtime* thevai illa.

# Docker — First Commands

<span class="level beginner">Beginner</span>

## Mudhal container

```bash
$ docker run -d --name web -p 8080:80 nginx:1.27-alpine
Unable to find image 'nginx:1.27-alpine' locally
1.27-alpine: Pulling from library/nginx
...
Status: Downloaded newer image for nginx:1.27-alpine
a3f1c9e2b7d4...
```

Indha oru line-la enna nadandhuchu:

1. Local-la `nginx:1.27-alpine` image irukka nu check → illa
2. Docker Hub-la irundhu **pull** (layers download)
3. Image-la irundhu container **create**
4. `-p 8080:80` → host port 8080 → container port 80 **map**
5. `-d` → background (detached)-la **start**
6. Container ID print

Browser-la `http://localhost:8080` open pannunga — nginx welcome page ✅.

| Flag | Meaning |
|---|---|
| `-d` | Detached — background-la run |
| `--name web` | Container-ku peru (illana random name: `quirky_turing`) |
| `-p 8080:80` | `HOST:CONTAINER` port mapping |
| `-e KEY=value` | Environment variable |
| `-v vol:/path` | Volume mount |
| `--rm` | Container stop aana auto delete |
| `-it` | Interactive + TTY (shell-ku) |

## Daily use commands

```bash
docker ps                      # running containers
docker ps -a                   # stopped containers-um
docker logs web                # stdout/stderr logs
docker logs -f --tail 50 web   # follow (tail -f maadhiri)
docker exec -it web sh         # running container-kulla shell
docker stop web                # SIGTERM → 10s wait → SIGKILL
docker start web               # stopped container-a thirumba start
docker rm web                  # delete (stop aagirukkanum; -f force)
docker images                  # local images
docker rmi nginx:1.27-alpine   # image delete
docker inspect web             # full JSON details (IP, mounts, env...)
docker stats                   # live CPU/memory usage
docker system df               # disk usage
docker system prune            # unused containers/networks/images clean
```

## Container Lifecycle

```text
            docker create          docker start
  Image ─────────────────► Created ───────────► Running ◄──────┐
                                                 │   │         │ docker start /
                                     docker stop │   │ process │ restart policy
                                     (SIGTERM)   ▼   ▼ exits   │
                                                Exited ────────┘
                                                 │
                                       docker rm ▼
                                              (deleted)
```

!!! warning "Common Mistake: Container udane exit aagudhu"
    `docker run ubuntu` → container start aagi udane `Exited (0)`. Yen? **Container main process (PID 1) mudinja, container mudinjidum.** Ubuntu image default command `bash` — TTY illama bash udane exit aagum. Container oru VM illa, "on-la" irukka adhu oru long-running process venum (nginx, gunicorn, dotnet). Shell venum na: `docker run -it ubuntu bash`.

!!! lab "Try Pannunga"
    ```bash
    docker run -d --name web -p 8080:80 nginx:1.27-alpine
    docker exec -it web sh
    # container-kulla:
    ps aux                 # PID 1 = nginx master. Vera process-e illa!
    hostname               # container ID
    echo "<h1>Vanakkam</h1>" > /usr/share/nginx/html/index.html
    exit
    curl localhost:8080    # Vanakkam
    docker rm -f web && docker run -d --name web -p 8080:80 nginx:1.27-alpine
    curl localhost:8080    # Vanakkam poiduchu! Container filesystem ephemeral.
    ```
    Kadaisi step mukkiyam: container delete pannina adhula panna changes **poidum**. Data persist panna **volumes** venum (Part B).

# Dockerfile Deep Dive

<span class="level beginner">Beginner</span>

Dockerfile = image build panra **recipe**. Ovvoru instruction-um oru **layer** create pannum (most of them).

## Instructions — ovvonnaa

| Instruction | Enna pannum | Example |
|---|---|---|
| `FROM` | Base image. Ellam Dockerfile-um idhula start. | `FROM python:3.12-slim` |
| `WORKDIR` | Working directory set (illana create) | `WORKDIR /app` |
| `COPY` | Host files → image | `COPY requirements.txt .` |
| `ADD` | COPY + URL/tar extract. Normally COPY use pannunga. | |
| `RUN` | Build time-la command run → result layer-a save | `RUN pip install -r requirements.txt` |
| `ENV` | Environment variable (build + runtime) | `ENV PYTHONUNBUFFERED=1` |
| `ARG` | Build-time variable mattum | `ARG VERSION=1.0` |
| `EXPOSE` | Documentation — "indha port listen pannum". Port publish pannadhu! | `EXPOSE 8000` |
| `USER` | Idhukku apram vara commands + runtime endha user | `USER 10001` |
| `CMD` | Default command (override pannalaam) | `CMD ["gunicorn", "..."]` |
| `ENTRYPOINT` | Fixed executable; CMD/args adhuku arguments | `ENTRYPOINT ["dotnet", "TaskApi.dll"]` |
| `HEALTHCHECK` | Container health check command | |

## Namma Django Dockerfile — line by line

<!-- include: django-backend/Dockerfile -->

**`FROM python:3.12-slim`** — Official Python image, *slim* variant (Debian minimal). `python:3.12` full image **1.62GB**, slim **179MB** (real `docker images` output). Alpine innum chinnadhu, aana musl libc — sila Python wheels (psycopg binary maadhiri) work aagaadhu / compile panna vendi varum. Slim = safe default for Python.

**`ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`** — `.pyc` files ezhudha vendaam (container-la useless). Unbuffered = `print`/logs udane stdout-ku pogum — illana `docker logs`-la logs delay-a varum or crash aana poidum.

**`COPY requirements.txt .` then `RUN pip install`** — idhu dhaan **layer caching trick** (adutha section).

**`COPY . .`** — Full source code. `.dockerignore`-la irukka files (`.venv`, `__pycache__`, `db.sqlite3`) skip aagum.

**`RUN useradd --uid 10001 ...` + `USER 10001`** — Root-a run panna koodadhu. App-la security hole irundhaa attacker container-la root-a iruppaan. Fixed UID (10001) kudutha Kubernetes `runAsUser: 10001` match pannalaam.

**`EXPOSE 8000`** — Documentation mattum. Actual publish `-p` or Compose `ports:`-la.

**`CMD [...]`** — gunicorn (production WSGI server) start. `runserver` production-ku illa — single-threaded, debug purpose mattum.

## Layer Caching — build speed-oda secret

Ovvoru instruction-um oru layer. Docker build pannumbodhu, **instruction + input files maaralana, previous build-oda layer-a reuse** pannum. Oru layer maarina, **adhukku keela irukka ellam layers-um rebuild** aagum.

```text
 ❌ BAD ORDER                         ✅ GOOD ORDER (namma Dockerfile)
 FROM python:3.12-slim                FROM python:3.12-slim
 WORKDIR /app                         WORKDIR /app
 COPY . .            ← code maarina   COPY requirements.txt .   ← rarely changes
 RUN pip install ... ← ithuvum rerun  RUN pip install ...       ← CACHED ✅
   (every code change = 1-2 min)      COPY . .                  ← code change → idhu mattum
                                        (every code change = 2 sec)
```

Real output — `views.py` maathi rebuild pannumbodhu:

```text
#6 [2/6] WORKDIR /app
#6 CACHED
#7 [3/6] COPY requirements.txt .
#7 CACHED
#8 [4/6] RUN pip install --no-cache-dir -r requirements.txt
#8 CACHED
#9 [5/6] COPY . .          ← idhu mattum rerun
```

`docker history`-la layers & size paakalaam:

```text
$ docker history taskapp/django-backend:1.0 --format '{{.Size}}\t{{.CreatedBy}}'
0B      CMD ["gunicorn" "config.wsgi:application" "-…
0B      EXPOSE [8000/tcp]
0B      USER 10001
49.2kB  RUN /bin/sh -c useradd --uid 10001 --no-crea…
123kB   COPY . . # buildkit
69.5MB  RUN /bin/sh -c pip install --no-cache-dir -r…
12.3kB  COPY requirements.txt . # buildkit
8.19kB  WORKDIR /app
```

`pip install` layer 69.5MB — idhu cache aagaradhu dhaan periya win. Code (`COPY . .`) verum 123kB.

!!! tip "Rule of thumb"
    Dockerfile-la **rarely changing → top**, **frequently changing → bottom**. OS packages → language deps → source code.

## .dockerignore

`docker build .` pannumbodhu, current folder full-a (build context) daemon-ku anuppum. `.venv` (500MB), `.git`, `node_modules` ellam pogum — slow, and secrets leak aagalaam.

<!-- include: django-backend/.dockerignore -->

!!! danger "Secrets image-la poga koodadhu"
    `.env` file `.dockerignore`-la illana `COPY . .` adha image-la podum. Image push pannina, yaar pull pannaalum unga secrets paakalaam. `docker history` and layer extract panni deleted files-a kooda recover pannalaam — **later layer-la `RUN rm .env` pannaalum previous layer-la irukkum!**

## CMD vs ENTRYPOINT — confusing aana mukkiyam

| | CMD | ENTRYPOINT |
|---|---|---|
| Purpose | Default command | Fixed executable |
| `docker run image xyz` | `xyz` CMD-a **replace** pannum | `xyz` ENTRYPOINT-ku **argument**-a add aagum |
| Compose `command:` | CMD replace | ENTRYPOINT-ku args |
| K8s `command:` | — | ENTRYPOINT **replace** |
| K8s `args:` | CMD **replace** | — |

Namma project-la rendu style-um use pannirukkom — purposely:

- **Django:** `CMD ["gunicorn", ...]` mattum. Migrate Job-la `command: ["python", "manage.py", "migrate"]` — full-a replace.
- **.NET:** `ENTRYPOINT ["dotnet", "TaskApi.dll"]`. DB init-ku `args: ["--init-db"]` mattum kudukkurom → `dotnet TaskApi.dll --init-db`.

```bash
# Try pannunga:
docker run --rm taskapp/django-backend:1.0 python --version     # CMD replaced
# Python 3.12.15
docker run --rm --entrypoint sh taskapp/dotnet-backend:1.0 -c 'id'  # ENTRYPOINT override
# uid=1654(app) gid=1654(app) groups=1654(app)
```

## Exec form vs Shell form

```dockerfile
CMD ["gunicorn", "config.wsgi:application"]   # exec form  ✅  gunicorn = PID 1
CMD gunicorn config.wsgi:application          # shell form ❌  /bin/sh -c "..." = PID 1
```

Shell form-la `/bin/sh` PID 1 aagum. `docker stop` / Kubernetes pod delete pannumbodhu **SIGTERM** PID 1-ku pogum — `sh` adha gunicorn-ku forward pannadhu. Result: graceful shutdown illa, 10s (Docker) / 30s (K8s) wait aagi **SIGKILL** — in-flight requests drop aagum. **Eppovume exec form (JSON array) use pannunga.**

# Multi-stage Builds — .NET Example

<span class="level beginner">Beginner</span> → <span class="level intermediate">Intermediate</span>

Compiled languages (.NET, Go, Java, Rust)-ku build panna **SDK** (compiler, build tools) venum. Run panna **runtime** mattum podhum. SDK image final image-la irundha:

- Size periyadhu (`sdk:10.0` = **1.3GB**, `aspnet:10.0` = 340MB)
- Attack surface adhigam (compiler, source code, build tools ellam production-la)

**Multi-stage:** Oru Dockerfile-la multiple `FROM`. Mudhal stage-la build, last stage-la output mattum copy.

<!-- include: dotnet-backend/Dockerfile -->

```text
 Stage "build" (sdk:10.0, 1.3GB)             Stage "runtime" (aspnet:10.0)
 ┌────────────────────────────┐              ┌────────────────────────────┐
 │ .NET SDK, MSBuild, NuGet   │              │ ASP.NET Core runtime       │
 │ source code (*.cs)         │   COPY       │ /app/TaskApi.dll + deps    │
 │ obj/, bin/, NuGet cache    │ ──--from──►  │                            │
 │ /app/publish/ ◄── output   │   build      │ USER app (1654)            │
 └────────────────────────────┘              └────────────────────────────┘
        thrown away 🗑️                         final image: 350MB
```

**`COPY TaskApi.csproj .` + `RUN dotnet restore`** — Same caching trick. NuGet packages restore layer `.csproj` maarina mattum rerun.

**`dotnet publish --no-restore`** — Release build, already restore pannadhaala thirumba pannadhu.

**`COPY --from=build /app/publish .`** — Previous stage-la irundhu compiled output mattum.

**`USER $APP_UID`** — Microsoft .NET 8+ images-la `app` user built-in (UID 1654). Default port-um 8080 (non-root user 1024-ku keela port bind panna mudiyaadhu).

!!! tip "Innum chinnadha venum na"
    - `mcr.microsoft.com/dotnet/aspnet:10.0-alpine` — Alpine based, 177MB (340MB-la irundhu ~half)
    - `10.0-noble-chiseled` — Ubuntu chiseled: shell-e illa, package manager illa (distroless maadhiri), non-root default. 180MB, very secure.
    - Native AOT (`PublishAot`) — `runtime-deps` image + single native binary.

    Trade-off: shell illana `docker exec ... sh` panna mudiyaadhu — debugging-ku `kubectl debug` (Part F) use pannanum.

Python-ku multi-stage edhukku? C extensions compile panna `gcc`, `libpq-dev` venum na — builder stage-la wheels build panni, final slim stage-la wheels mattum install. Namma project-la `psycopg[binary]` pre-built wheel use panradhaala thevai padala.

# Namma Apps — Code Walkthrough

<span class="level beginner">Beginner</span>

Docker/K8s-ku "container-friendly" app eppadi ezhudhanum? **12-Factor App** principles — mukkiyamaa:

1. **Config from environment** — hardcode illa. Same image dev/staging/prod.
2. **Logs to stdout** — files-la illa. Platform collect pannum.
3. **Stateless processes** — state DB-la. Endha replica-vum endha request-um handle pannalaam.
4. **Disposability** — fast start, graceful shutdown.
5. **Port binding** — app thaane HTTP port-la listen pannum.

## Django — settings.py

<!-- include: django-backend/config/settings.py -->

Key points:

- **Ellam `os.environ`-la irundhu.** Compose-la `environment:`, K8s-la ConfigMap + Secret. Code-la oru password-um illa.
- **`ALLOWED_HOSTS = "*"` default** — K8s probes pod IP-a Host header-a anuppum. Specific domain mattum vecha probes `400 Bad Request (DisallowedHost)` vaangi pod **never Ready** aagum. Real-world-la neraya per maattikira trap idhu!
- **`DB_HOST` illana SQLite** — Docker illama `python manage.py runserver` quick test-ku.
- **`CONN_MAX_AGE=60` + `CONN_HEALTH_CHECKS`** — DB connection reuse; dead connection-a detect pannum (Postgres pod restart aana useful).
- **LOGGING → StreamHandler** — stdout.

## Django — views.py (health vs ready)

<!-- include: django-backend/tasks/views.py -->

**Rendu health endpoints yen?** Idhu Kubernetes probes-ku design pannadhu (Part E-la deep-a):

| Endpoint | Check | Fail aana K8s enna pannum |
|---|---|---|
| `/api/health` (liveness) | Process respond pannudha | Container **restart** |
| `/api/ready` (readiness) | DB connect + table irukka | Traffic **stop** (restart illa) |

DB down aana — liveness-la DB check panna, **ellam backend pods-um restart loop** — DB thirumba vandhaalum restart storm. Readiness-la mattum DB check → pods alive-a irukkum, traffic mattum nirkum, DB vandha udane automatic-a resume.

`hostname` field — container-la `socket.gethostname()` = container ID (Docker) / pod name (K8s). Load balancing paakka idhu dhaan use pannrom.

## .NET — Program.cs

<!-- include: dotnet-backend/Program.cs -->

- **`ConnectionStrings__Default` env var** → .NET configuration `ConnectionStrings:Default`. Double underscore = nested key separator (Linux env vars-la `:` allowed illa).
- **`--init-db` mode** — Same image, different mode. Schema create panni exit. Compose-la one-shot service, K8s-la Job. App startup-la `EnsureCreated` panna, 2 replicas orey nerathula table create panna try panni race condition varum.
- **Minimal API** — Controllers illama `app.MapGet(...)`. Chinna services-ku clean.
- Same `/api/health` vs `/api/ready` design.

!!! note "EnsureCreated vs Migrations"
    Learning project-ku `EnsureCreated()` simple. Real .NET project-la **EF Core Migrations** (`dotnet ef migrations add`, `migrationBundle`) use pannunga — schema changes version-controlled-a irukkum. Django-la `makemigrations`/`migrate` already andha pattern.

## Frontend — nginx template trick

<!-- include: frontend/nginx/default.conf.template -->

<!-- include: frontend/Dockerfile -->

**Problem:** Frontend Django backend-kum (`backend:8000`) .NET backend-kum (`backend:8080`) pesanum. Rendu image build pannanuma?

**Solution:** Official nginx image start aagumbodhu `/etc/nginx/templates/*.template` files-la `${VAR}`-a **envsubst** panni `/etc/nginx/conf.d/`-la podum. So **build once, configure at runtime** — `BACKEND_URL` env mattum maathunga.

**Same-origin proxy:** Browser `http://localhost:3000/api/tasks` call pannum — same origin. nginx adha backend-ku forward pannum. Browser-ku backend URL theriyave theriyaadhu → **CORS config thevai illa**, backend public-a expose panna vendiyadhilla.

!!! interview "Interview Point: Build once, deploy many"
    Oru image-a dev → staging → prod promote pannanum; environment-ku environment **rebuild panna koodadhu**. Rebuild pannina, test panna image-um production image-um vera — "tested artifact" guarantee poidum. Config env vars / ConfigMaps moolama inject pannunga. Indha frontend image idhukku perfect example — K8s-la orey image 2 Deployments-la vera vera config-oda run aagudhu.

!!! lab "Try Pannunga — images build"
    ```bash
    cd docker-k8s-fullstack
    docker build -t taskapp/django-backend:1.0 django-backend
    docker build -t taskapp/dotnet-backend:1.0 dotnet-backend
    docker build -t taskapp/frontend:1.0 frontend
    docker images | grep taskapp
    # taskapp/frontend         1.0   73.6MB
    # taskapp/dotnet-backend   1.0   350MB
    # taskapp/django-backend   1.0   261MB
    ```
    Ippo `views.py`-la oru space add panni thirumba build pannunga — `CACHED` lines paarunga.
