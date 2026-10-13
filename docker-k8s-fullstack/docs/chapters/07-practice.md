# PART G — Practice {: .part }

Padichadhu podhaadhu — kai-la pannanum. 15 hands-on labs (easy → hard), cheat sheets, and 35 interview questions with Tanglish answers.

# Hands-on Labs

Ovvoru lab-um namma project-la dhaan. Hint paakkaama mudhalla try pannunga.

## Beginner

!!! lab "Lab 1 — Django local, Docker illama"
    `django-backend`-la venv create panni `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver`. `curl localhost:8000/api/health`. **Question:** DB enga? (Hint: `settings.py` — `DB_HOST` illana SQLite.)

!!! lab "Lab 2 — Image inspect"
    `docker image inspect taskapp/django-backend:1.0` — `Config.User`, `Config.Cmd`, `Config.ExposedPorts`, `Config.Env` kandupidinga. `docker history` vechu largest layer edhu?

!!! lab "Lab 3 — Port mapping"
    Django backend-a mattum `docker run -d --name lab3 -p 9000:8000 taskapp/django-backend:1.0` run pannunga. `/api/health` → 200, aana `/api/tasks` → **500**. `docker logs lab3`-la `sqlite3.OperationalError: unable to open database file`. Yen? (Hint: `DB_HOST` illa → SQLite `/app/db.sqlite3`. `/app` root own pannudhu, container `USER 10001` — ezhudha permission illa. Non-root security-oda side effect!) Fix: `-e DB_HOST=...` kuduthu Postgres-oda connect pannunga, or writable volume mount pannunga. Indha lab-la "health 200 aana app broken" — adhanala dhaan readiness probe venum.

!!! lab "Lab 4 — Compose scale"
    `docker compose -f compose.django.yaml up -d --scale backend=3`. Browser-la refresh panni pod/container name maarudha paarunga. nginx DNS-la 3 IPs resolve aagum.

## Intermediate

!!! lab "Lab 5 — Hot reload dev setup"
    `compose.django.dev.yaml` create pannunga: backend-ku bind mount `./django-backend:/app` + `runserver`. `docker compose -f compose.django.yaml -f compose.django.dev.yaml up` (multiple files merge). `views.py` edit → auto reload.

!!! lab "Lab 6 — New API field"
    Task model-la `priority` (IntegerField, default 0) add pannunga — Django: `makemigrations`, .NET: model property. Frontend-la kaattunga. Image tag `1.1` build, `minikube image load`, `kubectl set image` panni rolling update. Django migrate Job eppadi rerun pannuveenga? (Hint: TTL / `kubectl delete job`.)

!!! lab "Lab 7 — Rollback drill"
    Deliberately broken image (`CMD ["python", "nonexistent.py"]`) tag `1.2` build & deploy. `maxUnavailable: 0` irukkradhaala old pods innum serve pannudha? `rollout status` enna sollum? `rollout undo` panni recover.

!!! lab "Lab 8 — ConfigMap change"
    `DEBUG: "1"` ConfigMap-la maathunga. Pods-la reflect aagudha? Kustomize `configMapGenerator`-ku migrate panni, change pannumbodhu auto rollout aagudha paarunga.

!!! lab "Lab 9 — CronJob backup"
    Part E CronJob example + backup PVC create pannunga. `kubectl create job --from=cronjob/postgres-backup now` manual trigger. Backup file irukka verify (`kubectl exec` / debug pod mount).

## Advanced

!!! lab "Lab 10 — NetworkPolicy with Calico"
    `minikube delete && minikube start --cni=calico`. Full stack deploy, `k8s/extras/network-policy.yaml` apply. busybox pod-la irundhu `nc -zv postgres 5432` — block aaganum. django pod-la irundhu work aaganum. Probes enna aachu?

!!! lab "Lab 11 — Non-root frontend"
    `nginxinc/nginx-unprivileged:1.27-alpine` base use panni frontend-a port 8080, non-root, `readOnlyRootFilesystem` (writable paths: `/tmp`, `/var/cache/nginx`, `/etc/nginx/conf.d`) aakkunga. Namespace `enforce=restricted` label podunga — enna enna pods reject aagudhu?

