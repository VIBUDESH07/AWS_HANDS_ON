# PART F — Kubernetes Advanced {: .part }

Autoscaling real load-oda, scheduling control, security (RBAC, Pod Security, NetworkPolicy), Kustomize overlays & Helm, systematic debugging playbook, production path. Senior / DevOps interview level.

# Autoscaling — HPA, VPA, Cluster Autoscaler

<span class="level advanced">Advanced</span>

## 3 levels of scaling

| Autoscaler | Enna scale pannum | Trigger |
|---|---|---|
| **HPA** (Horizontal Pod Autoscaler) | Pod **count** | CPU/memory/custom metrics |
| **VPA** (Vertical Pod Autoscaler) | Pod **requests/limits** | Historical usage |
| **Cluster Autoscaler / Karpenter** | **Nodes** count | Pending pods (resources illa) |

Flow: Load ↑ → HPA pods add → nodes-la idam illa → pods `Pending` → Cluster Autoscaler/Karpenter new node add → pods schedule.

## Namma HPA

<!-- include: k8s/django/hpa.yaml -->

## HPA formula

```text
desiredReplicas = ceil( currentReplicas × currentMetricValue / targetMetricValue )

Example: 2 pods, average CPU 457% of request, target 70%
         ceil( 2 × 457 / 70 ) = ceil(13.06) = 13  → maxReplicas 5 cap → 5
```

**Utilization = request-oda percentage**, limit illa! Request 100m, usage 457m = 457%. Adhanala **requests set pannala na HPA work aagaadhu** (`<unknown>`).

## Real load test

```bash
# 3 busybox pods — infinite loop-la /api/tasks hit
kubectl -n taskapp create deployment load-gen --image=busybox:1.36 --replicas=3 -- \
  sh -c 'while true; do wget -q -O /dev/null http://django-backend:8000/api/tasks; done'

kubectl -n taskapp get hpa django-backend -w
```

```text
 time   TARGETS          REPLICAS
 30s    cpu: 68%/70%     2
 75s    cpu: 457%/70%    2          ← load spike detect
 90s    cpu: 457%/70%    5          ← scale up! (max 5)
 135s   cpu: 360%/70%    5
 # load-gen delete pannom
 +60s   cpu: 38%/70%     5          ← CPU kuranjudhu, aana udane scale down illa
 +4min  cpu: 2%/70%      3          ← stabilization window apram scale down start
 later  cpu: 2%/70%      2          ← minReplicas

$ kubectl -n taskapp describe hpa django-backend | grep "New size"
  Normal  SuccessfulRescale  5m23s  New size: 5; reason: cpu resource utilization (percentage of request) above target
  Normal  SuccessfulRescale  38s    New size: 3; reason: All metrics below target
```

**Scale up fast, scale down slow** — `behavior.scaleDown.stabilizationWindowSeconds: 120` = last 2 min-la highest recommendation-a use pannum. Traffic oscillate aana pods create/delete flapping avoid. (Default scale-down window 300s.)

!!! warning "HPA + replicas field conflict"
    HPA irukkura Deployment-la `replicas: 2` vecha, ovvoru `kubectl apply`-um replicas-a 2-ku reset pannum → HPA thirumba scale → flapping. Production-la HPA use pannum Deployment manifest-la `replicas` field-a **remove** pannunga (or Kustomize/Helm-la ignore). Namma learning setup-la visible-a vechirukkom.

## Custom metrics & KEDA

CPU ellaa apps-kum correct metric illa. Queue worker → queue length; API → requests/sec / latency.

- **Prometheus Adapter** — Prometheus metrics → HPA custom metrics
- **KEDA** — event-driven: Kafka lag, SQS/RabbitMQ queue length, cron, HTTP. **Scale to zero** support.

```yaml
metrics:
  - type: Pods
    pods:
      metric: { name: http_requests_per_second }
      target: { type: AverageValue, averageValue: "100" }
```

# Scheduling — Pods Enga Run Aaganum

<span class="level advanced">Advanced</span>

Scheduler 2 phases: **Filter** (fit aagaadha nodes remove — resources, taints, affinity) → **Score** (best node rank — spread, resource balance).

## nodeSelector & Node Affinity

```yaml
# Simple: label match
nodeSelector:
  disktype: ssd

# Expressive: required (hard) + preferred (soft)
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - { key: kubernetes.io/arch, operator: In, values: [amd64] }
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 50
        preference:
          matchExpressions:
            - { key: topology.kubernetes.io/zone, operator: In, values: [ap-south-1a] }
```

