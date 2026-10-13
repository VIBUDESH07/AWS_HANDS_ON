# PART D — Kubernetes Basics {: .part }

Docker oru machine-la containers run pannum. Kubernetes **100 machines-la 1000 containers**-a manage pannum — crash aana restart, load adhigamaana scale, update pannumbodhu zero downtime. Architecture-la irundhu Pods, Deployments, Services, ConfigMaps varaikum — namma project manifests-oda.

# Kubernetes Yen Venum?

<span class="level beginner">Beginner</span>

Compose-la namma stack super-a run aagudhu. Production-la enna problems varum?

| Problem | Compose | Kubernetes |
|---|---|---|
| Server crash aana? | App down ❌ | Vera node-la pods reschedule ✅ |
| Container crash? | `restart:` policy | Restart + backoff + health-based ✅ |
| Traffic 10x aana? | Manual `--scale` | HPA auto-scale ✅ |
| New version deploy | Down → up (downtime) | Rolling update, readiness-gated ✅ |
| Bad version? | Manual | `kubectl rollout undo` ✅ |
| Multiple servers | ❌ (single host) | Cluster of nodes ✅ |
| Service discovery | Docker DNS (single host) | Cluster DNS + load-balanced Services ✅ |
| Secrets/config | env/files | ConfigMap, Secret objects ✅ |
| Desired state enforce | ❌ | Controllers continuously reconcile ✅ |

## Declarative vs Imperative — core mindset

**Imperative** (Docker): *"Indha container-a start pannu. Ippo innoru start pannu."* — Steps sollreenga.
**Declarative** (Kubernetes): *"Enakku 2 django pods eppovum running-a irukkanum."* — **Desired state** sollreenga. Eppadi achieve pannanum nu K8s paathukkum.

```text
   ┌──────────────── Reconciliation Loop (forever) ─────────────────┐
   │                                                                │
   │   Desired state (YAML: replicas: 2)                            │
   │            │                                                   │
   │            ▼                                                   │
   │   Observe actual state ──► Diff? ──► Act (create/delete pod) ──┘
   │   (running pods: 1)        (1 ≠ 2)    (1 pod create)
```

Pod-a neenga delete pannaalum, node crash aanaalum — controller "actual ≠ desired" nu paathu fix pannum. Idhu dhaan **self-healing**. Namma test-la paathom:

```text
$ kubectl -n taskapp delete pod django-backend-5fd5f6b867-nrb48
$ kubectl -n taskapp get pods -l app=django-backend
django-backend-5fd5f6b867-qv5hg   0/1   Running   0     4s     ← new pod auto create!
django-backend-5fd5f6b867-w8pt6   1/1   Running   0     66s
```

## Compose → Kubernetes mapping

| Compose | Kubernetes | Namma file |
|---|---|---|
| `services.backend` (stateless) | Deployment + Service | `k8s/django/deployment.yaml`, `service.yaml` |
| `services.db` | StatefulSet + headless Service + PVC | `k8s/postgres/` |
| `services.migrate` (one-shot) | Job | `k8s/django/migrate-job.yaml` |
| `environment:` | ConfigMap + Secret | `k8s/django/configmap.yaml`, `secret.yaml` |
| `volumes:` (named) | PersistentVolumeClaim | `volumeClaimTemplates` |
| `ports: "3000:80"` | Ingress (or NodePort/LoadBalancer) | `k8s/ingress.yaml` |
| `healthcheck:` | liveness/readiness/startup probes | deployments-la |
| `depends_on:` | ❌ illa! → readiness probes + initContainers + retries | |
| `--scale backend=3` | `replicas: 3` / HPA | `k8s/django/hpa.yaml` |
| default network DNS | Cluster DNS (CoreDNS) | `postgres`, `django-backend` names |

!!! warning "depends_on Kubernetes-la illa"
    K8s-la startup order guarantee illa — ellam parallel-a start aagum. Design: apps **retry** pannanum, **readiness probe** dependency ready-a illana traffic vaangaadhu, **initContainer** wait pannum. Namma Jobs-la `wait-for-postgres` initContainer idhukku dhaan.

# Kubernetes Architecture

