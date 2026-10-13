# PART C — Docker Advanced {: .part }

Image size kuraikradhu, secure-a build panradhu, container ulla actual-a enna nadakkudhu (namespaces, cgroups, OverlayFS), PID 1 signals, registry & tagging strategy. Interview-la senior-level questions inga dhaan varum.

# Image Optimization & Security

<span class="level advanced">Advanced</span>

## Size yen matter aagudhu

- **Pull time** — K8s-la new node-la pod start aagumbodhu image pull. 1.5GB vs 150MB = autoscaling speed difference.
- **Storage & registry cost**
- **Attack surface** — image-la irukka ovvoru package-um oru potential CVE.

## Base image choices

| Base | Size (`docker images`, Docker 29) | Pros | Cons |
|---|---|---|---|
| `python:3.12` (full) | 1.62GB | Ellam tools irukku | Periyadhu, neraya CVEs |
| `python:3.12-slim` | 179MB | glibc, wheels work aagum | Build tools illa |
| `python:3.12-alpine` | 83.6MB | Romba chinnadhu | musl libc — wheels compile aagalaam, subtle bugs |
| `gcr.io/distroless/python3` | chinnadhu | Shell/package manager illa | Debug kashtam |
| `aspnet:10.0` | 340MB | Official, easy | |
| `aspnet:10.0-alpine` | 177MB | Half size | musl libc |
| `aspnet:10.0-noble-chiseled` | 180MB | No shell, non-root default | Debug-ku `kubectl debug` |
| `scratch` | 0 | Static binaries (Go, Rust) | Edhuvume illa |

## Optimization checklist

1. **Correct base** — slim / alpine / distroless / chiseled.
2. **Multi-stage** — build tools final image-la venaam.
3. **Layer order** — deps first, code last.
4. **RUN commands combine + cleanup same layer-la:**

    ```dockerfile
    # ❌ cleanup separate layer-la — size kuraiyaadhu (previous layer-la data irukku)
    RUN apt-get update
    RUN apt-get install -y libpq5
    RUN rm -rf /var/lib/apt/lists/*

    # ✅ orey layer
    RUN apt-get update \
     && apt-get install -y --no-install-recommends libpq5 \
     && rm -rf /var/lib/apt/lists/*
    ```

5. **`pip install --no-cache-dir`** — pip cache image-la venaam (namma Dockerfile-la irukku).
6. **`.dockerignore`** — context chinnadha.
7. **BuildKit cache mounts** — CI-la speed:

    ```dockerfile
    RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
    RUN --mount=type=cache,target=/root/.nuget/packages dotnet restore
    ```

## Security checklist

| Practice | Namma project-la |
|---|---|
| Non-root user | ✅ Django UID 10001, .NET UID 1654 |
| Specific version tags (`:latest` illa) | ✅ `python:3.12-slim`, `postgres:17-alpine`, `nginx:1.27-alpine` |
| Digest pin (`@sha256:...`) — ultimate reproducibility | ❌ (learning-ku tags podhum) |
| Secrets image-la illa | ✅ ellam env vars |
| Minimal base | ✅ slim / alpine |
| Read-only root filesystem | ✅ K8s `readOnlyRootFilesystem: true` (backends) |
| Drop Linux capabilities | ✅ K8s `capabilities.drop: [ALL]` |
| Vulnerability scan | Neenga try pannunga ⬇️ |

```bash
# Docker Scout (Docker built-in)
docker scout quickview taskapp/django-backend:1.0
docker scout cves taskapp/django-backend:1.0

# Trivy (open source, CI-la popular)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest \
  image --severity HIGH,CRITICAL taskapp/django-backend:1.0
```

!!! interview "Interview Point: Container-la root-a run panna enna problem?"
    Container root = host root (user namespaces enable pannala na — default-a illa). App-la RCE (remote code execution) bug irundhaa, attacker container-la root. Appo kernel exploit / misconfigured mount (`/var/run/docker.sock`, host path) / privileged flag irundhaa **container escape** panni host-a capture pannalaam. Non-root + capabilities drop + read-only FS + seccomp = defense in depth. Kubernetes `runAsNonRoot: true` vecha, root-a start aaga try panra container-a kubelet **reject** pannum.

# Docker Internals — Ulla Enna Nadakkudhu

<span class="level advanced">Advanced</span>

Container = **namespaces + cgroups + layered filesystem** use panra oru normal Linux process. Proof paapom — namma running Django container-la.

## Proof 1: Container oru host process dhaan