## Pod Anti-Affinity & Topology Spread — HA

2 django replicas **orey node-la** irundhaa, node crash = full outage. Spread pannunga:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname      # nodes across spread (zone-ku: topology.kubernetes.io/zone)
    whenUnsatisfiable: ScheduleAnyway        # DoNotSchedule = hard
    labelSelector:
      matchLabels: { app: django-backend }
```

## Taints & Tolerations

**Taint** node-la: "indha toleration illadha pods inga vara koodadhu". Dedicated nodes (GPU, DB), control-plane isolation.

```bash
kubectl taint nodes gpu-node-1 gpu=true:NoSchedule
```

```yaml
tolerations:
  - { key: gpu, operator: Equal, value: "true", effect: NoSchedule }
```

| Effect | Meaning |
|---|---|
| `NoSchedule` | New pods schedule aagaadhu |
| `PreferNoSchedule` | Soft — avoid pannum |
| `NoExecute` | Running pods-um evict (toleration illana) |

!!! interview "Interview Point: Taint vs Affinity"
    **Taint** = node pods-a *repel* pannum (node side). **Affinity** = pod node-a *attract* pannum (pod side). Toleration irundhaa taint node-la *allow* aagum — aana anga dhaan pogum nu guarantee illa. Dedicated GPU nodes-ku **rendum** venum: taint (matha pods vara koodadhu) + affinity/nodeSelector (GPU pods anga dhaan poganum).

## PodDisruptionBudget — voluntary disruptions

Node drain (upgrade, Karpenter consolidation) pannumbodhu ellam replicas-um orey nerathula evict aaga koodadhu:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: django-backend
  namespace: taskapp
spec:
  minAvailable: 1            # or maxUnavailable: 1
  selector:
    matchLabels: { app: django-backend }
```

`kubectl drain node-1` → PDB violate aagura eviction wait pannum. (Node crash maadhiri involuntary disruptions-ku PDB help pannaadhu — adhukku replicas + spread.)

## Priority & Preemption

`PriorityClass` — cluster full aana, high priority pods-ku low priority pods evict (preempt) aagum. Real output-la paathom: *"preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling"* — preempt pannaalum fit aagaadhu.

# Security — RBAC, Pod Security, NetworkPolicy

<span class="level advanced">Advanced</span>

Defense in depth — layers:

```text
 ┌ Cluster access ─── RBAC: yaar enna panna mudiyum (users, ServiceAccounts)
 ├ Admission ──────── Pod Security Standards, Kyverno/OPA policies
 ├ Pod/Container ──── securityContext: non-root, read-only FS, drop capabilities, seccomp
 ├ Network ────────── NetworkPolicy: yaar yaar-oda pesalaam
 ├ Secrets ────────── encryption at rest, external secret stores
 └ Supply chain ───── image scanning, signing (cosign), trusted registries
```

## securityContext — namma backends

```yaml
spec:
  securityContext:                    # POD level
    runAsNonRoot: true                # root UID-la start aana kubelet REJECT
    runAsUser: 10001
    seccompProfile:
      type: RuntimeDefault            # dangerous syscalls block
  containers:
    - securityContext:                # CONTAINER level
        allowPrivilegeEscalation: false   # setuid binaries vazhiya root aaga mudiyaadhu
        readOnlyRootFilesystem: true      # attacker malware ezhudha mudiyaadhu
        capabilities:
          drop: ["ALL"]                   # NET_RAW, CHOWN ... ellam remove
      volumeMounts:
        - { name: tmp, mountPath: /tmp }  # write venum na specific emptyDir mattum
```

`readOnlyRootFilesystem: true` vecha gunicorn crash aagum — worker heartbeat files `/tmp`-la ezhudhum. Adhanala `emptyDir` `/tmp`-ku. **Read-only FS enable pannumbodhu app enga ezhudhudhu nu kandupidichu andha paths-ku mattum emptyDir.**

## Pod Security Standards (PSA)

Namespace label vechu built-in admission controller enforce pannum:

| Level | Meaning |
|---|---|
| `privileged` | Restriction illa |
| `baseline` | Known privilege escalations block (hostNetwork, privileged...) |
| `restricted` | Best practices mandatory (non-root, drop ALL, seccomp...) |