<span class="level beginner">Beginner</span> → <span class="level intermediate">Intermediate</span>

```text
 ┌──────────────────────────── CONTROL PLANE ─────────────────────────────┐
 │                                                                        │
 │  ┌──────────────┐    ┌──────────┐   ┌────────────┐  ┌───────────────┐  │
 │  │kube-apiserver│◄──►│   etcd   │   │ scheduler  │  │  controller-  │  │
 │  │ (front door, │    │(key-value│   │(pod → node │  │   manager     │  │
 │  │  REST API,   │    │ store —  │   │ decide)    │  │(Deployment,RS,│  │
 │  │  auth, valid)│    │ ellam    │   └─────┬──────┘  │ Job, Node...  │  │
 │  └──────┬───────┘    │ state)   │         │ watch   │ controllers)  │  │
 │         ▲            └──────────┘         ▼         └───────┬───────┘  │
 │         └──────────────── ellam apiserver vazhiya ──────────┘          │
 └─────────┬──────────────────────────────────────────────────────────────┘
           │ (kubelet watch pannum)
 ┌─────────▼──────────── WORKER NODE ───────────┐  ┌──── WORKER NODE ────┐
 │  kubelet   ── CRI ──► containerd ──► runc    │  │  kubelet            │
 │  (node agent: pods run pannu, probes, status)│  │  kube-proxy         │
 │  kube-proxy (Service IPs → iptables/IPVS)    │  │  containerd         │
 │  ┌─────┐ ┌─────┐ ┌─────┐                     │  │  ┌─────┐ ┌─────┐    │
 │  │ pod │ │ pod │ │ pod │                     │  │  │ pod │ │ pod │    │
 │  └─────┘ └─────┘ └─────┘                     │  │  └─────┘ └─────┘    │
 └──────────────────────────────────────────────┘  └─────────────────────┘
```

## Components

| Component | Velai | Down aana? |
|---|---|---|
| **kube-apiserver** | Ellam requests-um idhu vazhiya. AuthN, AuthZ (RBAC), validation, admission. etcd-oda pesura **orey** component. | `kubectl` work aagaadhu; running pods continue aagum |
| **etcd** | Distributed key-value store — cluster-oda full state (ellam YAML objects) | Cluster brain gone — **backup mukkiyam** |
| **kube-scheduler** | Unscheduled pods-ku best node choose (resources, affinity, taints) | New pods `Pending`-la nirkum |
| **kube-controller-manager** | Controllers: Deployment, ReplicaSet, Job, Node, EndpointSlice... reconcile loops | Self-healing nirkum |
| **kubelet** | Ovvoru node-layum. Pods start, probes run, status report | Andha node pods-a manage panna mudiyaadhu |
| **kube-proxy** | Service virtual IPs → pod IPs (iptables/IPVS rules) | Service routing broken |
| **CoreDNS** | Cluster DNS (`django-backend.taskapp.svc.cluster.local`) | Name resolution fail |
| **CNI plugin** | Pod networking (Calico, Cilium, Flannel; minikube-la kindnet) | Pods pesa mudiyaadhu |

Real minikube-la ivanga ellam pods-a dhaan run aagudhu:

```text
$ kubectl -n kube-system get pods
coredns-559f6c778d-trjrc            Running
etcd-minikube                       Running
kindnet-cbmwh                       Running    ← CNI
kube-apiserver-minikube             Running
kube-controller-manager-minikube    Running
kube-proxy-sgxjd                    Running
kube-scheduler-minikube             Running
metrics-server-768f9f6999-sxs4w     Running    ← addon (HPA-ku)
storage-provisioner                 Running    ← PVC → hostPath volumes
```

## `kubectl apply -f deployment.yaml` — step by step enna nadakkudhu

```text
 1. kubectl ──HTTPS──► apiserver        : authenticate, authorize (RBAC), validate schema,
                                          admission controllers (defaults, policies)
 2. apiserver ──► etcd                  : Deployment object save
 3. Deployment controller (watch)       : "new Deployment!" → ReplicaSet create
 4. ReplicaSet controller (watch)       : "replicas 2, pods 0" → 2 Pod objects create (nodeName empty)
 5. scheduler (watch)                   : unscheduled pods → filter + score nodes → nodeName set
 6. kubelet on that node (watch)        : "en node-ku pod!" → CRI → containerd: image pull, container start
 7. kubelet                             : probes run → status (Running, Ready) apiserver-ku report
 8. EndpointSlice controller            : Ready pod IPs → Service endpoints-la add
 9. kube-proxy (watch)                  : iptables rules update → Service IP traffic pod-ku pogum
```