```text
$ docker inspect --format '{{.State.Pid}}' django-stack-backend-1
32285

$ ps -o pid,user,cmd -p 32285          # HOST-la run pannadhu
    PID USER     CMD
  32285 10001    /usr/local/bin/python3.12 /usr/local/bin/gunicorn config.wsgi:application
```

Host-la `ps` pannaa gunicorn theriyudhu — VM-la irundha theriyaadhu. User `10001` = namma Dockerfile `USER`.

## Proof 2: Namespaces — "enna paakalaam"

```text
$ for ns in pid net mnt uts; do ... done
pid  host=pid:[4026531836]  container=pid:[4026533108]
net  host=net:[4026531833]  container=net:[4026533110]
mnt  host=mnt:[4026531832]  container=mnt:[4026532796]
uts  host=uts:[4026531838]  container=uts:[4026533106]
```

Ovvoru namespace ID-um vera — container thani "view" la irukku.

| Namespace | Isolate pannradhu | Effect |
|---|---|---|
| **PID** | Process IDs | Container-la gunicorn = PID 1; host-la 32285 |
| **NET** | Network stack | Sontha IP, ports, `localhost` |
| **MNT** | Mount points | Sontha root filesystem (image) |
| **UTS** | Hostname | `hostname` = container ID / pod name |
| **IPC** | Shared memory | |
| **USER** | UID mapping | Container root → host non-root (rootless mode) |
| **CGROUP** | cgroup view | |

```text
$ docker exec django-stack-backend-1 python -c "import os; print(sorted(int(p) for p in os.listdir('/proc') if p.isdigit()))"
[1, 7, 8, 350]
```

Container-la 4 processes mattum theriyudhu: PID 1 (gunicorn master), 7 & 8 (2 workers — `--workers 2`), 350 (indha python command). Host-la 100s of processes irukku — PID namespace hide pannudhu.

!!! tip "Kubernetes Pod = shared namespaces"
    K8s Pod-la multiple containers irundhaa avanga **NET namespace share** pannuvanga — adhanala orey pod-la containers `localhost`-la pesalaam. Pod oru "pause" container namespace hold pannum, matha containers adha join pannum.

## Proof 3: cgroups — "evlo use pannalaam"

```text
$ docker info | grep -i cgroup
 Cgroup Driver: systemd
 Cgroup Version: 2

$ docker exec django-stack-backend-1 cat /sys/fs/cgroup/memory.max
max                                   ← limit illa (compose-la set pannala)

$ docker run --rm --memory=50m --memory-swap=50m python:3.12-slim \
    python -c "x = bytearray(200*1024*1024)"
$ echo $?
137                                   ← 128 + 9 (SIGKILL) = OOM killed
```

**Exit code 137** = memory limit thaandi kernel OOM killer SIGKILL pannudhu. Kubernetes-la idhu `OOMKilled` status-a theriyum. Indha number nyabagam vechikonga — debugging-la romba varum.

| cgroup controller | Docker flag | K8s field |
|---|---|---|
| memory | `--memory=256m` | `resources.limits.memory` |
| cpu | `--cpus=0.5` | `resources.limits.cpu: 500m` |
| cpu weight | `--cpu-shares` | `resources.requests.cpu` |
| pids | `--pids-limit=100` | (kubelet `podPidsLimit`) |

!!! interview "Interview Point: Memory limit vs CPU limit thaandina enna aagum?"
    **Memory** = incompressible resource → limit thaandina **kill** (OOMKilled, exit 137). **CPU** = compressible → limit thaandina **throttle** mattum (slow aagum, kill aagaadhu). Adhanala CPU limits romba tight-a vecha latency spikes varum; sila teams CPU limits-e vekkaama requests mattum vekkuraanga.

## OverlayFS — layers eppadi merge aagudhu

```text
 Container view (merged)      /app/manage.py  /usr/local/bin/python  /tmp/x
          ▲
          │ OverlayFS mount
 ┌────────┴─────────────────────────────────────────────┐
 │ upperdir  (container writable layer)  /tmp/x          │ ← write ellam inga
 ├───────────────────────────────────────────────────────┤
 │ lowerdir  layer N: COPY . .           /app/manage.py  │
 │ lowerdir  layer 2: pip install        site-packages/  │ read-only
 │ lowerdir  layer 1: python:3.12-slim   /usr/local/bin/ │
 └───────────────────────────────────────────────────────┘
```

- **Copy-on-write:** Lower layer file-a modify pannina, first adha upperdir-ku copy panni appuram modify.
- **Delete:** "whiteout" file create aagum — lower layer-la file innum irukku (adhanala dhaan `RUN rm secret` image size kuraikkaadhu, secret-um poagaadhu).
- 10 containers same image use pannaalum, lower layers disk-la **orey copy** dhaan.