```bash
# warn mode — reject pannaadhu, warning mattum
kubectl label ns taskapp pod-security.kubernetes.io/warn=restricted
kubectl -n taskapp rollout restart deploy/frontend-django
# Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false
#   (container "nginx" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities ...
kubectl -n taskapp rollout restart deploy/django-backend
# deployment.apps/django-backend restarted        ← warning illa ✅ compliant
kubectl label ns taskapp pod-security.kubernetes.io/warn-   # label remove
```

Namma backends `restricted` compliant ✅. **Postgres & nginx frontend compliant illa** (root-a start aagum) — exercise: `nginxinc/nginx-unprivileged` image (port 8080, non-root) use panni frontend-a fix pannunga.

## RBAC

```text
  Subject (yaar)              Role (enna permission)             Binding (connect)
  ┌───────────────┐          ┌─────────────────────────┐        ┌──────────────┐
  │ User / Group  │          │ Role (namespace scope)  │        │ RoleBinding  │
  │ ServiceAccount│◄─────────│ ClusterRole (cluster)   │◄───────│ ClusterRole- │
  └───────────────┘          │ verbs × resources        │        │ Binding      │
                             └─────────────────────────┘        └──────────────┘
```

Example — CI pipeline `taskapp`-la deploy mattum panna:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: deployer, namespace: taskapp }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: deployer, namespace: taskapp }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "patch", "update"]
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: deployer, namespace: taskapp }
subjects:
  - kind: ServiceAccount
    name: deployer
    namespace: taskapp
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl auth can-i patch deployments -n taskapp --as=system:serviceaccount:taskapp:deployer   # yes
kubectl auth can-i get secrets -n taskapp --as=system:serviceaccount:taskapp:deployer         # no ✅
```

!!! tip "ServiceAccount token auto-mount"
    Ovvoru pod-kum default ServiceAccount token `/var/run/secrets/kubernetes.io/serviceaccount/`-la mount aagum. App K8s API use pannala na: `automountServiceAccountToken: false` — attacker pod compromise pannaalum API token kidaikkaadhu.

## NetworkPolicy

Default: **ellam pods-um ellam pods-oda pesalaam** (flat network). Frontend compromise aana direct-a Postgres-ku connect pannalaam! NetworkPolicy = pod-level firewall.

<!-- include: k8s/extras/network-policy.yaml -->

- `podSelector` — indha policy endha pods-ku apply.
- `policyTypes: [Ingress]` — incoming traffic restrict. Policy select panna pod-ku, rules-la illadha ellam incoming **deny**.
- Policies **additive** (allow lists) — deny rule-nu thani illa.

!!! warning "CNI support venum"
    NetworkPolicy oru API object mattum — **CNI plugin enforce pannanum**. minikube default CNI (kindnet) enforce pannaadhu — apply aagum, aana effect illa! Test panna: `minikube start --cni=calico`. EKS-la VPC CNI network policy enable / Calico; AKS-la Azure NPM / Cilium; GKE Dataplane V2.

Common pattern — namespace default deny, apram explicit allow:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: taskapp }
spec:
  podSelector: {}           # ellam pods
  policyTypes: [Ingress]    # rules illa = ellam incoming deny
```

(Ingress controller namespace-la irundhu frontends-ku allow, DNS egress allow — marakkaadheenga.)

# Kustomize & Helm

<span class="level advanced">Advanced</span>

Same app dev, staging, prod-la — replicas, image tags, resources, domains vera. YAML copy-paste pannaa maintenance nightmare. 2 popular tools:

## Kustomize — overlays (patches)

Template language illa — plain YAML + patches. `kubectl`-la built-in (`-k`).

```text
k8s/                         ← base (namma current folder)
overlays/
├── dev/
│   └── kustomization.yaml
└── prod/
    ├── kustomization.yaml
    └── replicas-patch.yaml
```

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../k8s
images:                                  # image tag override — CI idha update pannum
  - name: taskapp/django-backend
    newName: ghcr.io/vibudesh/django-backend
    newTag: 1.4.2
patches:
  - path: replicas-patch.yaml
  - target: { kind: Ingress, name: taskapp }
    patch: |-
      - op: replace
        path: /spec/rules/0/host
        value: tasks.example.com
configMapGenerator:                      # content hash suffix → change aana auto rollout
  - name: django-config
    behavior: merge
    literals:
      - LOG_LEVEL=WARNING