!!! interview "Interview Point: Components direct-a pesuvaangala?"
    **Illa.** Ellam components-um **apiserver-a mattum** watch/update pannum — hub-and-spoke. Scheduler kubelet-ku "pod run pannu" nu sollaadhu; scheduler Pod object-la `nodeName` set pannum, kubelet adha *watch* panni paathu run pannum. Idhu dhaan K8s-oda loosely-coupled, level-triggered design. Oru component restart aanaalum, current state-a apiserver-la irundhu padichu continue pannum.

# Local Cluster & kubectl

<span class="level beginner">Beginner</span>

## minikube start

```bash
make k8s-start
# = minikube start --driver=docker --cpus=2 --memory=4096
#   minikube addons enable ingress
#   minikube addons enable metrics-server
```

```text
$ kubectl get nodes -o wide
NAME       STATUS   ROLES           VERSION   INTERNAL-IP    OS-IMAGE                         CONTAINER-RUNTIME
minikube   Ready    control-plane   v1.37.0   192.168.49.2   Debian GNU/Linux 12 (bookworm)   containerd://2.3.4
```

minikube `--driver=docker` = oru Docker container-kulla full K8s node (control plane + worker). `docker ps`-la `minikube` container theriyum. Node-kulla runtime **containerd** — Docker illa! (Docker build panna images OCI standard, adhanala work aagum.)

| Local option | Note |
|---|---|
| **minikube** | Easy, addons (ingress, metrics-server, dashboard). Namma choice. |
| **kind** | K8s in Docker; multi-node easy; CI-la popular |
| **k3d / k3s** | Lightweight K8s |
| **Docker Desktop K8s** | One checkbox; Mac/Windows |

## kubeconfig & contexts

`~/.kube/config`-la clusters, users, contexts. `minikube start` automatic-a context add pannum.

```bash
kubectl config get-contexts
kubectl config use-context minikube
kubectl config set-context --current --namespace=taskapp   # default namespace set — `-n taskapp` venaam
```

!!! danger "Wrong cluster-la delete!"
    Real job-la laptop-la dev, staging, prod contexts irukkum. `kubectl delete` prod-la run aaidum. Eppovume `kubectl config current-context` check pannunga; prompt-la context kaattura tools (kube-ps1, starship) use pannunga.

## kubectl essentials

```bash
kubectl get pods                         # list
kubectl get pods -o wide                 # + node, IP
kubectl get pods -w                      # watch (live updates)
kubectl get all -n taskapp               # common resources
kubectl get deploy django-backend -o yaml   # full object (spec + status)
kubectl describe pod <name>              # details + EVENTS (debug-ku No.1)
kubectl logs <pod>                       # logs; -f follow; --previous crashed container
kubectl logs deploy/django-backend       # deployment-la oru pod-oda logs
kubectl exec -it <pod> -- sh             # pod-kulla shell
kubectl port-forward svc/frontend-django 8080:80   # local port → service
kubectl apply -f file.yaml               # create/update (declarative)
kubectl apply -k k8s/                    # kustomize directory
kubectl delete -f file.yaml
kubectl explain deployment.spec.strategy # field documentation — offline docs!
kubectl api-resources                    # ellam resource types + short names
```

Short names: `po` (pods), `deploy`, `svc`, `cm` (configmap), `ns`, `pvc`, `sts` (statefulset), `ing`, `hpa`.

## YAML anatomy — ellam objects-um idhe shape

```yaml
apiVersion: apps/v1          # API group/version  (kubectl api-resources-la paakalaam)
kind: Deployment             # object type
metadata:                    # identity
  name: django-backend
  namespace: taskapp
  labels:                    # selectors-ku use aagum (key/value)
    app: django-backend
  annotations: {}            # tools-ku metadata (select panna mudiyaadhu)
spec:                        # DESIRED state — neenga ezhudhuradhu
  ...
status:                      # ACTUAL state — K8s fill pannum (neenga ezhudha koodadhu)
  ...
```