!!! lab "Lab 12 — Prod overlay"
    `overlays/dev` (replicas 1, DEBUG) & `overlays/prod` (replicas 3, bigger resources, PDB, topology spread) Kustomize-la. `kubectl kustomize overlays/prod | less` — diff paarunga.

!!! lab "Lab 13 — Helm chart"
    `helm create taskapp` panni Django Deployment/Service/HPA-va template pannunga. `values.yaml`-la image tag, replicas, resources. `helm upgrade --install` & `helm rollback`.

!!! lab "Lab 14 — Multi-node scheduling"
    `minikube start --nodes 3`. Django-ku topology spread / pod anti-affinity add pannunga — pods vera vera nodes-la poguthaa (`-o wide`)? `kubectl drain minikube-m02 --ignore-daemonsets` + PDB — enna nadakkudhu?

!!! lab "Lab 15 — Chaos day"
    Friend-kitta solli namma cluster-la 5 random breakages pannunga (wrong Secret key, Service selector typo, probe path change, memory limit 10Mi, image tag typo). Neenga debugging playbook vechu ellathaiyum 15 min-la fix pannunga.

# Cheat Sheet — Docker & Compose

## Docker

| Task | Command |
|---|---|
| Build | `docker build -t name:tag ./dir` |
| Build (no cache) | `docker build --no-cache -t name:tag .` |
| Run detached + port | `docker run -d --name x -p 8080:80 image` |
| Run + env + volume | `docker run -e K=V -v vol:/data image` |
| Run & auto-remove | `docker run --rm -it image sh` |
| Override entrypoint | `docker run --entrypoint sh image -c 'cmd'` |
| List | `docker ps` / `docker ps -a` |
| Logs | `docker logs -f --tail 100 x` |
| Shell | `docker exec -it x sh` |
| Inspect field | `docker inspect -f '{{.State.Pid}}' x` |
| Stats | `docker stats` |
| Stop / remove | `docker stop x` / `docker rm -f x` |
| Images | `docker images` / `docker rmi image` |
| Layers | `docker history image` |
| Tag & push | `docker tag a:1 reg/a:1 && docker push reg/a:1` |
| Networks | `docker network ls / create / inspect` |
| Volumes | `docker volume ls / inspect / rm` |
| Cleanup | `docker system df` / `docker system prune -a` |
| Multi-arch | `docker buildx build --platform linux/amd64,linux/arm64 --push -t ...` |

## Compose

| Task | Command |
|---|---|
| Up (build) | `docker compose -f f.yaml up -d --build` |
| Status | `docker compose ps -a` |
| Logs | `docker compose logs -f svc` |
| Exec | `docker compose exec svc sh` |
| One-off | `docker compose run --rm svc cmd` |
| Scale | `docker compose up -d --scale svc=3` |
| Final config | `docker compose config` |
| Down | `docker compose down` (`-v` volumes-um) |
| Restart one | `docker compose restart svc` |

# Cheat Sheet — kubectl

| Task | Command |
|---|---|
| Context | `kubectl config get-contexts` / `use-context x` |
| Default namespace | `kubectl config set-context --current --namespace=taskapp` |
| Get (wide/yaml) | `kubectl get pods -o wide` / `-o yaml` |
| Watch | `kubectl get pods -w` |
| Labels | `kubectl get pods --show-labels` / `-l app=x` |
| Describe | `kubectl describe pod x` |
| Events | `kubectl get events --sort-by=.lastTimestamp` |
| Logs | `kubectl logs x` / `-f` / `--previous` / `-c container` |
| Logs (deploy) | `kubectl logs deploy/x --all-containers` |
| Exec | `kubectl exec -it x -- sh` |
| Debug container | `kubectl debug -it x --image=busybox:1.36 --target=c` |
| Port forward | `kubectl port-forward svc/x 8080:80` |
| Apply / delete | `kubectl apply -f f.yaml` / `-k dir/` / `delete -f` |
| Dry run / diff | `kubectl apply --dry-run=server -f f.yaml` / `kubectl diff -k dir/` |
| Generate YAML | `kubectl create deploy x --image=y --dry-run=client -o yaml` |
| Scale | `kubectl scale deploy/x --replicas=3` |
| Set image | `kubectl set image deploy/x c=img:tag` |
| Rollout | `kubectl rollout status / history / undo / restart deploy/x` |
| Resource usage | `kubectl top pods` / `top nodes` |
| Docs | `kubectl explain pod.spec.containers.livenessProbe` |
| RBAC check | `kubectl auth can-i create pods --as=system:serviceaccount:ns:sa` |
| Temp pod | `kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh` |
| Node ops | `kubectl cordon / uncordon / drain node --ignore-daemonsets` |
| JSONPath | `kubectl get pods -o jsonpath='{.items[*].status.podIP}'` |