```

```yaml
# overlays/prod/replicas-patch.yaml  (strategic merge patch)
apiVersion: apps/v1
kind: Deployment
metadata: { name: django-backend, namespace: taskapp }
spec:
  template:
    spec:
      containers:
        - name: django
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits: { memory: 512Mi }
```

```bash
kubectl kustomize overlays/prod     # final YAML preview (apply pannaama)
kubectl apply -k overlays/prod
```

## Helm — package manager

Go templates + `values.yaml`. Charts share pannalaam (Artifact Hub). Install/upgrade/rollback **releases**.

```text
taskapp-chart/
├── Chart.yaml           # name, version, appVersion
├── values.yaml          # defaults
├── values-prod.yaml     # env overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── _helpers.tpl
```

```yaml
# templates/deployment.yaml (snippet)
spec:
  replicas: {{ .Values.django.replicas }}
  template:
    spec:
      containers:
        - name: django
          image: "{{ .Values.django.image.repository }}:{{ .Values.django.image.tag }}"
          resources: {{- toYaml .Values.django.resources | nindent 12 }}
```

```bash
helm install taskapp ./taskapp-chart -n taskapp --create-namespace
helm upgrade taskapp ./taskapp-chart -f values-prod.yaml --set django.image.tag=1.4.2
helm history taskapp -n taskapp
helm rollback taskapp 3 -n taskapp
helm template ./taskapp-chart            # render mattum (debug)

# Third-party software install — Helm-oda real power
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm install cnpg cnpg/cloudnative-pg -n cnpg-system --create-namespace
```

| | Kustomize | Helm |
|---|---|---|
| Approach | Patch plain YAML | Templates + values |
| Learning curve | Low | Medium (Go templates) |
| Packaging/sharing | ❌ | ✅ Charts, repos, versions |
| Release history/rollback | ❌ (git dhaan) | ✅ `helm rollback` |
| Best for | Own apps, env variations | 3rd-party software, distributable apps |

Real teams often **rendum**: 3rd-party (Prometheus, cert-manager, ingress) Helm-la; own apps Kustomize-la; ellathaiyum **Argo CD** GitOps-la deploy.

# Debugging Playbook

<span class="level advanced">Advanced</span>

Idhu dhaan interview + real job-la most important skill. Indha errors ellam namma `debug-lab` namespace-la **real-a reproduce** pannadhu:

```text
$ kubectl -n debug-lab get pods
NAME             READY   STATUS                       RESTARTS      AGE
bad-image        0/1     ImagePullBackOff             0             76s
crash            0/1     Error                        3 (60s ago)   75s   ← CrashLoopBackOff cycle
missing-secret   0/1     CreateContainerConfigError   0             75s
oom              0/1     OOMKilled                    3 (50s ago)   75s
too-big          0/1     Pending                      0             75s
```

## Debug flow — eppovume indha order

```text
  kubectl get pods  ──►  STATUS enna?
        │
        ├─ Pending ─────────────────► kubectl describe pod → Events: FailedScheduling
        │                              (Insufficient cpu/memory, taints, affinity, PVC unbound)
        ├─ ImagePullBackOff/ErrImagePull ► describe → image name/tag typo? private registry
        │                              (imagePullSecrets)? local image cluster-la load pannala?
        ├─ CreateContainerConfigError ► describe → missing ConfigMap/Secret/key
        ├─ CrashLoopBackOff / Error ─► kubectl logs <pod> --previous  (crash aana container logs)
        │                              describe → Last State: exit code
        ├─ OOMKilled (137) ──────────► memory limit increase / memory leak
        ├─ Running but 0/1 Ready ────► describe → Readiness probe failed: reason
        └─ Running 1/1, app work aagala ► Service endpoints? DNS? port/targetPort? Ingress?
```

## 1. Pending

```text
$ kubectl -n debug-lab describe pod too-big
Events:
  Warning  FailedScheduling  default-scheduler  0/1 nodes are available: 1 Insufficient cpu.
           preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
```

Causes: requests romba adhigam (namma `cpu: 16`), node taint, affinity match illa, PVC `Pending` (StorageClass illa), cluster full. Fix: requests kurai, nodes add (Cluster Autoscaler), toleration/affinity fix.

## 2. ImagePullBackOff / ErrImagePull

```text
$ kubectl -n debug-lab describe pod bad-image
  Normal   Pulling  kubelet  Pulling image "taskapp/does-not-exist:9.9"
  Warning  Failed   kubelet  Failed to pull image "taskapp/does-not-exist:9.9": rpc error: ...
  Warning  Failed   kubelet  Error: ErrImagePull
  Normal   BackOff  kubelet  Back-off pulling image "taskapp/does-not-exist:9.9"
  Warning  Failed   kubelet  Error: ImagePullBackOff