# Pods

<span class="level beginner">Beginner</span>

**Pod** = Kubernetes-la smallest deployable unit. Oru or adhukku mela containers, **shared network (orey IP) + shared volumes**.

```text
 ┌─────────────── Pod (IP 10.244.0.20) ───────────────┐
 │  ┌────────────────┐        ┌────────────────────┐  │
 │  │ app container  │◄──────►│ sidecar (optional) │  │   localhost-la pesalaam
 │  │ :8000          │ shared │ log shipper/proxy  │  │
 │  └────────────────┘  vol   └────────────────────┘  │
 └────────────────────────────────────────────────────┘
```

## Simple pod

```yaml
# pod-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo
  labels:
    app: demo
spec:
  containers:
    - name: web
      image: nginx:1.27-alpine
      ports:
        - containerPort: 80
```

```bash
kubectl apply -f pod-demo.yaml
kubectl get pod demo -o wide
kubectl port-forward pod/demo 8080:80     # browser: localhost:8080
kubectl logs demo
kubectl delete pod demo                    # pod gone — FOREVER. Yaarum recreate pannala!
```

## Pod lifecycle

| Phase | Meaning |
|---|---|
| `Pending` | Accept aachu, aana schedule aagala / image pull aagudhu |
| `Running` | Node-la bind, at least oru container running |
| `Succeeded` | Ellam containers exit 0 (Jobs) |
| `Failed` | At least oru container non-zero exit, restart illa |
| `Unknown` | Node-oda contact illa |

`kubectl get pods` STATUS column-la vara `CrashLoopBackOff`, `ImagePullBackOff`, `ContainerCreating`, `OOMKilled` — idhellam phase illa, **container state reasons**. Part F debugging chapter-la ovvonnum.

## Multi-container patterns

- **Init containers** — main containers-ku munnaadi, order-la, complete aaganum. (Namma Jobs: `wait-for-postgres`)
- **Sidecar** — main app-oda kooda run: log shipping, service mesh proxy (Envoy), config reload. K8s 1.29+ native sidecars: `initContainers` with `restartPolicy: Always`.
- **Ambassador / Adapter** — proxy for outbound / format conversion.

!!! interview "Interview Point: Bare Pod yen production-la use panna koodadhu?"
    Bare Pod-a yaarum **manage pannala** — node crash aanaalo, delete aanaalo, evicted aanaalo, recreate aagaadhu. Scaling, rolling update illa. Adhanala eppovume **controllers** use pannunga: stateless → **Deployment**, stateful → **StatefulSet**, per-node agent → **DaemonSet**, run-to-completion → **Job/CronJob**. Pod = "cattle", individual-a care panna koodadhu.

# Deployments & ReplicaSets

<span class="level beginner">Beginner</span> → <span class="level intermediate">Intermediate</span>

```text
 Deployment (django-backend)          ← neenga manage pannradhu: image, replicas, strategy
     │ owns
     ├── ReplicaSet django-backend-5fd5f6b867  (current, replicas 2)   ← pod template hash
     │       ├── Pod django-backend-5fd5f6b867-9gzlq
     │       └── Pod django-backend-5fd5f6b867-b7fsk
     └── ReplicaSet django-backend-94664d8b    (old, replicas 0)       ← rollback-ku vechirukku
```

- **ReplicaSet** — "N pods eppovum irukkanum" mattum. Neenga direct-a create panna maateenga.
- **Deployment** — ReplicaSets-a manage panni **rolling updates + rollback** kudukkum. Pod template maarina (image, env...) new ReplicaSet create, old-a gradual-a scale down.

## Namma Django Deployment

<!-- include: k8s/django/deployment.yaml -->

Mukkiyamaana fields:

**`selector.matchLabels` ↔ `template.metadata.labels`** — Deployment endha pods tanakku sondham nu labels vechu dhaan kandupidikkum. Rendum match aaganum (illana apply error). Selector **immutable** — create aana apram maatha mudiyaadhu.