## minikube

| Task | Command |
|---|---|
| Start / stop / delete | `minikube start` / `stop` / `delete` |
| IP | `minikube ip` |
| Load image | `minikube image load img:tag` |
| Use minikube Docker | `eval $(minikube docker-env)` |
| Addons | `minikube addons list` / `enable ingress` |
| Dashboard | `minikube dashboard` |
| Tunnel (Mac/Win) | `minikube tunnel` |
| SSH into node | `minikube ssh` |

# Interview Q&A Bank

## Docker

!!! interview "1. Image vs Container?"
    Image = read-only layered template (filesystem + metadata: CMD, ENV, USER). Container = image-oda running instance + thin writable layer + isolated process (namespaces, cgroups). Orey image-la irundhu pala containers.

!!! interview "2. Container vs VM?"
    VM = full guest OS + own kernel, hypervisor isolation, GBs, minutes boot. Container = host kernel share panra isolated process, MBs, ms–seconds boot. Isolation weaker (shared kernel) — adhanala gVisor/Kata maadhiri sandboxed runtimes irukku.

!!! interview "3. CMD vs ENTRYPOINT?"
    ENTRYPOINT = fixed executable; CMD = default args (or default command if no ENTRYPOINT). `docker run img X` → CMD replace. K8s-la `command` → ENTRYPOINT override, `args` → CMD override. Namma .NET: `ENTRYPOINT dotnet TaskApi.dll` + `args: [--init-db]`.

!!! interview "4. Layer caching eppadi work aagudhu? Optimize eppadi?"
    Ovvoru instruction-um cache key (instruction + inputs/file checksums). Oru layer miss aana keela ellam rebuild. Rarely-changing steps (deps manifest copy + install) mela, source code copy kadaisiya. BuildKit cache mounts, `.dockerignore`.

!!! interview "5. Multi-stage build benefit?"
    Build tools (SDK, compilers) final image-la varaadhu → chinna size (namma .NET: SDK 1.3GB → final 350MB), chinna attack surface, secrets/source leak illa.

!!! interview "6. COPY vs ADD?"
    COPY = local files. ADD = + remote URLs + auto tar extract. Predictability-ku COPY prefer.

!!! interview "7. Container-la data persist eppadi?"
    Writable layer ephemeral. Named volumes (Docker managed), bind mounts (host path — dev), tmpfs (RAM). K8s-la PVC.

!!! interview "8. Containers eppadi oruthar oruthar-oda pesuvaanga?"
    Same user-defined network-la service/container name DNS (127.0.0.11 embedded DNS). Default bridge-la DNS illa. Container-la `localhost` = adhe container.

!!! interview "9. Exit code 137 enna?"
    128 + 9 = SIGKILL. Usually OOM killed (memory limit), or stop grace period mudinjadhu apram force kill.

!!! interview "10. PID 1 problem enna?"
    PID 1 signals forward pannanum + zombies reap pannanum. Shell-form CMD-la `sh` PID 1 → SIGTERM app-ku pogaadhu → graceful shutdown illa. Exec form, `exec` in scripts, `--init`/tini.

!!! interview "11. Image secure-a vechikka best practices?"
    Minimal base (slim/distroless/chiseled), non-root USER, pinned versions/digests, no secrets in layers (BuildKit secrets), scan (Trivy/Scout), sign (cosign), read-only root FS, drop capabilities, regular rebuild for patches.

!!! interview "12. ARG vs ENV?"
    ARG = build-time mattum (`--build-arg`), final container-la illa (aana history-la theriyum — secrets-ku venaam). ENV = build + runtime.