```

`ErrImagePull` (attempt fail) → `ImagePullBackOff` (retry wait, exponential). Causes: tag typo, image push pannala, private registry auth (`imagePullSecrets`), **minikube-la `minikube image load` marandhuttom**, `:latest` + `IfNotPresent` confusion, architecture mismatch (arm64 vs amd64).

## 3. CrashLoopBackOff

```text
$ kubectl -n debug-lab logs crash
connecting to db...
FATAL: password authentication failed        ← root cause!

$ kubectl -n debug-lab describe pod crash
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
```

Container start → crash → kubelet restart → crash... Backoff: 10s, 20s, 40s, 80s, 160s, **max 300s**. STATUS `Error` ↔ `CrashLoopBackOff` maari maari varum.

`kubectl logs --previous` — **previous (crashed) container** logs. Current container innum start aagala na idhu dhaan useful.

| Exit code | Meaning |
|---|---|
| 0 | Success (aana `restartPolicy: Always` → restart! Main process "mudinjiduchu" — long-running process illa) |
| 1 | App error (logs paarunga) |
| 126 / 127 | Command not executable / not found (CMD typo, binary illa) |
| 137 | SIGKILL — OOMKilled, or liveness fail apram grace period mudinjadhu |
| 139 | Segfault |
| 143 | SIGTERM — graceful stop |

## 4. OOMKilled

```text
$ kubectl -n debug-lab describe pod oom
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
```

Container memory limit (64Mi) thaandi kernel kill pannudhu. Fix: limit increase (`kubectl top` paathu), memory leak fix, runtime tuning (JVM `-Xmx`, .NET `DOTNET_GCHeapHardLimit`, Node `--max-old-space-size` — container limit-ku match).

## 5. CreateContainerConfigError

```text
$ kubectl -n debug-lab describe pod missing-secret
  Warning  Failed  kubelet  Error: secret "nope-secret" not found
```

Referenced ConfigMap/Secret/key illa. Typo, wrong namespace (Secrets namespace-scoped!), or apply order. `optional: true` vecha missing-a irundhaalum start aagum.

## 6. Running but not Ready

```bash
kubectl describe pod <pod> | grep -A3 Readiness
# Readiness probe failed: HTTP probe failed with statuscode: 503
kubectl exec <pod> -- wget -qO- localhost:8000/api/ready
```

Namma DB-down demo idhu dhaan. Probe path/port wrong, dependency down, Django `ALLOWED_HOSTS` (400), app slow (timeout).

## 7. Service / networking issues

```bash
kubectl get endpointslices -l kubernetes.io/service-name=django-backend   # empty-a? → selector/readiness
kubectl get pods --show-labels                                            # labels match aagudha?
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh
  nslookup django-backend                       # DNS
  wget -qO- http://django-backend:8000/api/health   # Service
  wget -qO- http://10.244.0.20:8000/api/health      # Pod IP direct (Service bypass)
kubectl -n ingress-nginx logs deploy/ingress-nginx-controller             # Ingress 404/502/503
```

| Symptom | Likely cause |
|---|---|
| `Connection refused` via Service | targetPort wrong / app 127.0.0.1-la listen |
| Endpoints empty | Selector mismatch / pods not Ready |
| Ingress 404 | Host header match illa / ingressClassName wrong |
| Ingress 503 | Backend Service-ku ready endpoints illa |
| Ingress / nginx 502 | Upstream connection fail (pod terminating, crash) |
| DNS fail | CoreDNS pods, NetworkPolicy DNS egress block |

## Power tools

```bash
kubectl get events -n taskapp --sort-by=.lastTimestamp        # namespace events timeline
kubectl debug -it <pod> --image=busybox:1.36 --target=django  # ephemeral debug container
                                                              # (shell illadha distroless/chiseled images-ku!)