**`replicas: 2`** — HPA irundhaa adhu idha override pannum.

**`strategy.rollingUpdate`** — `maxSurge: 1, maxUnavailable: 0` = update-la 3 pods varaikum pogalaam (2+1), ready count 2-ku keela pogave koodadhu. New pod **Ready** aana apram dhaan old pod terminate. Default: 25% / 25%.

**`envFrom` + `env.valueFrom.secretKeyRef`** — ConfigMap-la ellam keys env-a; Postgres secret-la irundhu password mattum `DB_PASSWORD`-a rename panni. (Next chapters.)

**`resources`, probes, `securityContext`** — Part E & F-la deep-a.

## Real ReplicaSets output

```text
$ kubectl -n taskapp get rs
NAME                         DESIRED   CURRENT   READY   AGE
django-backend-5fd5f6b867    2         2         2       13m    ← active
django-backend-94664d8b      0         0         0       12m    ← old revision (rollback-ku)
dotnet-backend-6574bb5864    2         2         2       13m

$ kubectl -n taskapp get pods -l app=django-backend --show-labels
django-backend-5fd5f6b867-9gzlq   1/1   Running   app=django-backend,pod-template-hash=5fd5f6b867
```

Pod name = `<deployment>-<pod-template-hash>-<random>`. `pod-template-hash` label ReplicaSets-a overlap aagaama vechikkum.

## Scale, update, rollback

```bash
# Scale
kubectl -n taskapp scale deploy/django-backend --replicas=4

# Update (env change kooda new rollout trigger pannum — pod template maarudhu)
kubectl -n taskapp set env deploy/django-backend LOG_LEVEL=DEBUG
kubectl -n taskapp rollout status deploy/django-backend

# New image version
kubectl -n taskapp set image deploy/django-backend django=taskapp/django-backend:1.1

# History & rollback
kubectl -n taskapp rollout history deploy/django-backend
kubectl -n taskapp rollout undo deploy/django-backend                 # previous
kubectl -n taskapp rollout undo deploy/django-backend --to-revision=1

# Pause/resume (multiple changes orey rollout-la)
kubectl -n taskapp rollout pause deploy/django-backend
kubectl -n taskapp rollout resume deploy/django-backend

# Same spec, restart all pods (ConfigMap maathina apram)
kubectl -n taskapp rollout restart deploy/django-backend
```

Real rollout output (maxUnavailable: 0 — one by one):

```text
Waiting for deployment "django-backend" rollout to finish: 1 out of 2 new replicas have been updated...
Waiting for deployment "django-backend" rollout to finish: 1 old replicas are pending termination...
deployment "django-backend" successfully rolled out
```

!!! warning "rollout undo + kubectl apply = confusion"
    `rollout undo` pannumbodhu real output-la indha warning vandhuchu:
    *"resource deployments/django-backend was previously managed with 'kubectl apply'. Rolling back will not update the kubectl.kubernetes.io/last-applied-configuration annotation..."*
    Artham: cluster-la old version, aana unga YAML file-la new version. Adutha `kubectl apply` thirumba new version-a deploy pannidum! **Production-la rollback = git revert + apply** (GitOps). `rollout undo` emergency-ku mattum.

## Other strategies

| Strategy | Eppadi | Use |
|---|---|---|
| `RollingUpdate` (default) | Gradual replace | Most apps |
| `Recreate` | Ellam kill → new create (downtime) | 2 versions orey nerathula run aaga koodaadhu (DB schema incompatible) |
| Blue/Green | 2 Deployments, Service selector switch | Instant switch + rollback |
| Canary | Konjam % traffic new version-ku | Argo Rollouts, Flagger, service mesh |

# Services — Stable Networking

<span class="level beginner">Beginner</span> → <span class="level intermediate">Intermediate</span>

Pods ephemeral — recreate aana **new IP**. Frontend eppadi backend-a kandupidikkum? **Service** = stable virtual IP + DNS name + load balancing, label selector vechu pods-a track pannum.