## Kubernetes

!!! interview "13. Kubernetes architecture explain pannunga."
    Control plane: apiserver (front door, ellam idhu vazhiya), etcd (state), scheduler (pod → node), controller-manager (reconcile loops). Nodes: kubelet (pods run, probes), kube-proxy (Service routing), container runtime (containerd via CRI), CNI. Components apiserver-a watch panni loosely coupled-a work pannum.

!!! interview "14. `kubectl apply` pannumbodhu enna nadakkudhu?"
    AuthN/AuthZ/admission/validation → etcd save → Deployment controller ReplicaSet create → RS controller Pods create → scheduler nodeName assign → kubelet containerd vazhiya containers start → probes → Ready → EndpointSlice update → kube-proxy rules.

!!! interview "15. Deployment vs StatefulSet vs DaemonSet?"
    Deployment = stateless, interchangeable pods, random names, rolling update. StatefulSet = stable identity (`postgres-0`), per-pod PVC, ordered ops, headless service DNS. DaemonSet = ovvoru node-layum oru pod (log agents, CNI, monitoring).

!!! interview "16. Service types?"
    ClusterIP (internal VIP), NodePort (node IP:30000-32767), LoadBalancer (cloud LB), ExternalName (DNS CNAME), Headless (`clusterIP: None` → pod IPs direct DNS).

!!! interview "17. Liveness vs Readiness vs Startup?"
    Liveness fail → restart. Readiness fail → endpoints-la irundhu remove (traffic stop, restart illa). Startup → slow-start apps-ku; pass aagura varaikum matha probes hold. Liveness-la external dependencies check panna koodadhu (cascading restarts) — namma DB-down demo.

!!! interview "18. Requests vs Limits? QoS?"
    Requests = scheduling guarantee; Limits = runtime cap (CPU throttle, memory OOMKill). QoS: Guaranteed (req=lim ellam), Burstable, BestEffort (nothing) — node pressure-la BestEffort first evict.

!!! interview "19. ConfigMap update aana pods-la reflect aaguma?"
    Env vars-a inject pannina **illa** — restart venum. Volume mount pannina ~1 min-la file update (subPath illana). Pattern: configMapGenerator hash suffix / checksum annotation → auto rollout.

!!! interview "20. Secrets secure-a?"
    Default base64 mattum. Protect: RBAC, etcd encryption at rest (KMS), external stores (ESO, Vault, cloud secret managers), Sealed Secrets/SOPS for git, file mounts over env.

!!! interview "21. Rolling update zero-downtime-a eppadi guarantee panradhu?"
    `maxUnavailable: 0` + `maxSurge: 1`, accurate readiness probes, `preStop` sleep (endpoint propagation gap — namma real 2×502 bug), app graceful SIGTERM handling, PDB, enough replicas.

!!! interview "22. Pod Pending-la irukku — reasons?"
    Insufficient CPU/memory (requests), taints without tolerations, node affinity/selector mismatch, PVC unbound, ResourceQuota exceeded, too many pods per node. `describe` → FailedScheduling event.

!!! interview "23. CrashLoopBackOff debug?"
    describe (exit code, events) → `logs --previous` → config/secrets/dependencies → probe settings → recent changes / rollback. Exit codes: 1 app, 127 command not found, 137 OOM/kill.

!!! interview "24. ImagePullBackOff?"
    Wrong name/tag, image not pushed, private registry auth (imagePullSecrets), rate limits (Docker Hub), arch mismatch, network. Local clusters-la image load pannala.

!!! interview "25. HPA eppadi work aagudhu?"
    metrics-server/custom metrics → `desired = ceil(current × currentMetric / target)`; utilization = % of **requests**. Scale-down stabilization (default 5 min). Requests illana HPA `<unknown>`. Queue-based scaling-ku KEDA.

!!! interview "26. Ingress vs LoadBalancer Service?"
    LoadBalancer = per-service L4 cloud LB (costly at scale). Ingress = L7 HTTP routing (host/path), TLS termination, orey entry point; Ingress controller venum. Gateway API = next-gen, richer routing & role separation.