kubectl debug node/minikube -it --image=busybox:1.36          # node-la debug shell
kubectl get pod <pod> -o yaml | less                          # full status, conditions
kubectl top pods / kubectl top nodes                          # resource usage
stern -n taskapp django                                       # multi-pod log tail (tool)
k9s                                                           # terminal UI (tool) — highly recommended
```

!!! interview "Interview Point: Pod CrashLoopBackOff — eppadi debug pannuveenga?"
    Structured answer: (1) `kubectl describe pod` — Events + **Last State exit code** paapen. 137 na OOM/liveness, 1 na app error, 127 na command not found. (2) `kubectl logs --previous` — crash-ku munnaadi app enna sonnuchu. (3) Config check — env vars, Secrets mount aagudha, DB reachable-a (`kubectl exec`/debug pod-la irundhu test). (4) Liveness probe romba aggressive-a (startup slow app-ku startupProbe illa)? (5) Recent change enna — `kubectl rollout history`, image tag; venum na `rollout undo` panni mitigate, apram root cause. Mitigate first, then fix.

# Production Path — Laptop-la Irundhu Real World-ku

<span class="level advanced">Advanced</span>

## CI/CD pipeline

```text
 git push ──► CI (GitHub Actions / GitLab / CircleCI / Azure DevOps)
                │ 1. lint + unit tests (pytest / dotnet test)
                │ 2. docker build (BuildKit cache)
                │ 3. image scan (Trivy) — HIGH/CRITICAL fail
                │ 4. push: ghcr.io/org/django-backend:sha-3f9c2a1
                │ 5. sign (cosign) — optional
                ▼
           GitOps repo update: overlays/staging/kustomization.yaml → newTag: sha-3f9c2a1
                ▼
           Argo CD / Flux (cluster-kulla) — git watch → auto sync → cluster
                ▼
           staging ──(tests, approval)──► prod (same image digest!)
```

Sample GitHub Actions job:

```yaml
name: build
on: { push: { branches: [main] } }
jobs:
  django:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: "${{ github.actor }}", password: "${{ secrets.GITHUB_TOKEN }}" }
      - uses: docker/build-push-action@v6
        with:
          context: django-backend
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/django-backend:sha-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## GitOps

**Git = single source of truth.** Cluster-la `kubectl apply` manual-a yaarum pannaadhu. Argo CD git state-a cluster-oda continuously compare panni sync pannum (drift auto-fix). Rollback = `git revert`. Audit = git log. Namma `rollout undo` warning-ku idhu dhaan permanent solution.

## Managed Kubernetes

| | AWS EKS | Azure AKS | Google GKE |
|---|---|---|---|
| Control plane | Managed (paid/hour) | Managed (free tier) | Managed (Autopilot option) |
| Node autoscaling | Karpenter / Cluster Autoscaler | Cluster Autoscaler / NAP | Cluster Autoscaler / Autopilot |
| LoadBalancer | AWS NLB/ALB (LB Controller) | Azure LB / App Gateway | Google Cloud LB |
| Storage (RWO) | EBS CSI | Azure Disk CSI | PD CSI |
| Secrets | AWS Secrets Manager + ESO / CSI | Key Vault CSI | Secret Manager |
| Pod IAM | IRSA / EKS Pod Identity | Workload Identity | Workload Identity |

Namma manifests minimal changes-oda ellam-la run aagum: StorageClass name, Ingress class/annotations, image registry, managed DB (RDS) use panna Postgres StatefulSet remove panni `DB_HOST` maathunga.

## Observability — 3 pillars

| Pillar | Tools | Namma app-la |
|---|---|---|
| **Metrics** | Prometheus + Grafana, kube-state-metrics | `django-prometheus`, `prometheus-net` add pannalaam |
| **Logs** | Loki / ELK / OpenSearch + Fluent Bit | stdout logs already ✅ — collector pick pannum |
| **Traces** | OpenTelemetry + Jaeger / Tempo | OTel SDK (Python/.NET) — frontend→backend→DB trace |

Alerts: pod restarts, CrashLoop, HPA max-la, 5xx rate, p95 latency, PVC usage > 80%, node NotReady.

## Production checklist

- [ ] Images: pinned tags/digests, non-root, scanned, minimal base
- [ ] Requests/limits ellam containers-kum; LimitRange + ResourceQuota
- [ ] Liveness (no deps) / readiness (deps) / startup probes
- [ ] `preStop` sleep + graceful shutdown; PDB; topology spread across zones
- [ ] HPA (manifest-la replicas remove); Cluster Autoscaler/Karpenter
- [ ] Secrets external store-la (ESO/Sealed Secrets); encryption at rest; RBAC least privilege
- [ ] NetworkPolicies (default deny); Pod Security `restricted`
- [ ] Managed DB or operator; backups tested (restore panni paarunga!)
- [ ] Ingress TLS (cert-manager); WAF if public
- [ ] GitOps (Argo CD/Flux); separate namespaces/clusters per env
- [ ] Metrics, logs, traces, alerts; runbooks