```text
  frontend pod: http://django-backend:8000
                    │ CoreDNS: django-backend.taskapp.svc.cluster.local → 10.109.191.244 (ClusterIP)
                    ▼
          ┌──────────────────────┐
          │ Service django-backend│  selector: app=django-backend
          │ ClusterIP 10.109...  │  (virtual — kube-proxy iptables rules)
          └─────┬──────────┬─────┘
                ▼          ▼            EndpointSlice: READY pods mattum
        10.244.0.20:8000  10.244.0.21:8000
```

## Namma Service

<!-- include: k8s/django/service.yaml -->

## port vs targetPort vs containerPort

| Field | Enga | Meaning |
|---|---|---|
| `containerPort: 8000` (name: http) | Pod spec | App listen panra port (documentation + naming) |
| `targetPort: http` | Service | Traffic pod-la endha port-ku pogum (name or number) |
| `port: 8000` | Service | Clients call panra Service port |
| `nodePort: 30080` | Service (NodePort) | Ovvoru node-layum open aagura port (30000–32767) |

Named port (`http`) use pannaa — container port maarinaalum Service maatha vendaam.

## Real describe output

```text
$ kubectl -n taskapp describe svc django-backend
Selector:          app=django-backend
Type:              ClusterIP
IP:                10.109.191.244
Port:              http  8000/TCP
TargetPort:        http/TCP
Endpoints:         10.244.0.20:8000,10.244.0.21:8000     ← 2 ready pods
```

`Endpoints:` empty-a irundhaa → selector match aagala or pods Ready illa. **Service work aagala na first check idhu dhaan.**

## Service types

| Type | Reach | Use |
|---|---|---|
| **ClusterIP** (default) | Cluster-kulla mattum | Internal services (namma ellam) |
| **NodePort** | `<NodeIP>:30000-32767` | Simple external access, testing |
| **LoadBalancer** | Cloud LB (AWS NLB/ELB, Azure LB) public IP | Production external (cloud) |
| **ExternalName** | DNS CNAME | External DB-ku alias |
| **Headless** (`clusterIP: None`) | DNS → pod IPs direct | StatefulSets (namma postgres) |

## Cluster DNS — real test

```text
$ kubectl -n taskapp run dns-test --rm -i --restart=Never --image=busybox:1.36 -- \
    sh -c 'nslookup django-backend; nslookup postgres; wget -qO- http://django-backend:8000/api/health'

Name:    django-backend.taskapp.svc.cluster.local
Address: 10.109.191.244          ← ClusterIP (virtual)

Name:    postgres.taskapp.svc.cluster.local
Address: 10.244.0.17             ← headless → POD IP direct

{"status": "ok", "backend": "django", "hostname": "django-backend-5fd5f6b867-9gzlq"}
```

DNS format: `<service>.<namespace>.svc.cluster.local`. Same namespace-la `django-backend` mattum podhum; vera namespace-la `django-backend.taskapp`.

## Load balancing — real test

```text
$ for i in 1 2 3 4 5 6; do curl -s -H "Host: django.taskapp.local" http://$(minikube ip)/api/health | jq -r .hostname; done | sort | uniq -c
      4 django-backend-5fd5f6b867-nrb48
      2 django-backend-5fd5f6b867-w8pt6
```

Rendu pods-kum traffic pogudhu. kube-proxy iptables mode-la **random** selection per connection (round-robin illa) — adhanala 4/2 split.

!!! interview "Interview Point: ClusterIP-a ping panna reply varuma?"
    Varaadhu! ClusterIP oru **virtual IP** — endha network interface-layum illa. kube-proxy iptables/IPVS rules "indha IP:port-ku vara TCP/UDP packets-a indha pod IPs-ku DNAT pannu" nu mattum vechirukkum. ICMP (ping)-ku rule illa. Debug panna `curl service:port` use pannunga, ping illa.

!!! warning "Long-lived connections & load balancing"
    kube-proxy **connection** level-la balance pannum, request level illa. gRPC / HTTP/2 / DB connection pools — oru connection open panni adhulaye ellam requests anuppum → ellam traffic oru pod-ku. Solution: client-side LB, headless service + client balancing, or service mesh (Linkerd/Istio — L7 balancing).

# ConfigMaps & Secrets

<span class="level beginner">Beginner</span> → <span class="level intermediate">Intermediate</span>