## PID 1 & Signals — graceful shutdown

Container stop pannumbodhu:

```text
 docker stop / kubectl delete pod
        │
        ├──► SIGTERM → PID 1          (app: "new requests vaanga maaten, current mudichittu exit")
        │
        │    wait: Docker 10s / K8s terminationGracePeriodSeconds (default 30s)
        │
        └──► SIGKILL → PID 1          (force kill — in-flight requests drop)
```

Requirements for graceful shutdown:

1. **Exec form CMD/ENTRYPOINT** — app = PID 1, signal direct-a varum.
2. **App SIGTERM handle pannanum** — gunicorn, ASP.NET Core (Kestrel), nginx ellam built-in handle pannum.
3. **Shell script entrypoint venum na `exec` use pannunga:**

    ```bash
    #!/bin/sh
    python manage.py collectstatic --noinput
    exec gunicorn config.wsgi:application   # exec = shell process-a gunicorn replace pannum → PID 1
    ```

4. **Zombie reaping** — PID 1 child processes-a reap pannanum. App subprocess spawn pannina `docker run --init` (tini) use pannunga.

## Restart policies

| Policy | Behaviour |
|---|---|
| `no` (default) | Restart illa |
| `on-failure[:N]` | Non-zero exit-la mattum, max N times |
| `always` | Eppovum (daemon restart aanaalum) |
| `unless-stopped` | Always, manual stop pannina thavira |

Kubernetes-la idhu Pod `restartPolicy` (`Always` / `OnFailure` / `Never`) + exponential backoff (10s, 20s, 40s ... max 5 min) = **CrashLoopBackOff**.

# Registry, Tags & Multi-arch

<span class="level advanced">Advanced</span>

## Image name anatomy

```text
  ghcr.io / vibudesh / django-backend : 1.0.3 @sha256:a6e34c59...
  ───┬───   ───┬────   ──────┬──────   ──┬──   ───────┬────────
  registry  namespace     repository     tag      digest (immutable content hash)
  (default: docker.io)                  (default: latest)
```

`nginx:1.27-alpine` = actually `docker.io/library/nginx:1.27-alpine`.

## Tagging strategy

!!! danger ":latest anti-pattern"
    `:latest` = "kadaisiya push pannadhu" — version illa. Problems: (1) yaar enna version run panraanga nu theriyaadhu, (2) rollback panna previous `latest` enna nu theriyaadhu, (3) K8s-la `:latest` tag-ku default `imagePullPolicy: Always` — ovvoru pod start-um registry hit.

Good tags:

| Tag | Example | Use |
|---|---|---|
| Semantic version | `1.4.2` | Releases |
| Git SHA | `sha-3f9c2a1` | CI builds — exact commit trace |
| Both | `1.4.2` + `sha-3f9c2a1` | Best |
| Digest | `@sha256:...` | Production deploy (tag move aanaalum maaradhu) |

## Push to registry

```bash
# Docker Hub
docker login
docker tag taskapp/django-backend:1.0 <dockerhub-user>/django-backend:1.0
docker push <dockerhub-user>/django-backend:1.0

# GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u <github-user> --password-stdin
docker tag taskapp/django-backend:1.0 ghcr.io/<github-user>/django-backend:1.0
docker push ghcr.io/<github-user>/django-backend:1.0
```

Private registry-la irundhu Kubernetes pull panna `imagePullSecrets` venum:

```bash
kubectl -n taskapp create secret docker-registry ghcr-cred \
  --docker-server=ghcr.io --docker-username=<user> --docker-password=$GITHUB_TOKEN
```

```yaml
spec:
  imagePullSecrets:
    - name: ghcr-cred
```

## Multi-arch builds (Apple Silicon / AWS Graviton)

Mac M-series (ARM64)-la build panna image, x86 server-la `exec format error`-oda crash aagum. Solution — **buildx** multi-platform:

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/<user>/django-backend:1.0 --push django-backend
```

Registry-la oru **manifest list** — pull pannumbodhu machine architecture-ku match aagura image automatic-a varum.

!!! lab "Try Pannunga"
    1. `docker scout quickview` or Trivy-la namma 3 images scan pannunga. Endha base image-la adhiga CVEs?
    2. Django Dockerfile-a `python:3.12-alpine`-ku maathi build pannunga. Size enna? `psycopg[binary]` install aagudha?
    3. .NET Dockerfile runtime stage-a `mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled`-ku maathunga. Size compare pannunga. `docker exec -it ... sh` work aagudha? (Aagaadhu — shell illa!)
    4. `docker run --rm --memory=50m ...` OOM test-a neengale run panni exit code 137 paarunga.