!!! interview "27. Namespaces edhukku? Isolation tharuma?"
    Logical grouping, RBAC scope, ResourceQuota, naming scope. **Network isolation default-a illa** — NetworkPolicy venum. Strong isolation (multi-tenant hostile) venum na separate clusters / vClusters.

!!! interview "28. NetworkPolicy work aagala — yen?"
    CNI support illa (kindnet/flannel), selector labels wrong, policyTypes miss, DNS egress block pannitom. Policies allow-lists, additive.

!!! interview "29. Taints/tolerations vs node affinity?"
    Taint = node repels; toleration = pod allowed. Affinity = pod attracts to nodes. Dedicated nodes-ku rendum.

!!! interview "30. Init container vs sidecar?"
    Init = main-ku munnaadi sequential-a run to completion (wait-for-db, migrations, config). Sidecar = main-oda kooda lifetime full-a (proxy, log shipper); 1.29+ native sidecar = initContainer with `restartPolicy: Always`.

!!! interview "31. DB migrations K8s-la eppadi?"
    Separate Job (namma approach) / Helm pre-upgrade hook / Argo CD PreSync hook / initContainer (race risk with replicas — locking venum). Backward-compatible migrations (expand → migrate → contract) so old + new pods orey nerathula work aaganum during rolling update.

!!! interview "32. etcd backup yen mukkiyam?"
    Cluster-oda full state (ellam objects). Lost aana cluster rebuild. `etcdctl snapshot save`; managed K8s-la provider handle pannum. Plus GitOps repo = declarative rebuild source; PV data separately backup (Velero).

!!! interview "33. Kustomize vs Helm?"
    Kustomize = plain YAML + overlays/patches, kubectl built-in, own apps-ku. Helm = templating + packaging + release history/rollback, 3rd-party software-ku. Often together, GitOps-la.

!!! interview "34. GitOps enna? Benefits?"
    Git = desired state source of truth; Argo CD/Flux cluster-la irundhu pull & reconcile. Audit trail, easy rollback (git revert), drift detection, no direct kubectl access to prod.

!!! interview "35. Namma Task Board-a production-ku eppadi kondu poveenga?"
    Images CI-la build/scan/push (sha tags) → GitOps repo prod overlay → Argo CD. Managed Postgres (RDS/Azure DB) — StatefulSet remove. Secrets → ESO + cloud secret manager. Ingress/Gateway + cert-manager TLS + WAF. HPA + Karpenter, PDB, topology spread across AZs, preStop hooks. NetworkPolicies default deny, PSA restricted (frontend non-root fix). Prometheus/Grafana/Loki/OTel + alerts. Backups + restore drills. Separate dev/staging/prod.

# Mudivurai — Adutha Steps

Indha guide-la neenga:

- ✅ Container internals (namespaces, cgroups, OverlayFS, PID 1) purinjikitteenga
- ✅ Django & .NET apps-ku production-style Dockerfiles (layer caching, multi-stage, non-root) ezhudhuneenga
- ✅ Compose-la healthchecks, one-shot migrations, startup ordering-oda full stack run panneenga
- ✅ Kubernetes-la StatefulSet DB, Jobs, Deployments, Services, Ingress, HPA, probes, security contexts deploy panneenga
- ✅ Real bugs (502 during rollout, DisallowedHost, OOM, ImagePullBackOff) reproduce panni fix panneenga

## Adutha learning path

1. **Cloud K8s** — EKS / AKS / GKE-la indha project deploy (managed DB, real LoadBalancer, cert-manager).
2. **GitOps** — Argo CD install, indha repo-va sync pannunga.
3. **Observability** — kube-prometheus-stack Helm chart, Grafana dashboards, app metrics.
4. **Service mesh** — Linkerd (simple) / Istio: mTLS, retries, canary.
5. **Certifications** — CKAD (developer) → CKA (admin) → CKS (security). Indha guide-la irukka hands-on CKAD-ku nalla base.

!!! tip "Kadaisi advice"
    Theory 30%, practice 70%. Ovvoru week oru lab. Cluster-a break pannunga, fix pannunga — adhu dhaan real learning. **"Idhu illana enna aagum?"** nu kelvi kekkaradha nirutha koodadhu. All the best! 🚀