Image-la config hardcode panna koodadhu (build once, deploy many). K8s-la:

- **ConfigMap** — non-sensitive config (DB host, log level, feature flags)
- **Secret** — sensitive (passwords, API keys, TLS certs)

## Namma ConfigMap & Secrets

<!-- include: k8s/django/configmap.yaml -->

<!-- include: k8s/postgres/secret.yaml -->

## Pod-ku inject panna 4 vazhigal

```yaml
# 1. Ellam keys env vars-a
envFrom:
  - configMapRef:
      name: django-config
  - secretRef:
      name: django-secret

# 2. Specific key, rename panni
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secret
        key: POSTGRES_PASSWORD

# 3. $(VAR) dependent env — munnaadi define panna var use panni
env:
  - name: POSTGRES_PASSWORD
    valueFrom: { secretKeyRef: { name: postgres-secret, key: POSTGRES_PASSWORD } }
  - name: ConnectionStrings__Default
    value: Host=postgres;...;Password=$(POSTGRES_PASSWORD)

# 4. Files-a mount (namma postgres init script)
volumes:
  - name: init-scripts
    configMap:
      name: postgres-init
# → /docker-entrypoint-initdb.d/01-create-dotnet-db.sql
```

Method 3 real result:

```text
$ kubectl -n taskapp exec deploy/dotnet-backend -- printenv ConnectionStrings__Default
Host=postgres;Port=5432;Database=dotnetdb;Username=tasks;Password=k8s-super-secret-password
```

Password orey place-la (postgres-secret) — Django, .NET, Postgres moonu-um adha reference pannudhu. Password rotate panna orey Secret update.

## Postgres init ConfigMap — file mount

<!-- include: k8s/postgres/init-configmap.yaml -->

ConfigMap `data` key = filename, value = file content. Volume-a mount panna directory-la files-a varum.

## Update behaviour — mukkiyam

| Inject method | ConfigMap update pannina |
|---|---|
| env / envFrom | ❌ Pod restart pannura varaikum **old value** |
| Volume mount | ✅ ~1 min-la file update (kubelet sync) — app re-read pannanum |
| Volume `subPath` mount | ❌ Update aagaadhu |

So env change-ku: `kubectl rollout restart deploy/django-backend`. Kustomize `configMapGenerator` name-la hash podum (`django-config-7h2k9`) — content maarina name maarum → Deployment auto rollout. Production pattern.

## Secrets ≠ secure (by default)

```text
$ kubectl -n taskapp get secret postgres-secret -o jsonpath='{.data.POSTGRES_PASSWORD}'
azhzLXN1cGVyLXNlY3JldC1wYXNzd29yZA==

$ ... | base64 -d
k8s-super-secret-password
```

!!! danger "base64 = encoding, encryption illa"
    Secret read permission irukka yaarum decode pannalaam. Default-a etcd-la-um plain (base64) dhaan. Real protection:

    1. **RBAC** — secrets `get/list` permission restrict.
    2. **Encryption at rest** — apiserver `EncryptionConfiguration` (EKS/AKS/GKE-la KMS integration).
    3. **Git-la plain secrets commit panna koodadhu** — namma `secret.yaml` learning-ku mattum. Use: **Sealed Secrets** (encrypted YAML git-la safe), **External Secrets Operator** (AWS Secrets Manager / Azure Key Vault / Vault-la irundhu sync), **SOPS**.
    4. Env vars vida **file mount** konjam safer (child processes, crash dumps, `/proc/*/environ`-la leak aagaadhu).

!!! lab "Try Pannunga"
    1. `kubectl -n taskapp edit configmap django-config` — `LOG_LEVEL: DEBUG` maathunga. `kubectl exec deploy/django-backend -- printenv LOG_LEVEL` — innum INFO! `rollout restart` panni thirumba check pannunga.
    2. Imperative-a create: `kubectl -n taskapp create configmap demo --from-literal=COLOR=blue --dry-run=client -o yaml` — YAML generate panna idhu shortcut.
    3. `kubectl -n taskapp get endpointslices -l kubernetes.io/service-name=django-backend` — replicas 4 aakki thirumba paarunga.
