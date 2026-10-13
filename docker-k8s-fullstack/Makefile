# Shortcut commands — `make <target>`. Ulla enna command run aagudhu nu paathu kathukonga.
IMAGES := django-backend dotnet-backend frontend
TAG := 1.0

.PHONY: build django-up django-down dotnet-up dotnet-down k8s-start k8s-load k8s-deploy k8s-status k8s-hosts k8s-delete pdf

build:
	docker build -t taskapp/django-backend:$(TAG) django-backend
	docker build -t taskapp/dotnet-backend:$(TAG) dotnet-backend
	docker build -t taskapp/frontend:$(TAG) frontend

# ---------- Docker Compose ----------
django-up:
	docker compose -f compose.django.yaml up -d --build
	@echo "Open http://localhost:3000"

django-down:
	docker compose -f compose.django.yaml down

dotnet-up:
	docker compose -f compose.dotnet.yaml up -d --build
	@echo "Open http://localhost:3001"

dotnet-down:
	docker compose -f compose.dotnet.yaml down

# ---------- Kubernetes (minikube) ----------
k8s-start:
	minikube start --driver=docker --cpus=2 --memory=4096
	minikube addons enable ingress
	minikube addons enable metrics-server

# Local images-a minikube node-kulla copy pannum (registry thevai illa)
k8s-load: build
	$(foreach image,$(IMAGES),minikube image load --overwrite=true taskapp/$(image):$(TAG);)

k8s-deploy:
	kubectl apply -k k8s/
	kubectl -n taskapp wait --for=condition=complete job/django-migrate job/dotnet-db-init --timeout=300s
	kubectl -n taskapp rollout status deploy/django-backend
	kubectl -n taskapp rollout status deploy/dotnet-backend

k8s-status:
	kubectl -n taskapp get all,pvc,ingress,hpa

k8s-hosts:
	@echo "Indha line-a /etc/hosts-la add pannunga:"
	@echo "$$(minikube ip) django.taskapp.local dotnet.taskapp.local"

k8s-delete:
	kubectl delete -k k8s/

pdf:
	python3 docs/build_pdf.py
